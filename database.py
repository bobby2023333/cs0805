import os
import sqlite3
from sqlite3 import Error
from datetime import datetime
import pytz

beijing_tz = pytz.timezone('Asia/Shanghai')
current_time = datetime.now(beijing_tz)
current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")




import pdb  # 导入pdb模块

def get_all_files(username):
    directory = os.path.join('D:\\bank1\\uploads\\', username)
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]



    return files




def create_connection():
    conn = None;
    try:
        # 这里的 bank.db 是数据库的路径，你需要替换成自己的路径
        conn = sqlite3.connect('bank.db')
        print(sqlite3.version)
    except Error as e:
        print(e)
    return conn
def create_user_folder(username):
    user_folder = os.path.join('D:\\bank1\\uploads', username)

    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    return user_folder





def close_connection(conn):
    conn.close()


def save_file_info(conn, username, filename, filepath, upload_time):
    """
    把文件信息保存到数据库。

    参数：
    conn: 数据库连接。
    username: 上传文件的用户名。
    filename: 文件的原始名字。
    filepath: 文件保存的路径。
    upload_time: 文件上传的时间。
    """
    cursor = conn.cursor()

    sql = '''
    INSERT INTO user_files(username, filename, filepath, upload_time)
    VALUES(?, ?, ?, ?)
    '''

    cursor.execute(sql, (username, filename, filepath, upload_time))

    # 提交改变
    conn.commit()

def create_table(conn):
    """
    创建 user_files 表，如果它还不存在的话。

    参数：
    conn: 数据库连接。
    """
    cursor = conn.cursor()

    # 创建表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_files(
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        filename TEXT NOT NULL,
        filepath TEXT NOT NULL,
        upload_time TEXT NOT NULL
    )
    """)

    # 提交改变
    conn.commit()

def get_user_files(conn, username):
    cursor = conn.cursor()
    query = "SELECT filename, upload_time FROM user_files WHERE username = ?"
    cursor.execute(query, (username,))
    files = cursor.fetchall()
    return files

def get_merged_files(conn, username):
    cursor = conn.cursor()
    query = "SELECT filename, merge_time FROM merged_files WHERE username = ?"
    cursor.execute(query, (username,))
    files = cursor.fetchall()
    return files

def delete_data_from_db(file):
    # 建立数据库连接（取决于你的数据库设置和使用的库）
    conn = sqlite3.connect('my_database.db')  # replace with your connection info
    cursor = conn.cursor()

    # 执行删除操作
    cursor.execute("DELETE FROM data WHERE filename = ? AND username = ?", (file, session['username']))

    # 提交事务
    conn.commit()

    # 关闭连接
    conn.close()


