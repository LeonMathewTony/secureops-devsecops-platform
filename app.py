# =========================================
# IMPORTS
# =========================================

import os
from datetime import datetime
from functools import wraps

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

from models import (
    db,
    bcrypt,
    User,
    Task,
    Project
)

# =========================================
# CREATE FLASK APP
# =========================================

app = Flask(__name__)

# =========================================
# SECRET KEY
# =========================================

app.config["SECRET_KEY"] = "secureops_enterprise_secret"

# =========================================
# DATABASE CONFIG
# =========================================

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@db:5432/secureopsdb"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

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
# SECURITY HEADERS
# =========================================

@app.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com https://fonts.googleapis.com https://fonts.gstatic.com"
    return response

# =========================================
# ROLE DECORATORS — RBAC
# =========================================

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != "Admin":
            flash("Access denied.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function

def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                flash("Access denied.", "danger")
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

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
    return redirect(url_for("login"))

# =========================================
# REGISTER
# =========================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        username = request.form.get("username")
        name     = request.form.get("username")
        email    = request.form.get("email")
        password = request.form.get("password")

        existing_user = User.query.filter(
            (User.email == email) | (User.username == username)
        ).first()

        if existing_user:
            flash("Email or username already exists.", "danger")
            return render_template("register.html", error="Email or username already exists.")

        new_user = User(username=username, name=name, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# =========================================
# LOGIN
# =========================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        email    = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):

            if not user.is_active_user:
                return render_template("login.html", error="Your account has been disabled.")

            user.last_login = datetime.utcnow()
            db.session.commit()

            login_user(user)
            flash("Login successful.", "success")
            return redirect(url_for("dashboard"))

        else:
            return render_template("login.html", error="Invalid email or password.")

    return render_template("login.html")

# =========================================
# FORGOT PASSWORD
# =========================================

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":
        return render_template(
            "forgot_password.html",
            success="If that email exists, a reset link has been sent."
        )

    return render_template("forgot_password.html")

# =========================================
# DASHBOARD
# =========================================

@app.route("/dashboard")
@login_required
def dashboard():

    if current_user.role == "Admin":
        total_tasks     = Task.query.count()
        completed_tasks = Task.query.filter_by(status="Completed").count()
        pending_tasks   = Task.query.filter_by(status="Pending").count()
        progress_tasks  = Task.query.filter_by(status="In Progress").count()
        recent_tasks    = Task.query.order_by(Task.created_at.desc()).limit(5).all()
    else:
        total_tasks     = Task.query.filter(
            (Task.user_id == current_user.id) | (Task.is_global == True)
        ).count()
        completed_tasks = Task.query.filter(
            ((Task.user_id == current_user.id) | (Task.is_global == True)),
            Task.status == "Completed"
        ).count()
        pending_tasks   = Task.query.filter(
            ((Task.user_id == current_user.id) | (Task.is_global == True)),
            Task.status == "Pending"
        ).count()
        progress_tasks  = Task.query.filter(
            ((Task.user_id == current_user.id) | (Task.is_global == True)),
            Task.status == "In Progress"
        ).count()
        recent_tasks    = Task.query.filter(
            (Task.user_id == current_user.id) | (Task.is_global == True)
        ).order_by(Task.created_at.desc()).limit(5).all()

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

@app.route("/projects", methods=["GET", "POST"])
@login_required
def projects():

    if request.method == "POST":

        name        = request.form.get("name")
        description = request.form.get("description")
        status      = request.form.get("status", "Active")
        priority    = request.form.get("priority", "Medium")
        technology  = request.form.get("technology", "")

        if not name or not description:
            flash("Please fill all required fields.", "danger")
            return redirect(url_for("projects"))

        new_project = Project(
            name=name,
            description=description,
            status=status,
            priority=priority,
            technology=technology,
            user_id=current_user.id
        )

        db.session.add(new_project)
        db.session.commit()

        flash("Project created successfully.", "success")
        return redirect(url_for("projects"))

    if current_user.role == "Admin":
        all_projects = Project.query.order_by(Project.created_at.desc()).all()
    else:
        all_projects = Project.query.filter_by(
            user_id=current_user.id
        ).order_by(Project.created_at.desc()).all()

    return render_template("projects.html", user=current_user, projects=all_projects)

# =========================================
# DELETE PROJECT
# =========================================

@app.route("/delete_project/<int:id>")
@login_required
def delete_project(id):

    project = Project.query.get_or_404(id)

    if project.user_id != current_user.id and current_user.role != "Admin":
        flash("Unauthorized action.", "danger")
        return redirect(url_for("projects"))

    db.session.delete(project)
    db.session.commit()

    flash("Project deleted successfully.", "success")
    return redirect(url_for("projects"))

# =========================================
# TASKS
# =========================================

@app.route("/tasks", methods=["GET", "POST"])
@login_required
def tasks():

    if request.method == "POST":

        title       = request.form.get("title")
        description = request.form.get("description")
        status      = request.form.get("status", "Pending")
        priority    = request.form.get("priority", "Medium")

        if not title or not description:
            flash("Please fill all required fields.", "danger")
            return redirect(url_for("tasks"))

        # Admin tasks are global — visible to all employees
        is_global = current_user.role == "Admin"

        new_task = Task(
            title=title,
            description=description,
            status=status,
            priority=priority,
            user_id=current_user.id,
            is_global=is_global
        )

        db.session.add(new_task)
        db.session.commit()

        flash("Task created successfully.", "success")
        return redirect(url_for("tasks"))

    # Admin sees all tasks, others see own + global tasks
    if current_user.role == "Admin":
        all_tasks = Task.query.order_by(Task.created_at.desc()).all()
    else:
        all_tasks = Task.query.filter(
            (Task.user_id == current_user.id) | (Task.is_global == True)
        ).order_by(Task.created_at.desc()).all()

    return render_template("tasks.html", tasks=all_tasks, user=current_user)

# =========================================
# EDIT TASK
# =========================================

@app.route("/edit_task/<int:id>", methods=["GET", "POST"])
@login_required
def edit_task(id):

    task = Task.query.get_or_404(id)

    if task.user_id != current_user.id and current_user.role != "Admin":
        flash("Unauthorized action.", "danger")
        return redirect(url_for("tasks"))

    if request.method == "POST":

        task.title       = request.form.get("title")
        task.description = request.form.get("description")
        task.status      = request.form.get("status", task.status)
        task.priority    = request.form.get("priority", task.priority)

        db.session.commit()

        flash("Task updated successfully.", "success")
        return redirect(url_for("tasks"))

    return render_template("edit_task.html", task=task, user=current_user)

# =========================================
# DELETE TASK
# =========================================

@app.route("/delete_task/<int:id>")
@login_required
def delete_task(id):

    task = Task.query.get_or_404(id)

    if task.user_id != current_user.id and current_user.role != "Admin":
        flash("Unauthorized action.", "danger")
        return redirect(url_for("tasks"))

    db.session.delete(task)
    db.session.commit()

    flash("Task deleted successfully.", "success")
    return redirect(url_for("tasks"))

# =========================================
# ANALYTICS
# =========================================

@app.route("/analytics")
@login_required
@roles_required("Admin", "Security Analyst", "DevOps Engineer", "Cloud Engineer")
def analytics():

    if current_user.role == "Admin":
        total_tasks     = Task.query.count()
        completed_tasks = Task.query.filter_by(status="Completed").count()
        pending_tasks   = Task.query.filter_by(status="Pending").count()
        progress_tasks  = Task.query.filter_by(status="In Progress").count()
    else:
        total_tasks     = Task.query.filter(
            (Task.user_id == current_user.id) | (Task.is_global == True)
        ).count()
        completed_tasks = Task.query.filter(
            ((Task.user_id == current_user.id) | (Task.is_global == True)),
            Task.status == "Completed"
        ).count()
        pending_tasks   = Task.query.filter(
            ((Task.user_id == current_user.id) | (Task.is_global == True)),
            Task.status == "Pending"
        ).count()
        progress_tasks  = Task.query.filter(
            ((Task.user_id == current_user.id) | (Task.is_global == True)),
            Task.status == "In Progress"
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

    total_tasks = Task.query.filter_by(user_id=current_user.id).count()

    return render_template("profile.html", user=current_user, total_tasks=total_tasks)

# =========================================
# ADMIN USERS
# =========================================

@app.route("/admin/users", methods=["GET", "POST"])
@login_required
@admin_required
def admin_users():

    if request.method == "POST":

        username   = request.form.get("username")
        name       = request.form.get("name")
        email      = request.form.get("email")
        password   = request.form.get("password")
        role       = request.form.get("role", "DevOps Engineer")
        department = request.form.get("department", "Infrastructure")

        existing = User.query.filter(
            (User.email == email) | (User.username == username)
        ).first()

        if existing:
            flash("Email or username already exists.", "danger")
        else:
            new_user = User(
                username=username,
                name=name,
                email=email,
                role=role,
                department=department
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash(f"{name} created successfully.", "success")

    users = User.query.order_by(User.created_at.desc()).all()

    return render_template("admin_users.html", users=users, user=current_user)

# =========================================
# DELETE USER
# =========================================

@app.route("/delete-user/<int:user_id>")
@login_required
@admin_required
def delete_user(user_id):

    employee = User.query.get_or_404(user_id)

    if employee.id == current_user.id:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("admin_users"))

    db.session.delete(employee)
    db.session.commit()

    flash("Employee deleted successfully.", "success")
    return redirect(url_for("admin_users"))

# =========================================
# DISABLE USER
# =========================================

@app.route("/disable-user/<int:user_id>")
@login_required
@admin_required
def disable_user(user_id):

    employee = User.query.get_or_404(user_id)

    if employee.id == current_user.id:
        flash("You cannot disable your own account.", "danger")
        return redirect(url_for("admin_users"))

    employee.is_active_user = False
    db.session.commit()

    flash(f"{employee.name} disabled successfully.", "warning")
    return redirect(url_for("admin_users"))

# =========================================
# ENABLE USER
# =========================================

@app.route("/enable-user/<int:user_id>")
@login_required
@admin_required
def enable_user(user_id):

    employee = User.query.get_or_404(user_id)
    employee.is_active_user = True
    db.session.commit()

    flash(f"{employee.name} enabled successfully.", "success")
    return redirect(url_for("admin_users"))

# =========================================
# EDIT USER
# =========================================

@app.route("/edit-user/<int:user_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_user(user_id):

    employee = User.query.get_or_404(user_id)

    if request.method == "POST":

        employee.username   = request.form.get("username")
        employee.name       = request.form.get("name")
        employee.email      = request.form.get("email")
        employee.role       = request.form.get("role")
        employee.department = request.form.get("department")

        db.session.commit()

        flash("Employee updated successfully.", "success")
        return redirect(url_for("admin_users"))

    return render_template("edit_user.html", employee=employee, user=current_user)

# =========================================
# LOGOUT
# =========================================

@app.route("/logout")
@login_required
def logout():

    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

# =========================================
# CREATE DATABASE TABLES
# =========================================

with app.app_context():
    db.create_all()

# =========================================
# RUN APPLICATION
# =========================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )