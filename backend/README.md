# AI农田情绪诊断师 - 后端

## 📁 项目结构

```
backend/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── config/              # 配置文件
│   │   ├── __init__.py
│   │   └── settings.py      # 应用配置
│   ├── database/            # 数据库
│   │   ├── __init__.py
│   │   ├── database.py      # 数据库连接
│   │   └── models.py        # 数据模型
│   ├── api/                 # API 路由
│   │   ├── __init__.py
│   │   ├── diagnosis.py     # 诊断相关 API
│   │   ├── chat.py          # 聊天相关 API
│   │   ├── history.py       # 历史记录 API
│   │   └── sensor.py        # 传感器数据和预测 API
│   ├── core/                # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── doctor.py        # 诊断引擎
│   │   ├── llm.py           # LLM 客户端
│   │   └── predictor.py     # 传感器数据预测
│   └── utils/               # 工具函数
│       ├── __init__.py
│       └── logger.py        # 日志配置
├── prompts/                 # 提示词文件
│   ├── system_prompt.txt
│   └── chat_prompt.txt
├── uploads/                 # 上传文件保存目录
├── .env                     # 环境变量
├── .env.example
├── requirements.txt
└── README.md
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，并修改相关配置：

```bash
cp .env.example .env
```

主要配置项：
- 数据库配置
- LLM 配置（Doubao API）
- 服务器端口

### 3. 启动后端服务器

```bash
python src/main.py
```

服务器将在 `http://localhost:8000` 启动

### 4. 访问 API 文档

打开浏览器访问：`http://localhost:8000/docs`


## 📚 API 端点说明

### 诊断相关 API (`/api/diagnosis`)
- `POST /upload`: 上传图片并进行诊断
- `GET /result/{id}`: 获取诊断结果

### 聊天相关 API (`/api/chat`)
- `POST /message`: 发送聊天消息
- `GET /history/{diagnosis_id}`: 获取聊天历史

### 历史记录 API (`/api/history`)
- `GET /diagnoses`: 获取诊断历史列表
- `GET /diagnoses/{id}`: 获取单条诊断详情

### 传感器数据和预测 API (`/api/sensor`)
- `POST /data`: 保存传感器数据
- `GET /data`: 获取传感器历史数据
- `GET /predict/temperature`: 预测温度趋势
- `GET /predict/humidity`: 预测湿度趋势
- `GET /predict/light`: 预测光照趋势


## 🗄️ 数据库

项目使用 MySQL 数据库，运行前需要：

1. 创建数据库
2. 在 `.env` 中配置数据库连接
3. 首次运行时，数据库表会自动创建
