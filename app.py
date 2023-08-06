# 导入所有必需的模块和库
from flask import Flask, render_template, request, redirect, url_for, session, flash, get_flashed_messages, make_response, send_file, jsonify
from werkzeug.utils import secure_filename
from flask_login import login_required, LoginManager, UserMixin
from sqlalchemy import TypeDecorator, case, text, MetaData, Table, inspect, func, create_engine, Integer, String, Boolean, Float, Date, DateTime
from datetime import datetime
from dateutil import parser
import os
import sqlite3
import pytz
import pandas as pd
import shutil
import zipfile
import csv
import logging
from flask_login import LoginManager, UserMixin
from database import create_user_folder
from data_processing import allowed_file, save_file_path_to_database
from data_processing import DataProcessor
from database import save_file_info
from dtzs import txzs
from extensions import db
from models import User
from models import FxData
from models import UserUpload
from dtzs import txzs
from unidecode import unidecode
import re
from flask_paginate import Pagination, get_page_args
from database import get_all_files
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy


from flask import Flask

from data_cleaning import data_cleaning
from extensions import init_extensions

app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////D:/bank1/venv/bank.db'

db = SQLAlchemy(app)


CORS(app)
# 设置应用的密钥
app.secret_key = os.environ.get('SECRET_KEY') or 'your-default-secret-key'
app.register_blueprint(data_cleaning, url_prefix='/data_cleaning')


print(app.config.get('SQLALCHEMY_DATABASE_URI'))





app.register_blueprint(txzs, url_prefix='/txzs')

login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 在这里获取当前时间
beijing_tz = pytz.timezone('Asia/Shanghai')
current_time = datetime.now(beijing_tz)
current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")

# 保存文件信息
upload_time = "some time information"


# 定义所有的数据库模型
class CustomDate(TypeDecorator):
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return parser.parse(value)

    def process_result_value(self, value, dialect):
        if isinstance(value, datetime):  # 使用datetime，而不是datetime.datetime
            return value
        else:
            return parser.parse(value)

def secure_filename_chinese(filename):
    # 允许中文字符、字母、数字、"-"、"_"、"."、" "（空格）
    filename = re.sub(r'[^\w\s.-]', '', filename).strip()
    return filename

class Pagination:
    def __init__(self, page, total, per_page, record_name):
        self.page = page
        self.total = total
        self.per_page = per_page
        self.record_name = record_name

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page * self.per_page < self.total

    @property
    def next_num(self):
        return self.page + 1

    @property
    def prev_num(self):
        return self.page - 1

    @property
    def total_pages(self):
        return self.total // self.per_page + (self.total % self.per_page > 0)





# 定义所有的路由和视图函数
@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.password == password and not user.is_admin:
            session['username'] = username
            return redirect(url_for('main_page'))
        else:
            return "用户名或密码错误，或你不是普通用户"

    return render_template('login.html')

@app.route('/main')
def main_page():
    return render_template('main.html')

