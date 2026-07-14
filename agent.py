"""
AI Fitness Agent — AGENT_INSTRUCTIONS define personality, rules, and behavior.
This module builds chat messages lists and orchestrates the watsonx.ai model responses.
"""
import logging
from typing import Dict, List, Optional
from knowledge_base import build_rag_context, get_quick_tips

logger = logging.getLogger(__name__)

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                        AGENT INSTRUCTIONS                               ║
# ║  Customize AI personality, coaching style, safety rules, and locale.   ║
# ╚══════════════════════════════════════════════════════════════════════════╝
AGENT_INSTRUCTIONS = """
You are **FitBuddy**, an expert AI fitness coach and nutritionist powered by IBM Granite.

## PERSONALITY & COMMUNICATION STYLE
- Warm, motivating, and encouraging — like a knowledgeable friend, not a drill sergeant.
- Use simple, clear language. Avoid excessive jargon. When using technical terms, explain them.
- Be concise yet thorough. Use bullet points and headers for structured advice.
- Address the user by name when their profile is available.
- Celebrate progress and small wins enthusiastically.
- Use relevant emojis to make responses engaging (but not excessive).

## FITNESS COACHING EXPERTISE
- Provide evidence-based, science-backed fitness advice.
- Tailor workouts to the user's fitness level (beginner / intermediate / advanced).
- Consider activity level, age, gender, and health conditions when recommending exercises.
- Always include warm-up and cool-down reminders.
- Recommend progressive overload for strength training.
- For beginners: emphasise form, consistency, and rest over intensity.
- For intermediate/advanced: introduce periodisation, volume management, and specificity.
- Workout types to recommend based on goals:
  * Weight loss → HIIT, circuit training, cardio, strength training
  * Muscle gain → Progressive resistance training, hypertrophy protocol
  * Endurance → Zone 2 cardio, long runs, cycling
  * Flexibility → Yoga, stretching routines, mobility work
  * General fitness → Mixed modality, functional training

## NUTRITION GUIDANCE
- Calculate and explain TDEE (Total Daily Energy Expenditure) when relevant.
- Provide macro breakdowns: protein, carbohydrates, fats.
- Recommend protein: 1.6-2.2g per kg bodyweight for active individuals.
- Suggest meal timing strategies (pre/post workout nutrition).
- Understand and respect Indian dietary preferences:
  * Vegetarian / Vegan / Eggetarian / Jain / Non-vegetarian options
  * Suggest Indian superfoods: dal, paneer, curd, ghee (in moderation), millets, turmeric, amla.
  * Indian high-protein sources: soya chunks, rajma, chana, moong, paneer, Greek yogurt.
  * Incorporate traditional Indian meal patterns (thali concept for balanced nutrition).
- Hydration: always recommend water intake = body weight (kg) × 35 ml minimum.
- Flag harmful fad diets and explain why they're unsustainable.

## BMI & HEALTH CALCULATIONS
- Use Asian/Indian BMI cut-offs (overweight = 23+, obese = 27.5+).
- When calculating BMI, also discuss limitations (doesn't account for muscle mass).
- Reference waist circumference alongside BMI for metabolic health assessment.
- Provide TDEE using Mifflin-St Jeor equation.

## INDIAN LIFESTYLE & CULTURAL SENSITIVITY
- Respect vegetarian/vegan lifestyle choices enthusiastically.
- Reference Indian seasons and festivals (e.g., extra hydration in summer months).
- Suggest Desi fitness alternatives: walking after dinner (post-dinner parikrama), cricket, kabaddi.
- Incorporate Ayurvedic wisdom where scientifically supported (Ashwagandha, Triphala, Turmeric).
- Account for Indian climate conditions in workout recommendations.
- Suggest Indian kitchen ingredients for natural supplement alternatives.

## SAFETY RULES (NON-NEGOTIABLE)
- NEVER recommend dangerous crash diets, extreme fasting beyond 16:8 IF, or unhealthy practices.
- NEVER suggest steroids, unregulated weight loss drugs, or harmful supplements.
- ALWAYS recommend consulting a doctor for medical conditions before starting exercise.
- ALWAYS recommend proper form and injury prevention.
- For users with health conditions (diabetes, hypertension, heart disease, pregnancy):
  * Acknowledge the condition and recommend medical clearance.
  * Provide modified exercise recommendations (lower intensity, doctor-approved activities).
- Do not diagnose medical conditions — direct users to healthcare professionals.
- When in doubt about safety, err on the side of caution.

## SCOPE & BOUNDARIES
- Focus exclusively on fitness, nutrition, wellness, and healthy lifestyle topics.
- For off-topic questions, gently redirect: "I'm specialised in fitness and nutrition! Let me help you with..."
- Do not provide financial, legal, or medical diagnosis advice.
- Be honest about limitations: "Based on general guidelines, but your trainer/doctor may have specific advice."

## RESPONSE FORMAT
- Structure responses with clear sections when giving plans.
- Use tables for weekly workout schedules and meal plans.
- Always end motivational responses with an encouraging sign-off.
- For calculations (BMI, TDEE, calories), show the formula and working.
- When suggesting workouts, include: exercise name, sets, reps, rest time, and modifications.
""".strip()


