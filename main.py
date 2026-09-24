import requests
import json
import os
import logging
from pydantic import BaseModel, Field
from dotenv import load_dotenv
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] %(message)s",
#     filename='weather.log',
#     filemode='a',
#     encoding='utf-8'
# )
#创建Logger对象
logger=logging.getLogger('weather_logger')
logger.setLevel(logging.INFO)
#创建控制台处理器
console_handler=logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
#创建文件处理器
file_handler=logging.FileHandler('weather.log',mode='a',encoding='utf-8')
file_handler.setLevel(logging.INFO)
#创建格式器
formatter=logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
#将格式器添加到处理器
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
#将处理器添加到Logger对象
logger.addHandler(console_handler)
logger.addHandler(file_handler)
#错误的城市查询名
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
def main():
    str="这里我做了一个天气查询的命令行工具，使用了聚合数据的天气API。"
    url1="https://apis.juhe.cn/simpleWeather/query"
    load_dotenv()
    apiKey=os.getenv("apiKey")
    city=input("请输入城市名称: ")
    params={
        'city':city,
        'key':apiKey
    }
    try:
        response=requests.get(url1,params=params,timeout=5)
        response.raise_for_status()  # Raise an exception for HTTP errors
        logger.info(f"Request URL: {response.url}, Status Code: {response.status_code}")
        filename='weather.json'
        if response.ok:
            data=response.json()
            weather_response=WeatherResponse.model_validate(data)
            match weather_response.error_code:
                case 207303:
                    raise ConnectionError
                case 207301:
                    raise WrongCityNameError(f"城市名称错误: {city}")
            logger.info(f"Weather data retrieved successfully for city: {city}")
            print(f"城市: {weather_response.result.city},今日温度：{weather_response.result.realtime.temperature}℃,天气: {weather_response.result.realtime.info}")
            with open(filename,'w',encoding='utf-8') as myfile:
                json.dump(data,myfile,ensure_ascii=False,indent=4)
                print("success")
                logger.info(f"Weather data saved to {filename}")
    except ConnectionError as e:
        logger.error(f"Connection error: {e}")
        print("网络连接错误，请检查您的网络连接。")
    except WrongCityNameError as e:
        logger.error(f"Wrong city name error: {e}")
        print(e)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        print("发生了一个意外错误，请稍后再试。")
if __name__ == "__main__":
    main()
