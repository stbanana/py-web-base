import time

from imports import *
from backend.backMain import run_flask
from frontend.frontMain import run_webview
from database.dataMain import *
from runtime_logging import install_global_exception_hooks, log_business, log_runtime_exception


if __name__ == '__main__':
    multiprocessing.freeze_support()
    install_global_exception_hooks("main")
    log_business("info", "主进程启动", "main")

    manager = multiprocessing.Manager()
    event_main = manager.dict()
    event_main["flask_exit"] = manager.Event()
    event_main["database_exit"] = manager.Event()
    event_main["resolved_port"] = -1
    event_main["startup_error"] = ""

    redis_process = multiprocessing.Process(target=run_database, args =(event_main,))
    redis_process.start()
    log_business("info", "数据库进程已启动", "main", context={"pid": redis_process.pid})

    flask_process = multiprocessing.Process(target=run_flask, args=(event_main,))
    flask_process.start()
    log_business("info", "后端进程已启动", "main", context={"pid": flask_process.pid})

    webview_process = multiprocessing.Process(target=run_webview, args=(event_main,))
    webview_process.start()
    log_business("info", "前端进程已启动", "main", context={"pid": webview_process.pid})

    shutdown_reason = "webview_exit"
    try:
        while True:
            if not webview_process.is_alive():
                if webview_process.exitcode and webview_process.exitcode != 0:
                    shutdown_reason = f"webview_crash_exitcode_{webview_process.exitcode}"
                    log_business("error", "前端进程异常退出", "main", context={"exitcode": webview_process.exitcode})
                else:
                    shutdown_reason = "webview_exit"
                    log_business("info", "前端进程正常退出", "main")
                break

            if not flask_process.is_alive():
                shutdown_reason = f"flask_crash_exitcode_{flask_process.exitcode}"
                log_business("error", "后端进程异常退出", "main", context={"exitcode": flask_process.exitcode})
                break

            if not redis_process.is_alive():
                shutdown_reason = f"database_crash_exitcode_{redis_process.exitcode}"
                log_business("error", "数据库进程异常退出", "main", context={"exitcode": redis_process.exitcode})
                break

            time.sleep(0.5)
    except KeyboardInterrupt:
        shutdown_reason = "keyboard_interrupt"
        log_business("warn", "接收到键盘中断，开始关停", "main")
    except Exception:
        shutdown_reason = "main_unhandled_exception"
        log_runtime_exception("main", message="主进程循环出现未处理异常")
    finally:
        print(f"[main] shutdown start, reason={shutdown_reason}")
        log_business("info", "主进程开始关停", "main", context={"reason": shutdown_reason})
        event_main["database_exit"].set()
        event_main["flask_exit"].set()

        if webview_process.is_alive() and shutdown_reason != "webview_exit":
            webview_process.terminate()

        webview_process.join(timeout=10)
        if webview_process.is_alive():
            print("[main] webview graceful shutdown timeout, force terminate")
            log_business("warn", "前端进程优雅退出超时，执行强制回收", "main")
            webview_process.terminate()
            webview_process.join(timeout=10)

        flask_process.join(timeout=10)
        if flask_process.is_alive():
            print("[main] flask graceful shutdown timeout, force terminate")
            log_business("warn", "后端进程优雅退出超时，执行强制回收", "main")
            flask_process.terminate()
            flask_process.join(timeout=10)

        redis_process.join(timeout=10)
        if redis_process.is_alive():
            print("[main] database graceful shutdown timeout, force terminate")
            log_business("warn", "数据库进程优雅退出超时，执行强制回收", "main")
            redis_process.terminate()
            redis_process.join(timeout=10)

        print("[main] shutdown finished")
        log_business(
            "info",
            "主进程关停完成",
            "main",
            context={
                "webview_exitcode": webview_process.exitcode,
                "flask_exitcode": flask_process.exitcode,
                "database_exitcode": redis_process.exitcode,
            },
        )
