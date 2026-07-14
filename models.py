"""
SQLAlchemy database models for Fitness Buddy AI
"""
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    profile       = db.relationship("FitnessProfile", back_populates="user",
                                    uselist=False, cascade="all, delete-orphan")
    chat_messages = db.relationship("ChatMessage",    back_populates="user",
                                    cascade="all, delete-orphan")
    workouts      = db.relationship("WorkoutPlan",    back_populates="user",
                                    cascade="all, delete-orphan")
    goals         = db.relationship("FitnessGoal",    back_populates="user",
                                    cascade="all, delete-orphan")
    nutrition_logs = db.relationship("NutritionLog",  back_populates="user",
                                     cascade="all, delete-orphan")
    progress_logs  = db.relationship("ProgressLog",   back_populates="user",
                                     cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


class FitnessProfile(db.Model):
    __tablename__ = "fitness_profiles"

    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    age             = db.Column(db.Integer)
    gender          = db.Column(db.String(20))
    height_cm       = db.Column(db.Float)
    weight_kg       = db.Column(db.Float)
    fitness_level   = db.Column(db.String(20))   # beginner / intermediate / advanced
    activity_level  = db.Column(db.String(30))   # sedentary / lightly_active / moderately_active / very_active / extra_active
    primary_goal    = db.Column(db.String(50))   # weight_loss / muscle_gain / endurance / flexibility / general_fitness
    diet_preference = db.Column(db.String(30))   # vegetarian / vegan / non_vegetarian / eggetarian / jain
    health_conditions = db.Column(db.Text, default="")
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="profile")

    @property
    def bmi(self):
        if self.height_cm and self.weight_kg:
            h = self.height_cm / 100
            return round(self.weight_kg / (h * h), 1)
        return None

    @property
    def bmi_category(self):
        b = self.bmi
        if b is None:
            return "Unknown"
        if b < 18.5:
            return "Underweight"
        if b < 25.0:
            return "Normal"
        if b < 30.0:
            return "Overweight"
        return "Obese"

    @property
    def tdee(self):
        """Total Daily Energy Expenditure (Mifflin-St Jeor)"""
        if not all([self.age, self.gender, self.height_cm, self.weight_kg]):
            return None
        if self.gender == "male":
            bmr = 10 * self.weight_kg + 6.25 * self.height_cm - 5 * self.age + 5
        else:
            bmr = 10 * self.weight_kg + 6.25 * self.height_cm - 5 * self.age - 161
        multipliers = {
            "sedentary": 1.2,
            "lightly_active": 1.375,
            "moderately_active": 1.55,
            "very_active": 1.725,
            "extra_active": 1.9,
        }
        m = multipliers.get(self.activity_level, 1.2)
        return round(bmr * m)

    def to_dict(self):
        return {
            "age": self.age,
            "gender": self.gender,
            "height_cm": self.height_cm,
            "weight_kg": self.weight_kg,
            "fitness_level": self.fitness_level,
            "activity_level": self.activity_level,
            "primary_goal": self.primary_goal,
            "diet_preference": self.diet_preference,
            "health_conditions": self.health_conditions,
            "bmi": self.bmi,
            "bmi_category": self.bmi_category,
            "tdee": self.tdee,
        }


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role       = db.Column(db.String(10), nullable=False)   # user / assistant
    content    = db.Column(db.Text, nullable=False)
    timestamp  = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="chat_messages")


class WorkoutPlan(db.Model):
    __tablename__ = "workout_plans"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title       = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    plan_type   = db.Column(db.String(30))    # strength / cardio / yoga / hiit / flexibility
    duration_weeks = db.Column(db.Integer, default=4)
    days_per_week  = db.Column(db.Integer, default=3)
    content     = db.Column(db.Text)          # JSON-encoded workout days
    is_active   = db.Column(db.Boolean, default=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="workouts")


class FitnessGoal(db.Model):
    __tablename__ = "fitness_goals"

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title        = db.Column(db.String(120), nullable=False)
    goal_type    = db.Column(db.String(30))   # weight / strength / cardio / habit / nutrition
    target_value = db.Column(db.Float)
    current_value = db.Column(db.Float, default=0)
    unit         = db.Column(db.String(20))
    deadline     = db.Column(db.Date)
    is_completed = db.Column(db.Boolean, default=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="goals")

    @property
    def progress_pct(self):
        if self.target_value and self.target_value != 0:
            return min(round((self.current_value / self.target_value) * 100), 100)
        return 0

    @property
    def days_remaining(self):
        if self.deadline:
            delta = self.deadline - date.today()
            return delta.days
        return None


class NutritionLog(db.Model):
    __tablename__ = "nutrition_logs"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    log_date    = db.Column(db.Date, default=date.today)
    meal_type   = db.Column(db.String(20))   # breakfast / lunch / dinner / snack
    food_items  = db.Column(db.Text)
    calories    = db.Column(db.Integer)
    protein_g   = db.Column(db.Float)
    carbs_g     = db.Column(db.Float)
    fat_g       = db.Column(db.Float)
    notes       = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="nutrition_logs")


class ProgressLog(db.Model):
    __tablename__ = "progress_logs"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    log_date   = db.Column(db.Date, default=date.today)
    weight_kg  = db.Column(db.Float)
    body_fat_pct = db.Column(db.Float)
    notes      = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="progress_logs")
