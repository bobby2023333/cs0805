import pandas as pd
import os
from database import save_file_info  # 假设你已经创建了一个函数来保存文件信息
from database import create_user_folder


class DataProcessor:
    def __init__(self):
        pass






def save_file_path_to_database(conn, username, filename, filepath):
        try:
            # 创建一个游标对象
            cursor = conn.cursor()

            # 执行SQL语句
            cursor.execute("""
            INSERT INTO user_files (username, filename, filepath)
            VALUES (?, ?, ?)
            """, (username, filename, filepath))

            # 提交事务
            conn.commit()
        except Exception as e:
            print(f"An error occurred: {e}")


def allowed_file(filename):
    ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv'])  # 你可以根据你的需要修改这个列表
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


