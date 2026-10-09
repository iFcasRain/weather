import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.environ["DB_PORT"]),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.environ["DB_NAME"],
    )

def save_weather_history(
city:str,
    temperature:float,
    description:str,
    humidity:int,
)->int | None:
    connection=get_connection()
    cursor=connection.cursor()
    try:
        sql="""
        	INSERT INTO weather_history
        		(city,temperature,description,humidity)
        	VALUES
        		(%s,%s,%s,%s)
        """
        # """是多行字符串的输入 """
        # SQL中用%s 作为参数占用符，真正的值放在values元组中
        values = (city,temperature,description,humidity)
        cursor.execute(sql,values)    
        connection.commit()
        #确认写入，让改动正式生效
        return cursor.lastrowid
    except Exception:
        connection.rollback()
        #发生错误时撤销尚未提交的改动
        raise
    finally:
        cursor.close()
        connection.close()
def get_weather_history(city: str, limit: int = 20) -> list[dict]:
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        sql = """
            SELECT id, city, temperature, description, humidity, query_time
            FROM weather_history
            WHERE city = %s
            ORDER BY query_time DESC, id DESC
            LIMIT %s
        """

        cursor.execute(sql, (city, limit))
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()
def get_weather_stats()->list[dict]:
    connection = get_connection()
    cursor=connection.cursor(dictionary=True)
    
    try:
        sql = """
        SELECT city,COUNT(*) AS query_count
        FROM weather_history
        GROUP BY city
        ORDER BY query_count DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()