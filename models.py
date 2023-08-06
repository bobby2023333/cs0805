from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, Float, Date
from sqlalchemy.types import TypeDecorator, Date
from extensions  import db



from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


from werkzeug.security import generate_password_hash, check_password_hash



# models.py
from extensions import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    organization = db.Column(db.String(100))
    phone_number = db.Column(db.String(100))  # 我们将phone_number字段更名为phone
    is_admin = db.Column(db.Boolean, default=False)
    uploads = db.relationship('UserUpload', backref='user', lazy='dynamic', foreign_keys='UserUpload.user_id')




class MergedData(db.Model):
    __tablename__ = 'merged_data'
    __table_args__ = {'extend_existing': True}

    # Rest of the model definition
    # ...



    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', backref=db.backref('merged_data', lazy=True))
    filename = db.Column(db.String(255))
    merge_id = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, user_id, filename, merge_id, data):
        self.user_id = user_id
        self.filename = filename
        self.merge_id = merge_id
        self.timestamp = datetime.utcnow()

        # Dynamically add columns based on the keys of the data dictionary
        for column_name in data.keys():
            column = db.Column(db.String(255))
            setattr(self.__class__, column_name, column)
            setattr(self, column_name, data[column_name])


class UserCSVData(db.Model):
    __tablename__ = 'user_csv_data'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    filename = Column(String, nullable=False)
    name = Column(String, nullable=True)
    date = Column(Date, nullable=True)
    shouru = Column(Float, nullable=True)
    zhichu = Column(Float, nullable=True)
    yue = Column(Float, nullable=True)

class CustomDate(TypeDecorator):
    impl = Date


class FxData(db.Model):
    __tablename__ = 'fxdata'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=True)
    date = db.Column(CustomDate, nullable=True)
    shouru = db.Column(db.Float, nullable=True)
    zhichu = db.Column(db.Float, nullable=True)
    yue = db.Column(db.Float, nullable=True)

class UserUpload(db.Model):
    __tablename__ = 'user_uploads'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', use_alter=True))
    name = db.Column(db.String(255))    # assuming name is a string
    date = db.Column(db.Integer)        # assuming date is an integer, modify the type as per your requirements
    shouru = db.Column(db.Integer)      # assuming shouru is an integer, modify the type as per your requirements
    zhichu = db.Column(db.Integer)      # assuming zhichu is an integer, modify the type as per your requirements
    yue = db.Column(db.Integer)         # assuming yue is an integer, modify the type as per your requirements
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    filepath = db.Column(db.String(255))  # Old field
    filename = db.Column(db.String(255))  # New field