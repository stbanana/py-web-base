from imports import *
import sqlite3
from runtime_logging import install_global_exception_hooks, log_business, log_runtime_exception


def _get_db_path():
    if getattr(sys, 'frozen', False):
        # 打包后，使用当前工作目录
        base_dir = os.path.join(os.getcwd(), "~")
    else:
        # 开发环境，使用源代码目录
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "ats.db")


def _init_schema(conn: sqlite3.Connection):
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS test_items (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            version TEXT,
            content TEXT,
            created_ts INTEGER
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            testitem_id TEXT,
            operator TEXT,
            machine_id TEXT,
            start_ts INTEGER,
            end_ts INTEGER,
            status TEXT,
            report_path TEXT
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS artifacts (
            id TEXT PRIMARY KEY,
            run_id TEXT,
            kind TEXT,
            file_path TEXT,
            created_ts INTEGER
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS audit (
            id TEXT PRIMARY KEY,
            action TEXT,
            actor TEXT,
            detail TEXT,
            created_ts INTEGER
        );
        """
    )


def run_database(event_dict):
    install_global_exception_hooks("database")
    db_path = _get_db_path()
    try:
        conn = sqlite3.connect(db_path, timeout=30)
        _init_schema(conn)
        log_business("info", "数据库初始化完成", "database", context={"db_path": db_path})
        while True:
            if event_dict["database_exit"].is_set():
                log_business("info", "数据库进程收到退出信号", "database")
                break
            time.sleep(1)
    except Exception:
        log_runtime_exception("database", message="数据库进程运行时异常")
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass

if __name__ == '__main__':
    install_global_exception_hooks("database-main")
    manager = multiprocessing.Manager()
    event_main = manager.dict()
    event_main["database_exit"] = manager.Event()

    database_process = multiprocessing.Process(target=run_database, args=(event_main,))
    database_process.start()
    print('\n dataMain start')

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('dataMain exit')
        event_main["database_exit"].set()
        database_process.join()
