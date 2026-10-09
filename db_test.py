import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

connection = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_name"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)
try:
    cursor = connection.cursor()
    cursor.execute("SELECT DATABASE()")
    row = cursor.fetchall()
    print("连接成功，当前数据库：" , row[0])
finally:
    cursor.close()
    connection.close()
    