@app.route('/some_protected_page')
def some_protected_page():
    if 'username' not in session:
        return redirect(url_for('login'))

    return render_template('some_protected_page.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        real_name = request.form['real_name']
        organization = request.form['organization']
        phone_number = request.form['phone_number']

        if password != confirm_password:
            error = '两次输入的密码不一致。'
            return render_template('register.html', error=error)

        new_user = User(username=username, password=password, organization=organization, phone=phone_number)
        db.session.add(new_user)
        db.session.commit()

        flash('注册信息已提交，等待管理员审核！')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/create_admin', methods=['GET', 'POST'])
def create_admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        real_name = request.form['real_name']
        organization = request.form['organization']
        phone_number = request.form['phone_number']

        new_admin = User(username=username, password=password, organization=organization, phone=phone_number, is_admin=True)
        db.session.add(new_admin)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('create_admin.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.password == password and user.is_admin:
            session['username'] = username
            return redirect(url_for('admin_review'))
        else:
            return "用户名或密码错误，或你不是管理员"

    return render_template('admin_login.html')

@app.route('/admin_review', methods=['GET', 'POST'])
def admin_review():
    username = session.get('username')

    user = User.query.filter_by(username=username).first()

    if not user or not user.is_admin:
        return "你不是管理员"

    if request.method == 'POST':
        users = User.query.all()

        if 'delete' in request.form:
            for user in users:
                username = user.username
                if 'selected_' + username in request.form:
                    db.session.delete(user)

            db.session.commit()

        else:
            for form_key in request.form.keys():
                if form_key.startswith('approve_'):
                    username_to_approve = form_key.split('_')[1]
                    user = User.query.filter_by(username=username_to_approve).first()
                    user.is_admin = True
                    user.is_approved = True

            db.session.commit()

    users = User.query.all()

    print(users)

    return render_template('admin_review.html', users=users)


@app.route('/upload', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        # 获取当前登录的用户名
        username = session.get('username')
        if not username:
            return redirect(url_for('login'))

        # 检查是否有文件被上传
        if 'files[]' not in request.files:
            flash('No file part')
            return redirect(request.url)

        # 创建用户文件夹
        user_folder = create_user_folder(username)

        file_list = request.files.getlist('files[]')

        # 建立数据库连接
        conn = sqlite3.connect('D:\\bank1\\venv\\bank.db')

        # 遍历用户上传的每一个文件
        try:
            for file in file_list:
                if file and allowed_file(file.filename):
                    filename = secure_filename_chinese(file.filename)  # 使用新的函数
                    csv_filename = os.path.splitext(filename)[0] + '.csv'  # 生成csv文件名
                    csv_file_path = os.path.join(user_folder, csv_filename)

                    # 如果已存在同名文件，添加序号直到文件名唯一
                    counter = 1
                    while os.path.exists(csv_file_path):
                        name, ext = os.path.splitext(csv_filename)
                        csv_filename = f"{name}_{counter}{ext}"
                        csv_file_path = os.path.join(user_folder, csv_filename)
                        counter += 1

                    # 如果文件是Excel或CSV，转换为utf-8编码的csv文件
                    try:
                        df = pd.read_excel(file) if file.filename.endswith(('.xls', '.xlsx')) else pd.read_csv(file)
                    except UnicodeDecodeError:  # 处理不是UTF-8编码的csv文件
                        df = pd.read_csv(file, encoding='ISO-8859-1')  # 假设文件编码为 'ISO-8859-1'
                    except pd.errors.EmptyDataError:  # 处理没有内容的csv文件
                        flash(f"文件 '{filename}' 没有内容，无法上传。")
                        continue
                    except Exception as e:  # 处理其他异常
                        print(f"An error occurred while reading the file: {e}")
                        continue

                    # 检查DataFrame是否为空
                    if df.empty:
                        flash(f"文件 '{filename}' 没有内容，无法上传。")
                        continue

                    df.to_csv(csv_file_path, index=False, encoding='utf-8')
                    file_path = csv_file_path  # 更新为csv文件路径
                    filename = csv_filename  # 更新为csv文件名

                    print(f"Saving file to {file_path}")
                    print(f"File saved successfully")

                    # 将文件路径保存在数据库中
                    print(
                        f"About to save file info: username={username}, filename={filename}, filepath={file_path}, upload_time={current_time_str}")
                    save_file_info(conn, username, filename, file_path, current_time_str)

            flash("文件上传成功！")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            # 关闭数据库连接
            conn.close()

        return redirect(url_for('upload_files'))

    else:
        return render_template('upload.html')



@app.route('/logout')
def logout():
    # Remove username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/merge_page')
def merge_page():
    UPLOAD_FOLDER = 'D:/bank1/uploads/'
    user_folder = session.get('username')  # Get username from session
    user_upload_folder = os.path.join(UPLOAD_FOLDER, user_folder)

    if os.path.exists(user_upload_folder):
        # 读取目录下的所有文件
        all_files = os.listdir(user_upload_folder)
        # 过滤掉不存在的文件
        existing_files = [file for file in all_files if os.path.exists(os.path.join(user_upload_folder, file))]

        # Pagination
        per_page = 10
        current_page = request.args.get('page', 1, type=int)
        start = (current_page - 1) * per_page
        end = start + per_page

        files = existing_files[start:end]

        pagination = Pagination(page=current_page, total=len(existing_files), per_page=per_page, record_name='files')

        return render_template('merge_page.html', files=files, pagination=pagination)
    else:
        return "No files found for the user."



@app.route('/delete_selected', methods=['POST'])
def delete_files():
    selected_files = request.form.getlist('selected_files')

    print("Selected files:", selected_files)  # Debugging line

    UPLOAD_FOLDER = 'D:/bank1/uploads/'
    user_folder = session.get('username')  # Get username from session

    for file in selected_files:
        file_path = os.path.join(UPLOAD_FOLDER, user_folder, file)

        print("File path:", file_path)  # Debugging line

        # Check if the path is a file or a directory
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)

    flash('文件已被删除')
    return redirect(url_for('merge_page'))


from flask import session

@app.route('/merge_selected', methods=['POST'])
def merge_files():
    selected_files = request.form.getlist('selected_files')
    print(f"Selected files: {selected_files}")
    username = session.get('username')  # 获取存储在 session 中的用户名

    # 根据选中的文件路径列表，使用Pandas将它们读取为数据框，指定编码为utf_8_sig
    dfs = [pd.read_csv(os.path.join(f'D:\\bank1\\uploads\\{username}', file), encoding='utf_8_sig') for file in selected_files]

    # 使用concat方法将所有数据框合并为一个
    merged_df = pd.concat(dfs, ignore_index=True)

    # 创建合并文件的目标文件夹，如果不存在的话
    user_folder = os.path.join('D:\\bank1\\static\\merged_files\\', username)  # 使用动态用户名
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    # 使用当前时间生成文件名
    filename = 'merged_' + datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'
    target_path = os.path.join(user_folder, filename)

    # 将合并后的数据框写入CSV文件，使用utf_8_sig编码以避免中文乱码
    merged_df = merged_df.applymap(lambda x: f"=\"{x}\"" if isinstance(x, (int, float)) else x)  # 避免大数字被转化为科学计数法
    merged_df.to_csv(target_path, index=False, encoding='utf_8_sig')

    flash('文件成功合并')
    return redirect(url_for('merge_page'))


import json
@app.route('/select_all', methods=['POST'])
def select_all():
    session['select_all'] = True
    return '', 200  # 返回一个空的 200 OK 响应

@app.route('/parallel_merge_selected', methods=['POST'])
def parallel_merge_files():
    username = session.get('username')  # 获取存储在 session 中的用户名
    if session.get('select_all'):
        # 获取所有文件
        folder_path = f'D:\\bank1\\uploads\\{username}'
        selected_files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        # 重置全选状态
        session['select_all'] = False
    else:
        # 获取提交的文件
        selected_files = request.form.getlist('selected_files')

    if not selected_files:
        flash('请选择至少一个文件')
        return redirect(url_for('merge_page'))

    if len(selected_files) < 2:
        flash('并列合并需要至少两个文件')
        return redirect(url_for('merge_page'))

    # 分别存储A类和B类文件
    a_dfs = []
    b_dfs = []

    for file in selected_files:
        df = pd.read_csv(os.path.join(f'D:\\bank1\\uploads\\{username}', file), dtype={'开户人证件号码': str})

        df.columns = df.columns.str.strip()

        if "交易账号" not in df.columns:
            flash(f'文件"{file}"中找不到"交易账号"列')
            return redirect(url_for('merge_page'))

        # 判断文件类型并存储
        if '账户开户名称' in df.columns and '开户人证件号码' in df.columns and '账号开户银行' in df.columns:
            df = df[['交易账号', '账户开户名称', '开户人证件号码', '账号开户银行']]  # 只保留需要的列
            b_dfs.append(df)
        else:
            a_dfs.append(df)

    # 合并A类和B类文件
    a_df = pd.concat(a_dfs)
    b_df = pd.concat(b_dfs)

    # 使用交易账号合并两类文件
    merged_df = pd.merge(a_df, b_df, on='交易账号', how='outer')

    # 确保'账户开户名称', '开户人证件号码', '账号开户银行'在最前
    cols = ['账户开户名称', '开户人证件号码', '账号开户银行'] + [col for col in merged_df.columns if col not in ['账户开户名称', '开户人证件号码', '账号开户银行']]
    merged_df = merged_df[cols]

    # 创建合并文件的目标文件夹，如果不存在的话
    user_folder = os.path.join('D:\\bank1\\static\\merged_files\\', username)  # 使用动态用户名
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    # 使用当前时间生成文件名
    filename = 'parallel_merged_' + datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'
    target_path = os.path.join(user_folder, filename)

    # 将合并后的数据框写入CSV文件，使用utf_8_sig编码以避免中文乱码
    # 修改这部分代码
    merged_df = merged_df.applymap(lambda x: f"=\"'{x}\"" if isinstance(x, (int, float)) else x)

    # 写入CSV文件
    merged_df.to_csv(target_path, index=False, encoding='utf_8_sig')

    flash('并列文件成功合并')
    return redirect(url_for('merge_page'))







@app.route('/select_all_files', methods=['POST'])
def select_all_files():
    username = session.get('username')  # 从 session 获取用户名
    files = get_all_files(username)  # 从你的文件目录中获取所有文件的列表
    print(files)
    return jsonify({'files': files})  # 以 JSON 格式返回文件列表

@app.route('/deselect_all_files', methods=['POST'])
def deselect_all_files():
    # 取消全选，这里我们什么都不做，只返回一个空的 JSON 对象
    return jsonify({})





from flask import send_from_directory


@app.route('/mexport')
def mexport():
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    user_folder = session.get('username')  # Get username from session
    user_folder_path = os.path.join('D:/bank1/static/merged_files/', user_folder)

    if os.path.exists(user_folder_path):
        # Get only .csv files
        total_files = [f for f in os.listdir(user_folder_path) if f.endswith('.csv')]
        total = len(total_files)
        files = total_files[offset: offset + per_page]
        pagination = Pagination(page=page, per_page=per_page, total=total, record_name='files')

        total_pages = (total + per_page - 1) // per_page  # calculate the total number of pages

        return render_template('mexport.html', files=files, pagination=pagination, total_pages=total_pages)
    else:
        return "No files found for the user."




last_zip = None

@app.route('/export_selected', methods=['POST'])
def export_selected():
    global last_zip
    if last_zip and os.path.exists(last_zip):
        os.remove(last_zip)

    selected_files = request.form.getlist('selected_files')

    # If no files were selected for download
    if not selected_files:
        flash('No files were selected for download.', 'error')
        return redirect(url_for('mexport'))

    EXPORT_FOLDER = 'D:/bank1/static/merged_files/'
    user_export_folder = os.path.join(EXPORT_FOLDER, session.get('username'))

    zipf = zipfile.ZipFile('MyExportedFiles.zip', 'w', zipfile.ZIP_DEFLATED)

    for file in selected_files:
        file_path = os.path.join(user_export_folder, file)
        if os.path.exists(file_path):
            # Only use the base filename (no directories) in the zip file
            zipf.write(file_path, arcname=os.path.basename(file_path))
            os.remove(file_path)  # Delete the file after adding it to the zip
        else:
            flash(f'Error: File {file} not found.', 'error')
            return redirect(url_for('mexport'))

    zipf.close()
    last_zip = 'MyExportedFiles.zip'
    flash('Selected files have been downloaded', 'success')
    return send_file(last_zip, mimetype='application/zip', as_attachment=True)


@app.route('/delete_merged', methods=['POST'])
def delete_merged_files():
    selected_files = request.form.getlist('selected_files')

    # If no files were selected to be deleted
    if not selected_files:
        flash('No files were selected to delete.', 'error')
        return redirect(url_for('mexport'))

    MERGED_FOLDER = 'D:/bank1/static/merged_files/'
    user_folder = session.get('username')  # Get username from session
    user_merged_folder = os.path.join(MERGED_FOLDER, user_folder)

    for file in selected_files:
        file_path = os.path.join(user_merged_folder, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
            flash(f'Successfully deleted {file}!', 'success')
        else:
            flash(f'Error: {file} does not exist.', 'error')

    flash('Selected files have been deleted')

    # 重定向回 'mexport' 页面
    return redirect(url_for('mexport'))

# 在 Flask 应用中添加新路由

from flask import request, jsonify, render_template
from sqlalchemy import func
from datetime import datetime
from app import FxData

@app.route('/analysis', methods=['GET', 'POST'])
def analysis():
    global tables  # Declare tables as a global variable
    if 'tables' not in globals():  # If tables does not exist, create it
        tables = {}

    logging.info("Entered /analysis route")

    MERGED_FOLDER = 'D:/bank1/static/merged_files/'
    user_folder = session.get('username')  # Get username from session
    if user_folder is None:
        flash('You are not logged in.', 'error')
        logging.warning("User not logged in")
        return redirect(url_for('login'))  # Or some other appropriate action
    user_merged_folder = os.path.join(MERGED_FOLDER, user_folder)
    logging.info(f"User merged folder: {user_merged_folder}")

    table_name = 'fxdata'  # change this to your actual table name
    metadata = MetaData()
    inspector = inspect(db.engine)

    # check if table exists, create if not
    if not inspector.has_table(table_name):
        logging.info(f"Table {table_name} does not exist, creating")
        new_table = Table(table_name, metadata,
            db.Column('username', db.String),
            db.Column('filename', db.String),
            # add other columns as necessary
        )
        metadata.create_all(db.engine)
        tables[table_name] = new_table
    # rest of your code...

    else:
        if table_name not in tables:
            logging.info(f"Reflecting table {table_name}")
            metadata.reflect(bind=db.engine)
            tables[table_name] = metadata.tables[table_name]

    # ... rest of your code ...

    if request.method == 'POST':
        logging.info("Handling POST request")
        selected_files = request.form.getlist('selected_files')
        logging.info(f"Selected files: {selected_files}")

        if not selected_files:
            flash('No files were selected to analyze.', 'error')
            logging.warning("No files selected for analysis")
            return redirect(url_for('analysis'))

        for file in selected_files:
            # load file into dataframe
            df = pd.read_csv(os.path.join(user_merged_folder, file))
            unique_dates = df['date'].unique()
            logging.info(f"Unique dates in file {file}: {unique_dates}")

            # 转换日期格式
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d').dt.strftime('%Y-%m-%d')

            # add new columns
            df['username'] = session.get('username')
            df['filename'] = file

            # write to database
            try:
                df.to_sql(table_name, con=db.engine, if_exists='append', index=False)
                logging.info(f"Written data to table {table_name}")
            except Exception as e:
                logging.error(f"Error writing to database: {e}")

        flash('Selected files have been stored to the database')
        return redirect(url_for('analysis'))

    # Get all files in the merged folder
    files = os.listdir(user_merged_folder)
    logging.info(f"Files in user merged folder: {files}")

    # Get all saved files from the database for the current user
    saved_files_query = db.session.query(tables[table_name]).filter_by(username=user_folder)
    try:
        saved_files = [row.filename for row in saved_files_query.all() if isinstance(row.filename, str)]
        logging.info(f"Saved files: {saved_files}")
    except Exception as e:
        logging.error(f"Error querying saved files: {e}")
        saved_files = []  # Assign a default value in case of error

    filenames = [filename[0] for filename in db.session.query(tables[table_name].c.filename).distinct()]
    logging.info(f"Distinct filenames: {filenames}")
    return render_template('analysis.html', files=files, saved_files=saved_files, filenames=filenames)

@app.route('/check_file', methods=['GET'])
def check_file():
    filename = request.args.get('filename')
    logging.info(f"Checking file: {filename}")
    sql = text("SELECT EXISTS(SELECT 1 FROM fxdata WHERE filename=:filename)")
    result = db.session.execute(sql, params={'filename': filename}).scalar()
    logging.info(f"Check file result: {result}")
    return jsonify({'saved': result})

#...




from flask import request, jsonify, render_template
from sqlalchemy import func
from datetime import datetime
from app import FxData


@app.route('/txfx', methods=['GET', 'POST'])

def txfx():
    page = request.args.get('page', 1, type=int)
    filenames = db.session.query(FxData.filename).distinct().paginate(page=page, per_page=5)
    return render_template('txfx.html', filenames=filenames)


@app.route('/api-to-call', methods=['POST'])
def handle_file_analysis():
    filenames = request.json['filenames']
    print("Received these files for analysis: ", filenames)

    results = []
    for filename in filenames:
        query_results = db.session.query(
            func.min(FxData.date).label('start_date'),
            func.max(FxData.date).label('end_date'),
            func.sum(FxData.shouru).label('sum_shouru'),
            func.count(case((FxData.shouru != 0, 1))).label('count_shouru'),
            func.sum(FxData.zhichu).label('sum_zhichu'),
            func.count(case((FxData.zhichu != 0, 1))).label('count_zhichu')
        ).filter(FxData.filename == filename).first()

        if query_results is None or query_results.start_date is None:
            return jsonify({"error": f"No data found for filename {filename}"}), 404

        start_date, end_date, sum_shouru, count_shouru, sum_zhichu, count_zhichu = query_results

        # Calculate yue as the difference between total shouru and total zhichu
        calculated_yue = sum_shouru - sum_zhichu

        if isinstance(start_date, datetime):
            start_date = start_date.strftime("%Y年%m月%d日")

        if isinstance(end_date, datetime):
            end_date = end_date.strftime("%Y年%m月%d日")

        results.append({
            'start_date': start_date,
            'end_date': end_date,
            'calculated_yue': calculated_yue,
            'count_shouru': count_shouru,
            'sum_shouru': sum_shouru,
            'count_zhichu': count_zhichu,
            'sum_zhichu': sum_zhichu,
        })

    return jsonify(results)




@app.route('/analysis_result/<int:result_id>')
def analysis_result(result_id):
    result = Result.query.get(result_id)

    if not result:
        flash('Result not found.', 'error')
        return redirect(url_for('txfx'))

    return render_template('analysis_result.html', result=result)


@app.route('/api-to-call-visualization', methods=['POST'])
def handle_files_for_visualization():
    filenames = request.json['filenames']
    print("Received these files for visualization: ", filenames)
    data = []
    for filename in filenames:
        rows = FxData.query.filter_by(filename=filename).all()
        print("Data for file {}: {}".format(filename, rows))
        for row in rows:
            data.append({
                'username': row.username,
                'filename': row.filename,
                'name': row.name,
                'date': row.date.strftime("%Y-%m-%d"),
                'shouru': row.shouru,
                'zhichu': row.zhichu,
                'yue': row.yue
            })
    df = pd.DataFrame(data)
    session['df'] = df.to_dict()  # 将DataFrame转化为字典存储在session中
    return redirect(url_for('txzs.txzs_view')) # 重定向到图形分析页面



if __name__ == '__main__':
    app.run(debug=True)