class FitnessAgent:
    """Orchestrates chat messages building and watsonx.ai model calls."""

    def __init__(self, watsonx_client):
        self.client = watsonx_client

    # ── System Context Builder ───────────────────────────────────────────────
    def _build_system_content(self, user_profile: Optional[Dict] = None, rag_ctx: str = "") -> str:
        parts = [AGENT_INSTRUCTIONS]
        if user_profile:
            parts.append("\n\n## CURRENT USER PROFILE")
            profile_lines = []
            mapping = {
                "age":              "Age",
                "gender":           "Gender",
                "height_cm":        "Height (cm)",
                "weight_kg":        "Weight (kg)",
                "fitness_level":    "Fitness Level",
                "activity_level":   "Activity Level",
                "primary_goal":     "Primary Goal",
                "diet_preference":  "Diet Preference",
                "health_conditions":"Health Conditions",
                "bmi":              "BMI",
                "bmi_category":     "BMI Category",
                "tdee":             "TDEE (cal/day)",
            }
            for key, label in mapping.items():
                val = user_profile.get(key)
                if val:
                    profile_lines.append(f"- {label}: {val}")
            if profile_lines:
                parts.append("\n".join(profile_lines))
        if rag_ctx:
            parts.append("\n\n" + rag_ctx)
        return "\n".join(parts)

    # ── Messages Builder ─────────────────────────────────────────────────────
    def _build_messages(
        self,
        user_message:   str,
        user_profile:   Optional[Dict],
        chat_history:   List[Dict],
        rag_ctx:        str,
    ) -> List[Dict]:
        system_content = self._build_system_content(user_profile, rag_ctx)
        messages = [{"role": "system", "content": system_content}]
        for msg in chat_history[-8:]:
            role = "user" if msg["role"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})
        return messages

    # ── Public Methods ───────────────────────────────────────────────────────
    def chat(
        self,
        user_message:  str,
        user_profile:  Optional[Dict]  = None,
        chat_history:  List[Dict]      = None,
    ) -> str:
        chat_history = chat_history or []
        rag_ctx      = build_rag_context(user_message, user_profile)
        messages     = self._build_messages(
            user_message, user_profile, chat_history, rag_ctx
        )
        logger.debug("Chat messages count: %d", len(messages))
        return self.client.generate(messages)

    def generate_workout_plan(self, user_profile: Dict) -> str:
        level    = user_profile.get("fitness_level", "beginner")
        goal     = user_profile.get("primary_goal", "general_fitness")
        days     = {"beginner": 3, "intermediate": 4, "advanced": 5}.get(level, 3)
        activity = user_profile.get("activity_level", "moderately_active")
        messages = self._build_messages(
            user_message=(
                f"Create a detailed {days}-day per week workout plan for me. "
                f"My goal is {goal.replace('_', ' ')}, fitness level: {level}, "
                f"activity level: {activity.replace('_', ' ')}. "
                "Include exercise names, sets, reps, rest periods, and weekly schedule. "
                "Format as a structured weekly plan."
            ),
            user_profile=user_profile,
            chat_history=[],
            rag_ctx=build_rag_context(f"workout plan {goal} {level}", user_profile),
        )
        return self.client.generate(messages)

    def generate_meal_plan(self, user_profile: Dict) -> str:
        diet  = user_profile.get("diet_preference", "vegetarian")
        goal  = user_profile.get("primary_goal", "general_fitness")
        tdee  = user_profile.get("tdee", 2000)
        messages = self._build_messages(
            user_message=(
                f"Create a 7-day Indian {diet} meal plan for {goal.replace('_', ' ')}. "
                f"Target calories: {tdee} cal/day. "
                "Include breakfast, lunch, dinner, and snacks. "
                "Use common Indian ingredients. Show approximate calories per meal."
            ),
            user_profile=user_profile,
            chat_history=[],
            rag_ctx=build_rag_context(f"meal plan {diet} {goal}", user_profile),
        )
        return self.client.generate(messages)

    def analyze_bmi(self, user_profile: Dict) -> str:
        bmi      = user_profile.get("bmi")
        category = user_profile.get("bmi_category", "Unknown")
        weight   = user_profile.get("weight_kg")
        height   = user_profile.get("height_cm")
        goal     = user_profile.get("primary_goal", "general_fitness")
        messages = self._build_messages(
            user_message=(
                f"Analyse my BMI of {bmi} (category: {category}). "
                f"I am {height}cm tall and weigh {weight}kg. My goal is {goal.replace('_', ' ')}. "
                "Explain what this means for my health, ideal weight range, "
                "and provide actionable steps to reach a healthy BMI."
            ),
            user_profile=user_profile,
            chat_history=[],
            rag_ctx=build_rag_context("BMI analysis healthy weight", user_profile),
        )
        return self.client.generate(messages)

    def get_motivation(self, user_profile: Optional[Dict] = None) -> str:
        goal  = ""
        level = ""
        if user_profile:
            goal  = user_profile.get("primary_goal", "")
            level = user_profile.get("fitness_level", "")
        messages = self._build_messages(
            user_message=(
                f"Give me a short (3-4 sentences), powerful fitness motivation message. "
                f"{'Goal: ' + goal.replace('_', ' ') + '.' if goal else ''} "
                f"{'Level: ' + level + '.' if level else ''} "
                "Make it energetic and actionable."
            ),
            user_profile=user_profile,
            chat_history=[],
            rag_ctx="",
        )
        return self.client.generate(messages)

    def calculate_calories(
        self,
        food_items:   str,
        user_profile: Optional[Dict] = None,
    ) -> str:
        messages = self._build_messages(
            user_message=(
                f"Estimate the total calories and macronutrients (protein, carbs, fat) for: {food_items}. "
                "Provide a breakdown per item and the total. "
                "State if the meal is suitable for my fitness goal."
            ),
            user_profile=user_profile,
            chat_history=[],
            rag_ctx=build_rag_context(f"calories nutrition {food_items}", user_profile),
        )
        return self.client.generate(messages)

    def suggest_hydration(self, user_profile: Optional[Dict] = None) -> str:
        weight = user_profile.get("weight_kg", 70) if user_profile else 70
        water  = round(weight * 35)
        messages = self._build_messages(
            user_message=(
                f"My weight is {weight}kg. Calculate my daily water intake requirement. "
                f"Base requirement is {water}ml. Adjust for my activity level and any exercise sessions. "
                "Give me a practical hydration schedule across the day including Indian-friendly electrolyte tips."
            ),
            user_profile=user_profile,
            chat_history=[],
            rag_ctx=build_rag_context("hydration water electrolytes", user_profile),
        )
        return self.client.generate(messages)
