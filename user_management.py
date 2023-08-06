# user_management.py
import os
import sqlite3
from flask import session


db_path = "D:\\bank1\\venv\\bank.db"
print(f"Database path is: {db_path}")


def create_users_table(db_path):
    # 连接到SQLite数据库，数据库文件是D:/bank1/venv/bank.db
    conn = sqlite3.connect(db_path)

    # 创建一个游标对象，你可以用它来执行所有的SQL语句
    c = conn.cursor()

    # 创建一个新的users表
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            real_name TEXT NOT NULL,
            organization TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            is_approved INTEGER DEFAULT 0
        )
    ''')

    # 提交当前事务
    conn.commit()

    # 关闭连接
    conn.close()



def register_user(username, password, real_name, organization, phone_number):
    # 连接到SQLite数据库
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("SELECT username FROM users WHERE username = ?;", (username,))
    if c.fetchone() is not None:
        return False

    c.execute('''
        INSERT INTO users (username, password, real_name, organization, phone_number, is_approved)
        VALUES (?, ?, ?, ?, ?, 0)
    ''', (username, password, real_name, organization, phone_number))

    conn.commit()
    conn.close()

    return True


def valid_login(username, password):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("SELECT password FROM users WHERE username = ?;", (username,))
    result = c.fetchone()

    conn.close()

    if result is None:
        return False

    return result[0] == password

def log_the_user_in(username):
    session['username'] = username



def get_user_type(username):
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute('SELECT is_admin FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        if user and user[0] == 1:  # 注意这里的比较，确保你在数据库中的 is_admin 字段是整数类型
            return 'admin'
    return 'user'


def get_user_by_username(username):
    conn = sqlite3.connect(db_path)  # 使用db_path，而不是DATABASE
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    return user

def get_all_users():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("SELECT * FROM users")
    users = c.fetchall()

    conn.close()

    users_dict = []

    for user in users:
        user_dict = {
            'username': user[0],
            'password': user[1],
            'real_name': user[2],
            'organization': user[3],
            'phone_number': user[4],
            'is_admin': user[5],
            'is_approved': user[6]
        }

        users_dict.append(user_dict)

    return users_dict


def approve_user(username):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("UPDATE users SET is_approved = 1 WHERE username=?", (username,))

    conn.commit()
    conn.close()

def delete_user(username):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("DELETE FROM users WHERE username=?", (username,))

    conn.commit()
    conn.close()





