# app.py
from imports import *
from backend.routes.api_routes import api_bp, api_test
from backend.routes.socket_events import register_socket_events
import socket
from runtime_logging import install_global_exception_hooks, log_business, log_runtime_exception

def GetPath():
    # 动态获取当前.exe所在的目录，确保能正确加载资源文件
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe文件运行，'frozen' 属性会被设置
        app_dir = sys._MEIPASS
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))  # 获取当前脚本所在目录
    return app_dir

def create_app():
    productApp = Flask(__name__, static_folder='../frontend/my-app/out')
    productApp.register_blueprint(api_bp, url_prefix='/api')
    productApp.register_blueprint(api_test, url_prefix='/test')
    CORS(productApp, supports_credentials=True)
    return productApp


frontApp = create_app()
socketio = SocketIO(frontApp, cors_allowed_origins="*", async_mode="eventlet")

# 注册Socket.IO事件
register_socket_events(socketio)


@frontApp.route('/')
def index():
    return send_from_directory(frontApp.static_folder, 'index.html')


@frontApp.route('/<path:path>')
def static_proxy(path):
    return send_from_directory(frontApp.static_folder, path)

def _watch_flask_exit(event_dict):
    while True:
        if event_dict["flask_exit"].is_set():
            with frontApp.app_context():
                socketio.stop()
            break
        socketio.sleep(0.5)


def _is_port_available(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(('127.0.0.1', port))
            return True
        except OSError:
            return False


def _resolve_runtime_port(base_port, max_tries):
    for offset in range(max_tries):
        candidate_port = base_port + offset
        if _is_port_available(candidate_port):
            return candidate_port
    return None


def run_flask(event_dict):
    install_global_exception_hooks("backend")
    base_port = int(os.getenv("MAIN_PORT", "12233"))
    max_tries = int(os.getenv("PORT_FALLBACK_MAX_TRIES", "30"))

    try:
        resolved_port = _resolve_runtime_port(base_port, max_tries)
        if resolved_port is None:
            startup_error = (
                f"端口分配失败：从 {base_port} 开始连续尝试 {max_tries} 个端口均不可用。"
            )
            event_dict["startup_error"] = startup_error
            event_dict["resolved_port"] = -1
            log_business("error", "后端端口分配失败", "backend", detail=startup_error)
            print(f"[backMain] {startup_error}")
            return

        event_dict["resolved_port"] = resolved_port
        event_dict["startup_error"] = ""
        log_business("info", "后端端口分配成功", "backend", context={"port": resolved_port})
        if resolved_port != base_port:
            fallback_message = f"MAIN_PORT={base_port} 被占用，自动回退到端口 {resolved_port}"
            log_business("warn", "后端端口回退", "backend", detail=fallback_message)
            print(f"[backMain] {fallback_message}")

        socketio.start_background_task(_watch_flask_exit, event_dict)
        log_business("info", "后端服务开始监听", "backend", context={"port": resolved_port})
        socketio.run(frontApp, host='127.0.0.1', port=resolved_port, use_reloader=False)
    except Exception:
        log_runtime_exception("backend", message="后端进程运行时异常")
        raise


if __name__ == '__main__':
    install_global_exception_hooks("backend-main")
    manager = multiprocessing.Manager()
    event_main = manager.dict()
    event_main["flask_exit"] = manager.Event()
    event_main["resolved_port"] = -1
    event_main["startup_error"] = ""
    flask_process = multiprocessing.Process(target=run_flask, args=(event_main,))
    flask_process.start()
    print('\n backMain start')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("backMain exit")
        event_main["flask_exit"].set()
        flask_process.join()
