"""
RAG-based Fitness Knowledge Base
Provides context-aware fitness information retrieval for the AI agent.
"""
import re
from typing import List, Dict, Tuple

# ─────────────────────────────────────────────
#  Structured fitness knowledge corpus
# ─────────────────────────────────────────────
FITNESS_KNOWLEDGE = [
    # ── Workout Principles ───────────────────────────────────────────────────
    {
        "id": "w001", "category": "workout",
        "tags": ["beginner", "basics", "starting"],
        "title": "Beginner Workout Principles",
        "content": (
            "Beginners should start with 2-3 sessions per week, focusing on full-body compound "
            "movements: squats, deadlifts, push-ups, rows, and lunges. Rest 48 hours between "
            "sessions. Start with bodyweight or light weights. Prioritise form over load. "
            "Progressive overload: add 5% weight or 1-2 reps per week when current sets feel easy."
        ),
    },
    {
        "id": "w002", "category": "workout",
        "tags": ["cardio", "endurance", "fat loss"],
        "title": "Cardio and Fat Loss",
        "content": (
            "For fat loss, combine HIIT (High-Intensity Interval Training) 2x/week with "
            "steady-state cardio 2x/week. HIIT: 20-30 min, 30s sprint + 60s rest intervals. "
            "Steady-state: 40-60 min brisk walk, cycling, or swimming at 60-70% max HR. "
            "Zone 2 cardio (conversational pace) is excellent for metabolic health and fat oxidation."
        ),
    },
    {
        "id": "w003", "category": "workout",
        "tags": ["strength", "muscle", "hypertrophy"],
        "title": "Muscle Building (Hypertrophy)",
        "content": (
            "For muscle gain: train each muscle group 2x/week. Rep range 6-12, 3-4 sets per exercise. "
            "Rest 60-90 seconds between sets. Progressive overload is mandatory. Include compound lifts "
            "(bench press, squat, deadlift, overhead press, row) and isolation exercises. "
            "Ensure 1.6-2.2g protein per kg of bodyweight daily."
        ),
    },
    {
        "id": "w004", "category": "workout",
        "tags": ["yoga", "flexibility", "mindfulness", "indian"],
        "title": "Yoga and Indian Fitness Traditions",
        "content": (
            "Yoga styles: Hatha (gentle, beginner-friendly), Vinyasa (flow, moderate intensity), "
            "Ashtanga (rigorous), Yin (deep stretching). Surya Namaskar (Sun Salutation) 12 rounds "
            "burns ~150 calories and improves flexibility. Pranayama breathing (Anulom-Vilom, "
            "Kapalbhati) reduces stress and improves lung capacity. Practice on an empty stomach, "
            "preferably at sunrise or sunset."
        ),
    },
    {
        "id": "w005", "category": "workout",
        "tags": ["hiit", "home", "no equipment"],
        "title": "Home HIIT Workout (No Equipment)",
        "content": (
            "20-minute home HIIT: Warm-up 3 min (jumping jacks, arm circles). "
            "Circuit (4 rounds): Burpees 10 reps, Mountain climbers 20 reps, Jump squats 15 reps, "
            "Push-ups 10 reps, High knees 30 sec. Rest 30 sec between exercises, 1 min between rounds. "
            "Cool down 3 min (static stretches). Burns 200-300 calories."
        ),
    },
    # ── Nutrition ────────────────────────────────────────────────────────────
    {
        "id": "n001", "category": "nutrition",
        "tags": ["indian", "vegetarian", "diet", "meal"],
        "title": "Indian Vegetarian Diet for Fitness",
        "content": (
            "High-protein Indian vegetarian sources: Dal (lentils) 18g/100g dry, Paneer 18g/100g, "
            "Chana (chickpeas) 19g/100g dry, Rajma (kidney beans) 24g/100g dry, Soya chunks 52g/100g dry, "
            "Tofu 8g/100g, Greek yogurt 10g/100g, Eggs (eggetarian) 13g/100g. "
            "Balanced Indian meal: 1 cup dal + 2 rotis + 1 cup sabzi + 1 cup curd = ~500 cal, 25g protein."
        ),
    },
    {
        "id": "n002", "category": "nutrition",
        "tags": ["calorie", "macros", "weight loss"],
        "title": "Calorie Deficit for Weight Loss",
        "content": (
            "Safe weight loss: 0.5-1 kg/week = 500-1000 calorie deficit/day. "
            "Never go below 1200 cal/day (women) or 1500 cal/day (men). "
            "Macros for weight loss: 30-35% protein, 35-40% carbs, 25-30% fat. "
            "Prioritise fibre-rich carbs (oats, brown rice, millets like jowar/bajra). "
            "Avoid refined sugar, maida (white flour), and ultra-processed foods."
        ),
    },
    {
        "id": "n003", "category": "nutrition",
        "tags": ["muscle gain", "protein", "calories", "bulking"],
        "title": "Nutrition for Muscle Gain",
        "content": (
            "Calorie surplus: 200-500 cal above TDEE. Protein: 2.0-2.4g per kg bodyweight. "
            "Carbs (energy): 4-6g per kg bodyweight. Fat: 0.8-1g per kg bodyweight. "
            "Pre-workout (1-2hr before): carb + protein meal (rice + dal/chicken). "
            "Post-workout (within 30-45 min): fast protein + carbs (whey + banana, or curd + rice). "
            "Creatine monohydrate 3-5g/day is safe and effective for strength and muscle gain."
        ),
    },
    {
        "id": "n004", "category": "nutrition",
        "tags": ["hydration", "water", "electrolytes"],
        "title": "Hydration Guidelines",
        "content": (
            "Daily water intake: body weight (kg) × 35 ml. Active individuals add 500-750 ml/hr of exercise. "
            "In Indian summers (35-45°C), increase by additional 500-1000 ml. "
            "Electrolytes lost in sweat: sodium, potassium, magnesium. "
            "Natural electrolyte sources: coconut water, nimbu pani (lemon water + salt + sugar), "
            "buttermilk (chaas). Avoid sugary sports drinks unless exercising >90 minutes intensely."
        ),
    },
    {
        "id": "n005", "category": "nutrition",
        "tags": ["meal plan", "indian", "weight loss", "sample"],
        "title": "Sample Indian Weight Loss Meal Plan",
        "content": (
            "Breakfast (7-8 AM): 2 moong dal chilla + 1 cup green chutney + 1 cup masala chai (no sugar). "
            "Mid-morning (10 AM): 1 fruit + 10 almonds. "
            "Lunch (1 PM): 2 jowar rotis + 1 cup rajma/dal + 1 cup mixed sabzi + 1 cup curd. "
            "Evening (4 PM): 1 cup green tea + roasted chana 30g. "
            "Dinner (7-8 PM): 1 cup khichdi + 1 cup palak soup. Total: ~1600 cal, 75g protein."
        ),
    },
    {
        "id": "n006", "category": "nutrition",
        "tags": ["supplements", "vitamins", "indian"],
        "title": "Essential Supplements for Indians",
        "content": (
            "Common deficiencies in India: Vitamin D3 (60-70% Indians), B12 (especially vegetarians), "
            "Iron (especially women), Calcium, Omega-3. "
            "Recommended: Vitamin D3 2000-4000 IU/day with K2, B12 500mcg/day (vegetarians), "
            "Omega-3 1g EPA+DHA/day. Protein powder (whey/pea) if dietary protein is insufficient. "
            "Always consult a doctor before starting supplements."
        ),
    },
    # ── BMI & Body Composition ───────────────────────────────────────────────
    {
        "id": "b001", "category": "bmi",
        "tags": ["bmi", "body mass index", "weight"],
        "title": "BMI Interpretation for Indians",
        "content": (
            "BMI = weight(kg) / height(m)². Asian/Indian-specific cut-offs (lower than WHO): "
            "Underweight: <18.5, Normal: 18.5-22.9, Overweight: 23.0-27.4, Obese Class I: 27.5-32.4, "
            "Obese Class II: ≥32.5. Indians have higher body fat % at same BMI as Caucasians. "
            "Waist circumference is also important: Men <90 cm, Women <80 cm for metabolic health."
        ),
    },
    # ── Recovery & Sleep ─────────────────────────────────────────────────────
    {
        "id": "r001", "category": "recovery",
        "tags": ["sleep", "recovery", "rest"],
        "title": "Sleep and Recovery for Fitness",
        "content": (
            "Sleep 7-9 hours for optimal recovery. Most muscle repair and hormonal restoration "
            "occurs during deep sleep (stages 3-4). Poor sleep raises cortisol (fat storage), "
            "reduces testosterone/GH, and impairs muscle protein synthesis. "
            "Sleep hygiene tips: dark room, 18-22°C, avoid screens 1hr before bed, "
            "consistent sleep/wake times. Ashwagandha 300-600mg KSM-66 extract before bed "
            "improves sleep quality and reduces cortisol (safe Ayurvedic adaptogen)."
        ),
    },
    {
        "id": "r002", "category": "recovery",
        "tags": ["stretching", "mobility", "foam rolling"],
        "title": "Post-Workout Recovery",
        "content": (
            "Post-workout: static stretching (hold 30-60 sec per muscle), foam rolling, "
            "cold shower (contrast therapy), protein meal within 45 min. "
            "DOMS (Delayed Onset Muscle Soreness) peaks 24-48hr post-exercise; light movement helps. "
            "Active recovery: gentle yoga, 20-min walk, swimming on rest days. "
            "Epsom salt bath (magnesium sulfate) reduces muscle soreness."
        ),
    },
    # ── Mental Fitness ───────────────────────────────────────────────────────
    {
        "id": "m001", "category": "mental",
        "tags": ["motivation", "habits", "mindset"],
        "title": "Building Fitness Habits",
        "content": (
            "Habit stacking: attach workout to existing habit (after morning chai, before dinner). "
            "Start with minimum viable workout (10-15 min) to build consistency. "
            "Track streaks — visual progress motivates. Find intrinsic motivation (energy, health) "
            "not just aesthetics. Social accountability (workout buddy, group class) increases "
            "adherence by 65%. Celebrate small wins. Missing one day is OK; missing two is a pattern."
        ),
    },
    # ── Safety ───────────────────────────────────────────────────────────────
    {
        "id": "s001", "category": "safety",
        "tags": ["safety", "injury", "warm up"],
        "title": "Workout Safety Guidelines",
        "content": (
            "Always warm up 5-10 min before exercise (light cardio + dynamic stretches). "
            "Cool down 5-10 min after (static stretches). Listen to pain signals—sharp/joint pain = stop. "
            "Muscle soreness (dull ache) is normal; joint pain is not. "
            "Stay hydrated throughout. Never skip rest days. For medical conditions (diabetes, "
            "hypertension, heart disease), consult a doctor before starting an exercise program."
        ),
    },
]

