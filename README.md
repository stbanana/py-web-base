# py-web-base

本项目是一个基于 Python 的本地前后端分离开发模板，适合作为快速搭建本地应用的起点。后端采用 Python，前端采用 Next.js（React）。

## 目录结构

```
py-web-base/
├── backend/         # Python 后端服务
│   ├── routes/      # API 路由与 Socket 事件
│   └── services/    # 业务逻辑服务
├── database/        # 数据库相关代码
├── frontend/        # 前端相关代码
│   ├── my-app/      # Next.js 前端项目
│   └── ...          # 其他前端模块
├── utils/           # 工具脚本
├── requirements.txt # Python 依赖
├── main.py          # 软件入口
└── ...
```

## 快速开始

### 1. 后端启动

```bash
pip install -r requirements.txt
python main.py
```

### 2. 前端启动

```bash
cd frontend/my-app
npm install
npm run dev
```

前端开发环境默认运行在 http://localhost:3000，产物为静态文件，最终由后端统一集成并作为桌面应用发布。实际运行时，只有一个后端端口（由环境变量 env 控制），无需单独启动前端服务。


