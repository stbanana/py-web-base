import time
import tkinter as tk
from tkinter import ttk
from urllib import request, error
import os
import threading
import sys
from runtime_logging import install_global_exception_hooks, log_business, log_runtime_exception


def _ping_backend(port, timeout=0.2):
	url = f"http://127.0.0.1:{port}/api/ping"
	try:
		with request.urlopen(url, timeout=timeout) as response:
			return response.status == 200
	except error.URLError:
		return False
	except Exception:
		return False


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


def wait_startup_ready(event_dict, port_publish_timeout_seconds=10, startup_timeout_seconds=30):
	install_global_exception_hooks("loading-page")
	root = tk.Tk()
	root.title("yoroATS - 启动中")
	icon_path = _resolve_icon_path()
	if icon_path:
		try:
			root.iconbitmap(icon_path)
		except Exception:
			pass
	window_width = 440
	window_height = 220
	root.geometry(f"{window_width}x{window_height}")
	root.resizable(False, False)
	root.update_idletasks()
	screen_width = root.winfo_screenwidth()
	screen_height = root.winfo_screenheight()
	x = int((screen_width - window_width) / 2)
	y = int((screen_height - window_height) / 2)
	root.geometry(f"{window_width}x{window_height}+{x}+{y}")

	title_var = tk.StringVar(value="系统正在加载")
	detail_var = tk.StringVar(value="正在启动后台服务，请稍候...")

	container = ttk.Frame(root, padding=20)
	container.pack(fill=tk.BOTH, expand=True)

	title_label = ttk.Label(container, textvariable=title_var, font=("Microsoft YaHei UI", 14, "bold"))
	title_label.pack(anchor=tk.CENTER, pady=(8, 8))

	progress = ttk.Progressbar(container, mode="indeterminate", length=340)
	progress.pack(anchor=tk.CENTER, pady=(8, 12))
	progress.start(10)

	detail_label = ttk.Label(container, textvariable=detail_var, font=("Microsoft YaHei UI", 10))
	detail_label.pack(anchor=tk.CENTER)

	button_frame = ttk.Frame(container)
	button_frame.pack(anchor=tk.CENTER, pady=(14, 0))

	state = {
		"done": False,
		"ready": False,
		"error": "",
		"start_ts": time.time(),
		"next_probe_ts": time.time() + 2.0,
		"probe_interval_seconds": 0.2,
		"probe_inflight": False,
		"error_shown": False,
		"resolved_port": None,
		"port_resolve_ts": None,
	}

	def run_probe_once():
		ok = _ping_backend(state["resolved_port"])
		if ok:
			state["ready"] = True
		state["probe_inflight"] = False

	def close_window():
		state["done"] = True
		root.destroy()

	def on_close():
		if not state["ready"] and not state["error"]:
			state["error"] = "用户取消了启动。"
			log_business("warn", "用户在启动页主动关闭窗口", "loading-page")
		close_window()

	root.protocol("WM_DELETE_WINDOW", on_close)

	def show_error(message):
		if state["error_shown"]:
			return
		state["error_shown"] = True
		state["error"] = message
		log_business("error", "启动页展示错误", "loading-page", detail=message)
		progress.stop()
		title_var.set("启动失败")
		detail_var.set(message)
		close_button = ttk.Button(button_frame, text="关闭", command=close_window)
		close_button.pack()

	def check_state():
		if state["done"]:
			return

		now = time.time()
		elapsed_seconds = now - state["start_ts"]

		startup_error = event_dict.get("startup_error", "")
		if startup_error:
			show_error(startup_error)
			return

		if elapsed_seconds < 2.0:
			remain = 2.0 - elapsed_seconds
			detail_var.set(f"正在初始化界面，请稍候...（{remain:.1f}s）")
		else:
			if state["resolved_port"] is None:
				resolved_port = event_dict.get("resolved_port", -1)
				if isinstance(resolved_port, int) and resolved_port > 0:
					state["resolved_port"] = resolved_port
					state["port_resolve_ts"] = now
					detail_var.set(f"端口 {resolved_port} 已就绪，正在连接服务...")
				else:
					detail_var.set("正在分配可用端口，请稍候...")
					if elapsed_seconds >= port_publish_timeout_seconds:
						show_error(f"后端在 {port_publish_timeout_seconds} 秒内未发布可用端口。")
						return
			else:
				port_ready_elapsed = now - state["port_resolve_ts"]
				detail_var.set(f"正在启动后台服务，请稍候...（端口 {state['resolved_port']}）")
				if (not state["probe_inflight"]) and (now >= state["next_probe_ts"]):
					state["probe_inflight"] = True
					state["next_probe_ts"] = now + state["probe_interval_seconds"]
					threading.Thread(target=run_probe_once, daemon=True).start()

				if port_ready_elapsed >= startup_timeout_seconds:
					show_error(
						f"后端在 {startup_timeout_seconds} 秒内未就绪，请检查端口 {state['resolved_port']} 或服务日志。"
					)
					return

		if state["ready"]:
			state["done"] = True
			log_business("info", "启动页检查通过", "loading-page", context={"port": state["resolved_port"]})
			title_var.set("系统加载完成")
			detail_var.set("正在打开主界面...")
			root.after(250, root.destroy)
			return

		root.after(50, check_state)

	root.after(200, check_state)
	try:
		root.mainloop()
	except Exception:
		log_runtime_exception("loading-page", message="启动页运行时异常")
		raise
	return state["ready"], state["error"], state["resolved_port"]


def wait_backend_ready(port, timeout_seconds=30):
	debug_event_dict = {
		"resolved_port": port,
		"startup_error": "",
	}
	ready, startup_error, _ = wait_startup_ready(
		debug_event_dict,
		port_publish_timeout_seconds=2,
		startup_timeout_seconds=timeout_seconds,
	)
	return ready, startup_error


if __name__ == '__main__':
	install_global_exception_hooks("loading-page-main")
	test_port = int(os.getenv("MAIN_PORT", "12233"))
	test_timeout = int(os.getenv("STARTUP_TIMEOUT_SECONDS", "30"))
	test_event_dict = {
		"resolved_port": test_port,
		"startup_error": "",
	}
	ready, startup_error, resolved_port = wait_startup_ready(
		test_event_dict,
		port_publish_timeout_seconds=2,
		startup_timeout_seconds=test_timeout,
	)
	print(f"[loadingPage] ready={ready}, error={startup_error}, port={resolved_port}")
