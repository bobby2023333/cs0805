from flask import Blueprint, request, redirect, url_for, current_app, send_from_directory, session
from flask import Blueprint, request, redirect, url_for, session, render_template
from flask import flash
import os
from extensions import db
data_cleaning = Blueprint('data_cleaning', __name__)

UPLOAD_FOLDER_CLEAN = 'D:/bank1/clean'

class CleanData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(128), nullable=False)
    data = db.Column(db.Text, nullable=False)  # 这里我们将 CSV 数据保存为文本，这可能并不是最优的选择，具体取决于你的应用场景。



@data_cleaning.route('/')
def data_cleaning_home():
    if 'username' not in session:
        return "You are not logged in!", 401

    username = session['username']
    user_folder_path = os.path.join(current_app.config['CLEAN_FOLDER'], username)

    # Get all files in the user's to-clean folder
    to_clean_files = os.listdir(user_folder_path) if os.path.exists(user_folder_path) else []

    return render_template('data_cleaning.html', to_clean_files=to_clean_files)



@data_cleaning.route('/upload_to_clean', methods=['POST'])
def upload_file_to_clean():
    if 'username' not in session:
        return "You are not logged in!", 401

    if 'file' not in request.files:
        return "No file part", 400

    file = request.files['file']

    if file.filename == '':
        return "No selected file", 400

    if file:
        username = session['username']
        user_folder_path = os.path.join(current_app.config['CLEAN_FOLDER'], username)

        if not os.path.exists(user_folder_path):
            os.makedirs(user_folder_path)

        file.save(os.path.join(user_folder_path, file.filename))
        flash('File successfully uploaded!')  # 新增的 flash 语句

    return redirect(url_for('data_cleaning.data_cleaning_home'))

@data_cleaning.route('/delete_to_clean/<filename>', methods=['POST'])
def delete_to_clean_file(filename):
    if 'username' not in session:
        return "You are not logged in!", 401

    username = session['username']
    user_folder_path = os.path.join(current_app.config['CLEAN_FOLDER'], username)

    # Check if file exists
    file_path = os.path.join(user_folder_path, filename)
    if os.path.exists(file_path):
        # Remove the file
        os.remove(file_path)

    return redirect(url_for('data_cleaning.data_cleaning_home'))



@data_cleaning.route('/store_to_db', methods=['POST'])
def store_to_db():
    if 'username' not in session:
        return "You are not logged in!", 401

    file_id = request.form.get('file_id')

    file = CleanData.query.filter_by(id=file_id).first()
    if not file:
        return "File not found", 404

    file_path = os.path.join(current_app.config['CLEAN_FOLDER'], file.username, file.filename)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:  # 指定编码为'utf-8'
            data = f.read()
    except UnicodeDecodeError:
        flash("Error reading file: Invalid encoding")
        return redirect(url_for('data_cleaning.data_cleaning_home'))

    # ...其他代码...

    if not os.path.exists(file_path):
        return "File not found", 404

    with open(file_path, 'r') as f:
        data = f.read()

    clean_data = CleanData(filename=filename, data=data)
    db.session.add(clean_data)
    db.session.commit()

    flash('File successfully stored to database!')  # 新增的 flash 语句

    return redirect(url_for('data_cleaning.data_cleaning_home'))
