"""
Fitness Buddy AI — Flask Application Entry Point
IBM watsonx.ai + Granite powered fitness coaching web app
"""
import os
import json
import logging
from datetime import datetime, date, timedelta
from functools import wraps

from dotenv import load_dotenv
load_dotenv()

from flask import (
    Flask, render_template, request, jsonify,
    redirect, url_for, flash, session,
)
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user,
)
from flask_wtf.csrf import CSRFProtect

from models import db, User, FitnessProfile, ChatMessage, WorkoutPlan, FitnessGoal, NutritionLog, ProgressLog
from watsonx_client import watsonx
from agent import FitnessAgent
from knowledge_base import get_quick_tips

# ─── App Initialisation ───────────────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"]            = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

# Build absolute DB path so SQLite works regardless of cwd
_db_url = os.getenv("DATABASE_URL", "sqlite:///instance/fitness_buddy.db")
if _db_url.startswith("sqlite:///") and not _db_url.startswith("sqlite:////"):
    _rel = _db_url[len("sqlite:///"):]
    _abs = os.path.join(os.path.dirname(os.path.abspath(__file__)), _rel)
    _db_url = "sqlite:///" + _abs.replace("\\", "/")
app.config["SQLALCHEMY_DATABASE_URI"] = _db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["WTF_CSRF_TIME_LIMIT"]   = None

db.init_app(app)
csrf    = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view  = "login"
login_manager.login_message = "Please log in to access your Fitness Buddy."
login_manager.login_message_category = "info"

agent   = FitnessAgent(watsonx)
logging.basicConfig(level=logging.INFO)
logger  = logging.getLogger(__name__)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ─── Context Processor ───────────────────────────────────────────────────────
@app.context_processor
def inject_globals():
    tips = get_quick_tips()
    import random
    return {
        "app_name":    os.getenv("APP_NAME", "Fitness Buddy AI"),
        "daily_tip":   random.choice(tips),
        "watsonx_ready": watsonx.is_ready,
    }


# ─── Helpers ─────────────────────────────────────────────────────────────────
def get_user_profile_dict(user: User):
    if user.profile:
        return user.profile.to_dict()
    return {}


