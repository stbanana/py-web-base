from imports import *
from frontend.loadingPage import wait_startup_ready
from runtime_logging import install_global_exception_hooks, log_business, log_runtime_exception

chinese = {
    'global.quitConfirmation': u'确定关闭?',
}


def _resolve_icon_path():
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    candidate = os.path.join(base_dir, 'frontend', 'my-app', 'out', 'favicon.ico')
    if os.path.exists(candidate):
        return candidate

    fallback = os.path.join(base_dir, 'my-app', 'out', 'favicon.ico')
    if os.path.exists(fallback):
        return fallback

    return None


def run_webview(event_dict):
    install_global_exception_hooks("frontend")
    icon_path = _resolve_icon_path()
    startup_timeout_seconds = int(os.getenv("STARTUP_TIMEOUT_SECONDS", "30"))
    port_wait_timeout_seconds = int(os.getenv("PORT_PUBLISH_TIMEOUT_SECONDS", "10"))

    try:
        ready, startup_error, port = wait_startup_ready(
            event_dict,
            port_publish_timeout_seconds=port_wait_timeout_seconds,
            startup_timeout_seconds=startup_timeout_seconds,
        )
        if not ready:
            log_business("error", "启动页检查失败", "frontend", detail=startup_error)
            print(f"[frontMain] startup failed: {startup_error}")
            raise SystemExit(1)

        log_business("info", "前端窗口即将启动", "frontend", context={"port": port})

        webview.settings = {
            'ALLOW_DOWNLOADS': True, # 允许下载文件
            'ALLOW_FILE_URLS': True, # 允许访问本地文件
            'OPEN_EXTERNAL_LINKS_IN_BROWSER': True,
            'OPEN_DEVTOOLS_IN_DEBUG': True,
            'REMOTE_DEBUGGING_PORT': None, # 禁止远程调试端口，提升安全性
        }
        webview.create_window('yoroATS',
                              f'http://127.0.0.1:{port}',
                              text_select=True,  # 可复制文字
                              zoomable=True,  # 可调整大小
                              confirm_close=True,  # 关闭时提示
                              min_size =(160, 160), # 最小窗口大小
                              shadow = True,  # 窗口阴影
                              background_color='#333333'
                              )

        webview.start(gui="edgechromium", ssl=True, icon=icon_path, storage_path=os.path.join(os.path.dirname(__file__), "webview_storage"), localization=chinese)
        log_business("info", "前端窗口已退出", "frontend")
    except SystemExit:
        raise
    except Exception:
        log_runtime_exception("frontend", message="前端进程运行时异常")
        raise


if __name__ == '__main__':
    install_global_exception_hooks("frontend-main")
    debug_event_dict = {
        "resolved_port": int(os.getenv("MAIN_PORT", "12233")),
        "startup_error": "",
    }
    run_webview(debug_event_dict)
