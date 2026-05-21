# =========================================
# IMPORTS
# =========================================

import os

from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    flash
)

from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

# =========================================
# IMPORT DATABASE MODELS
# =========================================

from models import (
    db,
    bcrypt,
    User,
    Task
)

# =========================================
# CREATE APP
# =========================================

app = Flask(__name__)

# =========================================
# SECRET KEY
# =========================================

app.config['SECRET_KEY'] = 'secureops_secret_key'

# =========================================
# DATABASE CONFIG
# =========================================

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@database:5432/secureops"
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# =========================================
# INITIALIZE DATABASE
# =========================================

db.init_app(app)

bcrypt.init_app(app)

# =========================================
# LOGIN MANAGER
# =========================================

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"

login_manager.login_message_category = "info"

# =========================================
# USER LOADER
# =========================================

@login_manager.user_loader
def load_user(user_id):

    return User.query.get(int(user_id))

# =========================================
# HOME
# =========================================

@app.route("/")
def home():

    return redirect(
        url_for("login")
    )

# =========================================
# REGISTER
# =========================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        username = request.form.get("username")

        email = request.form.get("email")

        password = request.form.get("password")

        role = request.form.get(
            "role",
            "DevOps Engineer"
        )

        # CHECK EXISTING EMAIL

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash(
                "Email already exists",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        # HASH PASSWORD

        hashed_password = generate_password_hash(
            password
        )

        # CREATE USER

        new_user = User(

            username=username,

            email=email,

            password=hashed_password,

            role=role
        )

        db.session.add(new_user)

        db.session.commit()

        flash(
            "Account Created Successfully",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )

# =========================================
# LOGIN
# =========================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        email = request.form.get("email")

        password = request.form.get("password")

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            login_user(user)

            flash(
                "Login Successful",
                "success"
            )

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid Email or Password",
            "danger"
        )

    return render_template(
        "login.html"
    )

# =========================================
# DASHBOARD
# =========================================

@app.route("/dashboard")
@login_required
def dashboard():

    total_tasks = Task.query.filter_by(
        user_id=current_user.id
    ).count()

    completed_tasks = Task.query.filter_by(
        user_id=current_user.id,
        status="Completed"
    ).count()

    pending_tasks = Task.query.filter_by(
        user_id=current_user.id,
        status="Pending"
    ).count()

    progress_tasks = Task.query.filter_by(
        user_id=current_user.id,
        status="In Progress"
    ).count()

    recent_tasks = Task.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Task.created_at.desc()
    ).limit(5).all()

    return render_template(

        "dashboard.html",

        user=current_user,

        total_tasks=total_tasks,

        completed_tasks=completed_tasks,

        pending_tasks=pending_tasks,

        progress_tasks=progress_tasks,

        recent_tasks=recent_tasks
    )

# =========================================
# PROJECTS
# =========================================

@app.route("/projects")
@login_required
def projects():

    return render_template(

        "projects.html",

        user=current_user
    )

# =========================================
# TASKS
# =========================================

@app.route("/tasks", methods=["GET", "POST"])
@login_required
def tasks():

    if request.method == "POST":

        title = request.form.get("title")

        description = request.form.get(
            "description"
        )

        status = request.form.get(
            "status",
            "Pending"
        )

        priority = request.form.get(
            "priority",
            "Medium"
        )

        if not title or not description:

            flash(
                "Please fill all fields",
                "danger"
            )

            return redirect(
                url_for("tasks")
            )

        # CREATE TASK

        new_task = Task(

            title=title,

            description=description,

            status=status,

            priority=priority,

            user_id=current_user.id
        )

        db.session.add(new_task)

        db.session.commit()

        flash(
            "Task Added Successfully",
            "success"
        )

        return redirect(
            url_for("tasks")
        )

    all_tasks = Task.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Task.created_at.desc()
    ).all()

    return render_template(

        "tasks.html",

        tasks=all_tasks,

        user=current_user
    )

# =========================================
# DELETE TASK
# =========================================

@app.route("/delete_task/<int:id>")
@login_required
def delete_task(id):

    task = Task.query.get_or_404(id)

    if task.user_id != current_user.id:

        flash(
            "Unauthorized Action",
            "danger"
        )

        return redirect(
            url_for("tasks")
        )

    db.session.delete(task)

    db.session.commit()

    flash(
        "Task Deleted Successfully",
        "success"
    )

    return redirect(
        url_for("tasks")
    )

# =========================================
# ANALYTICS
# =========================================

@app.route("/analytics")
@login_required
def analytics():

    total_tasks = Task.query.filter_by(
        user_id=current_user.id
    ).count()

    completed_tasks = Task.query.filter_by(
        user_id=current_user.id,
        status="Completed"
    ).count()

    pending_tasks = Task.query.filter_by(
        user_id=current_user.id,
        status="Pending"
    ).count()

    progress_tasks = Task.query.filter_by(
        user_id=current_user.id,
        status="In Progress"
    ).count()

    return render_template(

        "analytics.html",

        user=current_user,

        total_tasks=total_tasks,

        completed_tasks=completed_tasks,

        pending_tasks=pending_tasks,

        progress_tasks=progress_tasks
    )

# =========================================
# PROFILE
# =========================================

@app.route("/profile")
@login_required
def profile():

    total_tasks = Task.query.filter_by(
        user_id=current_user.id
    ).count()

    return render_template(

        "profile.html",

        user=current_user,

        total_tasks=total_tasks
    )

# =========================================
# LOGOUT
# =========================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "Logged Out Successfully",
        "info"
    )

    return redirect(
        url_for("login")
    )

# =========================================
# CREATE DATABASE
# =========================================

with app.app_context():

    db.create_all()

# =========================================
# RUN APP
# =========================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True
    )