# ─────────────────────────────────────────────
#  Retrieval Engine
# ─────────────────────────────────────────────

def _score(query: str, entry: Dict) -> float:
    """Simple TF-IDF-inspired keyword scoring."""
    q_tokens = set(re.findall(r"\w+", query.lower()))
    score = 0.0
    searchable = (
        " ".join(entry["tags"])
        + " " + entry["title"]
        + " " + entry["content"]
        + " " + entry["category"]
    ).lower()
    tokens = set(re.findall(r"\w+", searchable))
    score += len(q_tokens & tokens) * 1.0
    # Boost title / tag matches
    title_tokens = set(re.findall(r"\w+", entry["title"].lower()))
    tag_tokens   = set(re.findall(r"\w+", " ".join(entry["tags"]).lower()))
    score += len(q_tokens & title_tokens) * 1.5
    score += len(q_tokens & tag_tokens)   * 2.0
    return score


def retrieve_knowledge(query: str, top_k: int = 3) -> List[Dict]:
    """Retrieve the most relevant fitness knowledge entries for a query."""
    scored = [(entry, _score(query, entry)) for entry in FITNESS_KNOWLEDGE]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [e for e, s in scored[:top_k] if s > 0]


def build_rag_context(query: str, user_profile: Dict = None) -> str:
    """Build a RAG context string to inject into the prompt."""
    entries = retrieve_knowledge(query, top_k=3)
    if not entries:
        return ""

    lines = ["=== Relevant Fitness Knowledge ==="]
    for e in entries:
        lines.append(f"\n[{e['title']}]\n{e['content']}")

    if user_profile:
        lines.append("\n=== User Profile ===")
        for k, v in user_profile.items():
            if v:
                lines.append(f"{k}: {v}")

    return "\n".join(lines)


