import os
import logging
import requests
import json
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel,Field
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException,Depends
from fastapi.security import HTTPAuthorizationCredentials , HTTPBearer
from fastapi.responses import JSONResponse
#日志
logger=logging.getLogger('weather_logger')
logger.setLevel(logging.INFO)
console_handler=logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
file_handler=logging.FileHandler('weather.log',mode='a',encoding='utf-8')
file_handler.setLevel(logging.INFO)
formatter=logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

load_dotenv()
API_URL="https://apis.juhe.cn/simpleWeather/query"
API_KEY=os.getenv("apiKey")
app=FastAPI(title="天气查询API",version="1.0",docs_url="/docs")
#---------------------------------------------------------
class WrongCityNameError(Exception):
    pass
class FutureWid(BaseModel):
    day:  str
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
    city:   str=Field(min_length=1)
class WeatherResponse(BaseModel):
    result: WeatherResult | None
    error_code: int

class WeatherRequest(BaseModel):
    city: list[str] = Field(min_length=1,description="城市查询列表")
#---------------------------------------------------------中间件
class TracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self,request,call_next):
        trace_id= str(uuid.uuid4())[:8]
        request.state.trace_id=trace_id
        start=time.time()
        response = await call_next(request)
        duration_ms = (time.time()-start) *1000
        log_entry=json.dumps({
            "trace_id" : trace_id,
            "method" : request.method,   
            "duration_ms" : round(duration_ms, 2),        
            "path" : request.url.path,
            "status_code" : response.status_code
            }
        )
        logger.info(log_entry)
        response.headers["X-Trace-ID"] = trace_id
        return response


app.add_middleware(TracingMiddleware)
#鉴权---------------------------------------------------------
security = HTTPBearer()
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if token != os.getenv("API_TOKEN"):
        raise HTTPException(status_code=401,detail="无效的token")
    return credentials.credentials
#---------------------------------------------------------
def fetch_weather(city:str) -> dict|None:
    params={
        "city":city,
        "key":API_KEY
    }
    try:
        response=requests.get(API_URL,params=params,timeout=5)
        response.raise_for_status()
        weather_response=WeatherResponse.model_validate(response.json())
        match weather_response.error_code:
            case 207303:
                raise ConnectionError("上游接口连接错误")
            case 207301:
                raise WrongCityNameError(f"城市名称错误：{city}")

        logger.info(f"Weather data retrieved successfully for {city}")
        return weather_response.result.model_dump(exclude={"city"})

    except WrongCityNameError as e:
        logger.error(f"Wrong city name error: {e}")
        raise HTTPException(status_code=400, detail=str(e))    
    except ConnectionError as e:
        logger.error(f"Connection error: {e}")
        raise HTTPException(status_code=502, detail=str(e)) 
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误，请稍后再试")
#------------------ -------------------------------------------------------
#接口
@app.get("/weather/hot")
async def get_hot_weather():
    """查询热门城市的天气"""
    hot_citys=["北京","上海","广州","深圳","杭州","南京","成都","重庆","武汉"]
    results=[]
    for hot_city in hot_citys:
        try:
            result=fetch_weather(hot_city)
            if result:
                results.append({"city":hot_city,**result})
        except HTTPException as e:
            logger.error(f"Error fetching weather for {hot_city}: {e.detail}")
            continue
    return {"results":results}
        

@app.get("/weather/{city}")
async def get_weather(city:str,token : str = Depends(verify_token)):
    """查询单个城市的天气"""
    result=fetch_weather(city)
    if not result:
        raise HTTPException(status_code=404,detail=f"未找到城市：{city}")
    return {"city":city,**result}

@app.post("/weather/batch")
async def get_weather_batch(request:WeatherRequest):
    """批量查询多个城市的天气，单个城市失败不影响整体"""
    results,errors=[],[]
    for city in request.city:
        try:
            result=fetch_weather(city)
            if  result:
                results.append({"city":city,**result})
            else:
                errors.append({"city":city,"detail":f"未找到城市：{city}"})
        except HTTPException as e:
            errors.append({"city":city,"detail":e.detail})
    return {"results":results,"errors":errors}
#---------------------------------------------------------
#统一异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request,exc):
    trace_id=getattr(request.state,"trace_id","unknown")
    return JSONResponse(
        status_code=500,
        content={
            "message":str(exc),
            "code":500,
            "trace_id":trace_id,
        }
    )
#---------------------------------------------------------
#异常测试接口
@app.get("/error")
async def error():
    raise Exception("测试异常处理")