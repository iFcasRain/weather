"""天气查询 API —— 复用第一周 CLI 的查询逻辑，暴露为 HTTP 接口。

运行方式：
    uvicorn mainAPI:app --reload

接口：
    GET  /weather/{city}      单城市查询
    POST /weather/batch       批量查询
"""

import logging
import os

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

load_dotenv()

# ---------------------------------------------------------------------------
# 日志（沿用 main.py 的配置）
# ---------------------------------------------------------------------------
logger = logging.getLogger("weather_api_logger")
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
file_handler = logging.FileHandler("weather.log", mode="a", encoding="utf-8")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
API_URL = "https://apis.juhe.cn/simpleWeather/query"
API_KEY = os.getenv("apiKey")

app = FastAPI(title="天气查询 API", version="1.0")


# ---------------------------------------------------------------------------
# 数据模型（与聚合天气 API 返回结构对应）
# ---------------------------------------------------------------------------
class FutureWid(BaseModel):
    day: str
    night: str


class FutureItem(BaseModel):
    date: str
    temperature: str
    weather: str
    wid: FutureWid
    direct: str


class RealTime(BaseModel):
    temperature: str
    humidity: str
    info: str
    wid: str
    direct: str
    power: str
    aqi: str


class WeatherResult(BaseModel):
    realtime: RealTime
    future: list[FutureItem]
    city: str = Field(min_length=1)


class WeatherResponse(BaseModel):
    result: WeatherResult | None
    error_code: int


class WeatherRequest(BaseModel):
    cities: list[str] = Field(min_length=1, description="要批量查询的城市列表")


class WrongCityNameError(Exception):
    pass


# ---------------------------------------------------------------------------
# 核心查询逻辑（第一周 CLI 中的 main() 逻辑抽取而来）
# ---------------------------------------------------------------------------
def fetch_weather(city: str) -> dict | None:
    """查询单个城市的天气。

    返回不含 city 字段的结果字典（realtime + future），
    城市名错误时返回 None，网络/上游错误时抛 HTTPException。
    """
    if not API_KEY:
        raise HTTPException(status_code=500, detail="服务端未配置 apiKey")

    params = {"city": city, "key": API_KEY}
    try:
        response = requests.get(API_URL, params=params, timeout=5)
        response.raise_for_status()
        weather_response = WeatherResponse.model_validate(response.json())

        match weather_response.error_code:
            case 207303:
                raise ConnectionError("上游接口连接错误")
            case 207301:
                raise WrongCityNameError(f"城市名称错误: {city}")

        logger.info(f"Weather data retrieved successfully for city: {city}")
        return weather_response.result.model_dump(exclude={"city"})

    except WrongCityNameError:
        return None
    except ConnectionError as e:
        logger.error(f"Connection error: {e}")
        raise HTTPException(status_code=502, detail="上游天气服务不可用，请稍后再试")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=502, detail="查询失败，请稍后再试")


# ---------------------------------------------------------------------------
# 接口
# ---------------------------------------------------------------------------
@app.get("/weather/{city}")
async def get_weather(city: str):
    """根据城市名查询天气"""
    result = fetch_weather(city)
    if not result:
        raise HTTPException(status_code=404, detail=f"未找到 {city} 的天气数据")
    return {"city": city, **result}


@app.post("/weather/batch")
async def batch_weather(request: WeatherRequest):
    """批量查询多个城市，单个城市失败不影响整体"""
    results, errors = [], []
    for city in request.cities:
        try:
            result = fetch_weather(city)
            if result:
                results.append({"city": city, **result})
            else:
                errors.append({"city": city, "detail": f"未找到 {city} 的天气数据"})
        except HTTPException as e:
            errors.append({"city": city, "detail": e.detail})
    return {"results": results, "errors": errors}
