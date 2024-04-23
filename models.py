from enum import Enum
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum
from sqlalchemy.orm import relationship
          
db = SQLAlchemy()

class UserRole(Enum):
    USER = 'user'
    ADMIN = 'admin'
          
class Users(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    name = db.Column(db.String(150), index=True, unique=True)
    email = db.Column(db.String(150), index=True, unique=True)
    password = db.Column(db.String(255), index=True, unique=True)
    role = db.Column(db.String(10), default='user')
    
class Books(db.Model):
    __tablename__ = "tblbook"
    bookid = db.Column(db.Integer, primary_key=True,unique=True)
    name = db.Column(db.String(150), index=True, unique=True)
    picture = db.Column(db.String(150), index=True, unique=True)
    isbn = db.Column(db.String(255), index=True, unique=True)
    available_tickets = db.Column(db.Integer, default=11)  