# weather-cli

基于 [聚合数据](https://www.juhe.cn/) 天气 API 的终端天气查询工具。输入城市名称，即可获取当前温度、天气状况等信息。

## 环境要求

- Python >= 3.13
- [uv](https://docs.astral.sh/uv/)（推荐的 Python 包管理器）

## 安装

```bash
# 1. 克隆仓库
git clone <your-repo-url>
cd weather-cli

# 2. 使用 uv 安装依赖
uv sync
```

## 配置 API Key

在项目根目录创建 `.env` 文件，填入你的聚合数据 API Key：

```
apiKey=你的聚合数据API密钥
```

> 前往 [聚合数据 - 天气查询 API](https://www.juhe.cn/docs/api/id/73) 申请免费 API Key。

## 使用方法

```bash
# 查询北京的天气
uv run python main.py 北京

# 查询上海的天气
uv run python main.py 上海
```

运行后终端会输出类似：

```
城市: 北京，今日温度：26℃，天气: 晴
```

查询结果会同时保存到项目目录下的 `weather.json` 文件中，运行日志记录在 `weather.log`。

## 依赖

| 依赖           | 用途                     |
| -------------- | ------------------------ |
| `requests`     | 发送 HTTP 请求调用天气 API |
| `python-dotenv` | 从 `.env` 文件加载 API Key |
| `pydantic`     | 数据校验与序列化          |
| `ruff`         | 代码格式化与静态检查       |

## 开发

```bash
# 代码格式化
uv run ruff format .

# 代码检查
uv run ruff check .
```

## 项目结构

```
weather-cli/
├── main.py          # 主程序入口
├── pyproject.toml   # 项目配置与依赖声明
├── .env             # API 密钥（需自行创建）
└── README.md
```

## License

MIT