def get_category_knowledge(category: str) -> List[Dict]:
    """Return all entries for a given category."""
    return [e for e in FITNESS_KNOWLEDGE if e["category"] == category]


def get_quick_tips(category: str = None) -> List[str]:
    """Return a list of quick tip strings."""
    tips = [
        "💧 Drink a glass of water first thing in the morning.",
        "🏃 Even a 10-minute walk counts as exercise!",
        "🥗 Fill half your plate with vegetables at every meal.",
        "😴 Sleep is when your muscles actually grow.",
        "🧘 5 minutes of deep breathing reduces cortisol significantly.",
        "📱 Put your phone down 1 hour before bed for better sleep.",
        "🥜 Handful of nuts = perfect pre-workout snack.",
        "🏋️ Consistency beats intensity — show up even on tired days.",
        "🌅 Morning workouts boost metabolism for the whole day.",
        "🫁 Breathe out during the exertion phase of every exercise.",
        "🌿 Ashwagandha and Turmeric (haldi) are powerful natural supplements.",
        "🍌 Banana + peanut butter = excellent post-workout snack.",
        "⏱️ Rest 48 hours before training the same muscle group again.",
        "📏 Track progress with measurements, not just the scale.",
        "🤸 Warm up for 5 minutes before every workout to prevent injury.",
    ]
    return tips