def get_chat_history(user_id: int, limit: int = 20):
    msgs = (
        ChatMessage.query
        .filter_by(user_id=user_id)
        .order_by(ChatMessage.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [{"role": m.role, "content": m.content} for m in reversed(msgs)]


# ─── Auth Routes ─────────────────────────────────────────────────────────────
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email    = request.form.get("email",    "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")
        errors   = []
        if len(username) < 3:
            errors.append("Username must be at least 3 characters.")
        if "@" not in email:
            errors.append("Enter a valid email address.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if User.query.filter_by(username=username).first():
            errors.append("Username already taken.")
        if User.query.filter_by(email=email).first():
            errors.append("Email already registered.")
        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("register.html", username=username, email=email)
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        profile = FitnessProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
        login_user(user)
        flash(f"Welcome to Fitness Buddy, {username}! Let's set up your profile.", "success")
        return redirect(url_for("profile"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password   = request.form.get("password",   "")
        remember   = request.form.get("remember") == "on"
        user = (
            User.query.filter_by(username=identifier).first()
            or User.query.filter_by(email=identifier.lower()).first()
        )
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get("next")
            flash(f"Welcome back, {user.username}! 💪", "success")
            return redirect(next_page or url_for("dashboard"))
        flash("Invalid username/email or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out. Stay fit! 🏃", "info")
    return redirect(url_for("index"))


# ─── Dashboard ────────────────────────────────────────────────────────────────
@app.route("/dashboard")
@login_required
def dashboard():
    profile   = current_user.profile
    goals     = FitnessGoal.query.filter_by(user_id=current_user.id, is_completed=False).all()
    today     = date.today()
    week_ago  = today - timedelta(days=7)
    # Progress data for chart (last 30 days)
    progress  = (
        ProgressLog.query
        .filter(ProgressLog.user_id == current_user.id,
                ProgressLog.log_date >= today - timedelta(days=30))
        .order_by(ProgressLog.log_date)
        .all()
    )
    # Nutrition summary today
    nutrition_today = (
        NutritionLog.query
        .filter_by(user_id=current_user.id, log_date=today)
        .all()
    )
    total_cal = sum(n.calories or 0 for n in nutrition_today)
    total_pro = sum(n.protein_g or 0 for n in nutrition_today)
    # Chart data
    weight_dates  = [p.log_date.strftime("%b %d") for p in progress]
    weight_values = [p.weight_kg for p in progress]
    # Stats
    stats = {
        "total_goals":     FitnessGoal.query.filter_by(user_id=current_user.id).count(),
        "completed_goals": FitnessGoal.query.filter_by(user_id=current_user.id, is_completed=True).count(),
        "active_workouts": WorkoutPlan.query.filter_by(user_id=current_user.id, is_active=True).count(),
        "chat_messages":   ChatMessage.query.filter_by(user_id=current_user.id).count(),
    }
    return render_template(
        "dashboard.html",
        profile=profile,
        goals=goals,
        stats=stats,
        total_cal=total_cal,
        total_pro=round(total_pro, 1),
        weight_dates=json.dumps(weight_dates),
        weight_values=json.dumps(weight_values),
    )


# ─── Profile ─────────────────────────────────────────────────────────────────
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    p = current_user.profile or FitnessProfile(user_id=current_user.id)
    if request.method == "POST":
        p.age              = int(request.form.get("age") or 0) or None
        p.gender           = request.form.get("gender")
        p.height_cm        = float(request.form.get("height_cm") or 0) or None
        p.weight_kg        = float(request.form.get("weight_kg") or 0) or None
        p.fitness_level    = request.form.get("fitness_level")
        p.activity_level   = request.form.get("activity_level")
        p.primary_goal     = request.form.get("primary_goal")
        p.diet_preference  = request.form.get("diet_preference")
        p.health_conditions = request.form.get("health_conditions", "")
        p.updated_at       = datetime.utcnow()
        if not current_user.profile:
            db.session.add(p)
        db.session.commit()
        flash("Profile updated successfully! 🎯", "success")
        return redirect(url_for("dashboard"))
    return render_template("profile.html", profile=p)


# ─── AI Chatbot ──────────────────────────────────────────────────────────────
@app.route("/chat")
@login_required
def chat():
    messages = (
        ChatMessage.query
        .filter_by(user_id=current_user.id)
        .order_by(ChatMessage.timestamp)
        .limit(50)
        .all()
    )
    return render_template("chat.html", messages=messages)


@app.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    data    = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400
    # Save user message
    user_msg = ChatMessage(user_id=current_user.id, role="user", content=message)
    db.session.add(user_msg)
    db.session.flush()
    # Get AI response
    profile     = get_user_profile_dict(current_user)
    history     = get_chat_history(current_user.id)
    ai_response = agent.chat(message, profile, history)
    # Save assistant message
    ai_msg = ChatMessage(user_id=current_user.id, role="assistant", content=ai_response)
    db.session.add(ai_msg)
    db.session.commit()
    return jsonify({
        "response":  ai_response,
        "timestamp": datetime.utcnow().strftime("%I:%M %p"),
        "model":     os.getenv("GRANITE_MODEL_ID", "ibm/granite-3-8b-instruct"),
    })


@app.route("/api/chat/stream", methods=["POST"])
@login_required
def api_chat_stream():
    """Server-Sent Events endpoint — streams reply tokens as they arrive."""
    from flask import Response, stream_with_context
    import json as _json

    data    = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400

    # Persist user message immediately
    user_msg = ChatMessage(user_id=current_user.id, role="user", content=message)
    db.session.add(user_msg)
    db.session.commit()

    profile = get_user_profile_dict(current_user)
    history = get_chat_history(current_user.id)

    # Build messages list via agent (same context as non-streaming)
    from knowledge_base import build_rag_context
    rag_ctx  = build_rag_context(message, profile)
    messages = agent._build_messages(message, profile, history, rag_ctx)

    # Capture full text so we can persist after streaming
    full_text_holder = []
    user_id = current_user.id

    def generate():
        accumulated = []
        try:
            for chunk in watsonx.stream(messages):
                accumulated.append(chunk)
                yield f"data: {_json.dumps({'token': chunk})}\n\n"
        finally:
            full_reply = "".join(accumulated)
            if full_reply:
                with app.app_context():
                    ai_msg = ChatMessage(
                        user_id=user_id,
                        role="assistant",
                        content=full_reply,
                    )
                    db.session.add(ai_msg)
                    db.session.commit()
            yield f"data: {_json.dumps({'done': True, 'timestamp': datetime.utcnow().strftime('%I:%M %p')})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/api/chat/clear", methods=["POST"])
@login_required
def clear_chat():
    ChatMessage.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({"status": "cleared"})


@app.route("/api/motivate", methods=["GET"])
@login_required
def api_motivate():
    profile  = get_user_profile_dict(current_user)
    msg      = agent.get_motivation(profile)
    return jsonify({"motivation": msg})


# ─── Workout Planner ─────────────────────────────────────────────────────────
@app.route("/workout")
@login_required
def workout():
    plans = WorkoutPlan.query.filter_by(user_id=current_user.id).order_by(WorkoutPlan.created_at.desc()).all()
    return render_template("workout.html", plans=plans, profile=current_user.profile)


@app.route("/api/workout/generate", methods=["POST"])
@login_required
def api_generate_workout():
    profile = get_user_profile_dict(current_user)
    if not profile:
        return jsonify({"error": "Please complete your fitness profile first."}), 400
    plan_content = agent.generate_workout_plan(profile)
    level = profile.get("fitness_level", "beginner")
    days  = {"beginner": 3, "intermediate": 4, "advanced": 5}.get(level, 3)
    plan  = WorkoutPlan(
        user_id=current_user.id,
        title=f"AI Workout Plan — {datetime.now().strftime('%b %Y')}",
        plan_type="mixed",
        duration_weeks=4,
        days_per_week=days,
        content=plan_content,
    )
    db.session.add(plan)
    db.session.commit()
    return jsonify({"plan": plan_content, "plan_id": plan.id})


@app.route("/api/workout/<int:plan_id>/delete", methods=["POST"])
@login_required
def delete_workout(plan_id):
    plan = WorkoutPlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    db.session.delete(plan)
    db.session.commit()
    return jsonify({"status": "deleted"})


# ─── Nutrition ───────────────────────────────────────────────────────────────
@app.route("/nutrition")
@login_required
def nutrition():
    today = date.today()
    logs  = NutritionLog.query.filter_by(user_id=current_user.id, log_date=today).all()
    recent = (
        NutritionLog.query
        .filter(NutritionLog.user_id == current_user.id)
        .order_by(NutritionLog.created_at.desc())
        .limit(20)
        .all()
    )
    return render_template("nutrition.html",
                           logs=logs, recent=recent, today=today,
                           profile=current_user.profile)


@app.route("/api/nutrition/meal-plan", methods=["POST"])
@login_required
def api_meal_plan():
    profile = get_user_profile_dict(current_user)
    if not profile:
        return jsonify({"error": "Please complete your fitness profile first."}), 400
    meal_plan = agent.generate_meal_plan(profile)
    return jsonify({"meal_plan": meal_plan})


@app.route("/api/nutrition/analyze", methods=["POST"])
@login_required
def api_analyze_calories():
    data  = request.get_json(silent=True) or {}
    food  = (data.get("food_items") or "").strip()
    if not food:
        return jsonify({"error": "Please enter food items."}), 400
    profile  = get_user_profile_dict(current_user)
    analysis = agent.calculate_calories(food, profile)
    return jsonify({"analysis": analysis})


@app.route("/api/nutrition/log", methods=["POST"])
@login_required
def api_log_nutrition():
    data = request.get_json(silent=True) or {}
    log  = NutritionLog(
        user_id   = current_user.id,
        log_date  = date.today(),
        meal_type = data.get("meal_type", "snack"),
        food_items= data.get("food_items", ""),
        calories  = int(data.get("calories") or 0) or None,
        protein_g = float(data.get("protein_g") or 0) or None,
        carbs_g   = float(data.get("carbs_g") or 0) or None,
        fat_g     = float(data.get("fat_g") or 0) or None,
        notes     = data.get("notes", ""),
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({"status": "logged", "id": log.id})


@app.route("/api/nutrition/hydration", methods=["GET"])
@login_required
def api_hydration():
    profile = get_user_profile_dict(current_user)
    tips    = agent.suggest_hydration(profile)
    return jsonify({"tips": tips})


# ─── Goals ───────────────────────────────────────────────────────────────────
@app.route("/goals")
@login_required
def goals():
    all_goals = (
        FitnessGoal.query
        .filter_by(user_id=current_user.id)
        .order_by(FitnessGoal.created_at.desc())
        .all()
    )
    return render_template("goals.html", goals=all_goals)


@app.route("/api/goals/add", methods=["POST"])
@login_required
def api_add_goal():
    data     = request.get_json(silent=True) or {}
    deadline = None
    if data.get("deadline"):
        try:
            deadline = datetime.strptime(data["deadline"], "%Y-%m-%d").date()
        except ValueError:
            pass
    goal = FitnessGoal(
        user_id      = current_user.id,
        title        = data.get("title", "New Goal"),
        goal_type    = data.get("goal_type", "habit"),
        target_value = float(data.get("target_value") or 0) or None,
        current_value= float(data.get("current_value") or 0),
        unit         = data.get("unit", ""),
        deadline     = deadline,
    )
    db.session.add(goal)
    db.session.commit()
    return jsonify({"status": "added", "id": goal.id})


@app.route("/api/goals/<int:goal_id>/update", methods=["POST"])
@login_required
def api_update_goal(goal_id):
    goal = FitnessGoal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    data = request.get_json(silent=True) or {}
    if "current_value" in data:
        goal.current_value = float(data["current_value"])
    if "is_completed" in data:
        goal.is_completed = bool(data["is_completed"])
    db.session.commit()
    return jsonify({"status": "updated", "progress": goal.progress_pct})


@app.route("/api/goals/<int:goal_id>/delete", methods=["POST"])
@login_required
def api_delete_goal(goal_id):
    goal = FitnessGoal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    db.session.delete(goal)
    db.session.commit()
    return jsonify({"status": "deleted"})


# ─── Progress Tracking ────────────────────────────────────────────────────────
@app.route("/api/progress/log", methods=["POST"])
@login_required
def api_log_progress():
    data = request.get_json(silent=True) or {}
    log  = ProgressLog(
        user_id    = current_user.id,
        log_date   = date.today(),
        weight_kg  = float(data.get("weight_kg") or 0) or None,
        body_fat_pct = float(data.get("body_fat_pct") or 0) or None,
        notes      = data.get("notes", ""),
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({"status": "logged", "id": log.id})


@app.route("/api/progress/data", methods=["GET"])
@login_required
def api_progress_data():
    days  = int(request.args.get("days", 30))
    since = date.today() - timedelta(days=days)
    logs  = (
        ProgressLog.query
        .filter(ProgressLog.user_id == current_user.id, ProgressLog.log_date >= since)
        .order_by(ProgressLog.log_date)
        .all()
    )
    return jsonify({
        "dates":  [l.log_date.strftime("%b %d") for l in logs],
        "weight": [l.weight_kg for l in logs],
        "fat":    [l.body_fat_pct for l in logs],
    })


# ─── BMI API ─────────────────────────────────────────────────────────────────
@app.route("/api/bmi/analyze", methods=["POST"])
@login_required
def api_bmi():
    profile = get_user_profile_dict(current_user)
    if not profile.get("bmi"):
        return jsonify({"error": "Please enter your height and weight in your profile."}), 400
    analysis = agent.analyze_bmi(profile)
    return jsonify({"analysis": analysis, "bmi": profile["bmi"], "category": profile["bmi_category"]})


# ─── DB Init & Run ───────────────────────────────────────────────────────────
def create_tables():
    with app.app_context():
        # Ensure the instance folder exists before SQLite tries to open the file
        db_url = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if "sqlite:///" in db_url:
            # Extract path from sqlite:///path/to/file.db
            db_path = db_url.replace("sqlite:///", "")
            if db_path and not db_path.startswith("/") and not (len(db_path) > 1 and db_path[1] == ":"):
                db_path = os.path.join(os.path.dirname(__file__), db_path)
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        os.makedirs("instance", exist_ok=True)
        db.create_all()
        logger.info("Database tables created.")


if __name__ == "__main__":
    create_tables()
    app.run(
        host  = "0.0.0.0",
        port  = int(os.getenv("PORT", 5000)),
        debug = os.getenv("FLASK_DEBUG", "True").lower() == "true",
    )
