from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
from datetime import datetime

# =========================================
# INITIALIZE DATABASE & BCRYPT
# =========================================

db = SQLAlchemy()
bcrypt = Bcrypt()

# =========================================
# USER MODEL
# =========================================

class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True, nullable=False)
    name     = db.Column(db.String(100), nullable=False)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    role           = db.Column(db.String(50),  default="DevOps Engineer")
    department     = db.Column(db.String(100), default="Infrastructure")
    is_active_user = db.Column(db.Boolean,     default=True)
    profile_image  = db.Column(db.String(200), default="default.png")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    tasks    = db.relationship('Task',    backref='user',  lazy=True, cascade="all, delete")
    projects = db.relationship('Project', backref='owner', lazy=True, cascade="all, delete")

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    def is_admin(self):
        return self.role == "Admin"

    def __repr__(self):
        return f"<User {self.username}>"

# =========================================
# TASK MODEL
# =========================================

class Task(db.Model):

    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)

    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text,        nullable=False)
    status      = db.Column(db.String(50),  default="Pending")
    priority    = db.Column(db.String(50),  default="Medium")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deadline   = db.Column(db.DateTime, nullable=True)

    # Admin tasks visible to all employees
    is_global = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f"<Task {self.title}>"

# =========================================
# PROJECT MODEL
# =========================================

class Project(db.Model):

    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)

    name        = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text,        nullable=False)
    status      = db.Column(db.String(50),  default="Active")
    priority    = db.Column(db.String(50),  default="Medium")
    technology  = db.Column(db.String(200), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f"<Project {self.name}>"