import os

class Config:
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:'ChaitanyA@23'@localhost/<DB_NAME>"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.urandom(24)