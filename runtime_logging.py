import datetime
import json
import os
import sys
import threading
import traceback


_WRITE_LOCK = threading.Lock()


def _get_log_dir():
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    log_dir = os.path.join(base_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def _build_entry(level, source, message, detail=None, context=None, kind='business'):
    return {
        'ts': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'level': level,
        'kind': kind,
        'source': source,
        'message': message,
        'detail': detail or '',
        'context': context or {},
        'pid': os.getpid(),
        'thread': threading.current_thread().name,
    }


def _append_log(file_name, entry):
    log_dir = _get_log_dir()
    file_path = os.path.join(log_dir, file_name)
    line = json.dumps(entry, ensure_ascii=False)
    with _WRITE_LOCK:
        with open(file_path, 'a', encoding='utf-8') as file_handle:
            file_handle.write(line + '\n')


def read_log_entries(channel='error', limit=100):
    channel_to_file = {
        'state': 'state.log',
        'error': 'error.log',
        'runtime': 'runtime_crash.log',
    }
    file_name = channel_to_file.get(channel, 'error.log')
    file_path = os.path.join(_get_log_dir(), file_name)
    if not os.path.exists(file_path):
        return []

    entries = []
    with _WRITE_LOCK:
        with open(file_path, 'r', encoding='utf-8') as file_handle:
            for line in file_handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    entries.append({'ts': '', 'level': 'error', 'kind': 'parse', 'message': line})

    return entries[-max(1, int(limit)):]


def log_business(level, message, source, detail=None, context=None):
    try:
        level = str(level).lower()
        entry = _build_entry(level=level, source=source, message=message, detail=detail, context=context, kind='business')
        _append_log('state.log', entry)
        if level in ('error', 'fatal'):
            _append_log('error.log', entry)
    except Exception:
        pass


def log_runtime_exception(source, exc_info=None, message='未捕获运行时异常', context=None):
    try:
        if exc_info is None:
            exc_info = traceback.format_exc()

        detail = exc_info
        entry = _build_entry(
            level='fatal',
            source=source,
            message=message,
            detail=detail,
            context=context,
            kind='runtime',
        )
        _append_log('runtime_crash.log', entry)
        _append_log('error.log', entry)
    except Exception:
        pass


def install_global_exception_hooks(source):
    try:
        def _sys_hook(exc_type, exc_value, exc_tb):
            detail = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
            log_runtime_exception(source=source, exc_info=detail, message='sys.excepthook 捕获到未处理异常')

        sys.excepthook = _sys_hook

        if hasattr(threading, 'excepthook'):
            def _thread_hook(args):
                detail = ''.join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))
                log_runtime_exception(
                    source=source,
                    exc_info=detail,
                    message='threading.excepthook 捕获到线程未处理异常',
                    context={'thread_name': getattr(args.thread, 'name', 'unknown')},
                )

            threading.excepthook = _thread_hook
    except Exception:
        pass
