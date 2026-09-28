# 天气查询 API

基于 FastAPI 和聚合数据（Juhe）天气 API 的天气查询服务，支持热门城市、单城市和批量天气查询。服务提供 Swagger 文档、Bearer Token 鉴权、请求追踪 ID 和日志记录。

## 功能

- 查询预设热门城市的天气
- 查询单个城市的天气
- 批量查询多个城市；单个城市失败时，其余查询继续执行
- 通过 `X-Trace-ID` 响应头和日志追踪请求
- 使用 Bearer Token 保护单城市查询接口
- 提供统一的未处理异常响应

## 环境要求

- Python 3.13 或更高版本（与 `pyproject.toml` 中的项目要求一致）
- [uv](https://docs.astral.sh/uv/) 包管理器
- 聚合数据天气查询 API Key

> Ubuntu 22.04 自带的 Python 版本可能低于本项目声明的最低版本。部署前请确认 `python3 --version` 满足要求，或使用 uv 安装兼容的 Python 版本。

## 配置

在项目根目录创建 `.env` 文件：

```dotenv
apiKey=替换为你的聚合数据API密钥
API_TOKEN=替换为你自己生成的访问令牌
```

- `apiKey`：向聚合数据天气接口发起请求所需的 API Key。
- `API_TOKEN`：访问 `GET /weather/{city}` 所需的 Bearer Token。

可前往[聚合数据天气查询 API](https://www.juhe.cn/docs/api/id/73)申请 API Key。请勿将真实密钥或令牌提交到 Git 仓库；`.env` 已加入 `.gitignore`。

## 本地安装与运行

在项目根目录执行：

```bash
uv sync
uv run uvicorn APITRY:app --reload --host 127.0.0.1 --port 8000
```

打开 Swagger 文档：

```text
http://127.0.0.1:8000/docs
```

代码入口是 `APITRY.py` 中的 `app` 对象，因此 Uvicorn 模块路径为 `APITRY:app`。

## API 接口

| 方法 | 路径 | 鉴权 | 说明 |
| --- | --- | --- | --- |
| `GET` | `/weather/hot` | 不需要 | 查询预设热门城市 |
| `GET` | `/weather/{city}` | 需要 | 查询单个城市 |
| `POST` | `/weather/batch` | 不需要 | 批量查询城市 |
| `GET` | `/docs` | 不需要 | Swagger 交互式 API 文档 |
| `GET` | `/error` | 不需要 | 异常处理测试接口 |

当前实现中只有单城市查询接口要求令牌；热门城市和批量查询接口无需令牌。`/error` 仅用于验证异常处理，不应作为正常业务接口使用。

### 查询热门城市

```bash
curl -i http://127.0.0.1:8000/weather/hot
```

响应包含 `results` 数组。热门城市列表在 `APITRY.py` 中预设。

### 查询单个城市

该接口需要在 `.env` 中配置 `API_TOKEN`，请求时以 Bearer Token 方式传入：

```bash
curl -i \
  -H "Authorization: Bearer 替换为你的API_TOKEN" \
  http://127.0.0.1:8000/weather/%E5%8C%97%E4%BA%AC
```

成功时返回城市名及实时、未来天气数据。错误城市会返回客户端错误；已识别的上游连接错误会返回网关错误。缺少或无效的令牌会被拒绝。

### 批量查询城市

请求体字段是 `city`（单数），值为非空城市名称数组：

```bash
curl -i -X POST http://127.0.0.1:8000/weather/batch \
  -H "Content-Type: application/json" \
  -d '{"city":["北京","上海"]}'
```

响应中：

- `results`：成功查询到的城市天气；
- `errors`：逐个城市查询失败的信息。

### 验证异常处理与追踪 ID

```bash
curl -i http://127.0.0.1:8000/error
```

该接口会触发测试异常。响应体包含 `message`、`code` 和 `trace_id`；正常返回的 API 响应会带有 `X-Trace-ID` 响应头。服务日志写入控制台和项目目录中的 `weather.log`。

## 部署到 Ubuntu 云服务器

以下示例使用 `deploy` 用户、项目目录 `/home/deploy/weather-api`，并由 Nginx 对外提供 HTTP 访问。请将仓库地址替换成自己的仓库地址。

### 1. 安装系统依赖并准备用户

使用有 sudo 权限的账号执行：

```bash
sudo apt update
sudo apt install -y git curl ca-certificates
sudo adduser deploy
sudo usermod -aG sudo deploy
```

切换到 `deploy` 用户：

```bash
sudo -iu deploy
```

安装 uv 并用它安装 Python 3.13：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"
uv python install 3.13
```

如果安装脚本提示需要重新打开终端，重新 SSH 登录后再继续。

### 2. 克隆项目、配置密钥并安装依赖

```bash
git clone <你的仓库地址> /home/deploy/weather-api
cd /home/deploy/weather-api
```

在服务器上创建 `.env` 并填写自己的真实凭据：

```bash
nano .env
chmod 600 .env
```

`.env` 内容格式：

```dotenv
apiKey=你的聚合数据API密钥
API_TOKEN=你自己的访问令牌
```

安装依赖：

```bash
uv sync
```

确认项目可以在服务器本机启动和访问：

```bash
uv run uvicorn APITRY:app --host 127.0.0.1 --port 8000
```

另开一个 SSH 窗口测试：

```bash
curl -i http://127.0.0.1:8000/weather/hot
```

测试完成后按 `Ctrl+C` 停止前台进程。

### 3. 配置 systemd

使用有 sudo 权限的账号创建服务文件：

```bash
sudo nano /etc/systemd/system/weather-api.service
```

填入以下内容：

```ini
[Unit]
Description=Weather API Service
After=network.target

[Service]
User=deploy
WorkingDirectory=/home/deploy/weather-api
ExecStart=/home/deploy/weather-api/.venv/bin/uvicorn APITRY:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

加载并启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now weather-api
sudo systemctl status weather-api
```

查看服务日志：

```bash
sudo journalctl -u weather-api -n 100 --no-pager
```

### 4. 配置 Nginx 反向代理

安装 Nginx：

```bash
sudo apt install -y nginx
```

创建 `/etc/nginx/sites-available/weather-api`：

```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用并检查配置：

```bash
sudo ln -s /etc/nginx/sites-available/weather-api /etc/nginx/sites-enabled/weather-api
sudo nginx -t
sudo systemctl enable --now nginx
sudo systemctl reload nginx
```

如果服务器仍启用了 Nginx 默认欢迎页，访问公网 IP 时可能先命中默认站点。确认 `/etc/nginx/sites-enabled/default` 是默认欢迎页链接后，再停用它并重新加载 Nginx。

在阿里云安全组入方向开放 TCP `22`（建议来源限制为自己的公网 IP）和 TCP `80`。因为 Uvicorn 只监听 `127.0.0.1:8000`，无需将 `8000` 端口开放给公网。配置 HTTPS 后再开放 TCP `443`。

部署完成后访问：

```text
http://你的服务器公网IP/docs
```

如果只想临时绕过 Nginx 直接测试公网访问，需要将 Uvicorn 的监听地址改为 `0.0.0.0`，并在安全组中临时放行 TCP `8000`。测试完成后建议恢复为 Nginx 反向代理方案并关闭公网 `8000` 规则。

## 日志与常用运维命令

应用日志会输出到控制台并追加写入 `weather.log`。systemd 管理的服务日志也可以通过 journal 查看：

```bash
sudo systemctl status weather-api
sudo systemctl restart weather-api
sudo journalctl -u weather-api -f
```

## 项目文件

```text
weather-cli/
├── APITRY.py       # FastAPI 应用、接口、鉴权、中间件和天气查询逻辑
├── pyproject.toml  # 项目元数据和依赖
├── uv.lock         # 锁定的依赖版本
├── .env            # 本地凭据，不提交到 Git
└── README.md
```
