# Fitness Buddy AI 🏋️

> AI-powered fitness coaching web app built with **Flask** + **IBM watsonx.ai Granite** models.

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-green)](https://flask.palletsprojects.com)
[![IBM watsonx.ai](https://img.shields.io/badge/IBM-watsonx.ai-purple)](https://www.ibm.com/products/watsonx-ai)

---

## Features

| Feature | Description |
|---------|-------------|
| 🤖 **AI Chat Coach** | 24/7 fitness Q&A powered by IBM Granite |
| 💪 **Workout Planner** | AI-generated personalised workout plans |
| 🥗 **Nutrition AI** | Indian-friendly meal plans & calorie analysis |
| 📊 **Dashboard** | Charts, BMI, TDEE, calorie tracking |
| 🎯 **Goal Tracker** | SMART goals with progress bars & deadlines |
| 💧 **Hydration Guide** | Personalised daily water intake |
| 📐 **BMI Analysis** | Asian/Indian BMI cut-offs with AI analysis |
| 🧠 **RAG Knowledge** | 15+ curated fitness knowledge entries for context |
| 🔐 **Auth System** | Flask-Login with hashed passwords |
| 🌙 **Dark Mode** | Full dark/light theme with one click |
| 📱 **Mobile First** | Fully responsive Bootstrap 5.3 UI |
| 🗄️ **SQLite DB** | Zero-config local database |

---

## Quick Start

### 1. Clone / Download

```bash
git clone https://github.com/your-username/fitness-buddy-ai.git
cd fitness-buddy-ai
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```ini
# ── IBM watsonx.ai ──────────────────────────────────────────────
IBM_API_KEY=your_ibm_cloud_api_key_here
WATSONX_PROJECT_ID=your_watsonx_project_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com
GRANITE_MODEL_ID=ibm/granite-3-8b-instruct

# ── Flask ────────────────────────────────────────────────────────
SECRET_KEY=your_super_secret_key_here  # python -c "import secrets; print(secrets.token_hex(32))"
FLASK_ENV=development
FLASK_DEBUG=True
```

### 5. Run the App

```bash
python app.py
```

Open http://localhost:5000 in your browser.

---

## Getting IBM watsonx.ai Credentials

### Step 1 — IBM Cloud Account
1. Sign up at [cloud.ibm.com](https://cloud.ibm.com) (free tier available)
2. Go to **IAM → Manage → API keys → Create**
3. Copy the API key to `IBM_API_KEY`

### Step 2 — watsonx.ai Project
1. Visit [dataplatform.cloud.ibm.com](https://dataplatform.cloud.ibm.com)
2. Create a new project (or use existing)
3. Go to **Manage → General → Project ID**
4. Copy to `WATSONX_PROJECT_ID`

### Step 3 — Service Instance
1. In your watsonx.ai project, go to **Manage → Services & integrations**
2. Associate a **Watson Machine Learning** service instance
3. Ensure the service is in the same region as `WATSONX_URL`

### Available Granite Models
| Model ID | Description |
|----------|-------------|
| `ibm/granite-3-8b-instruct` | Latest, recommended, 8B params |
| `ibm/granite-13b-instruct-v2` | Larger, more detailed responses |
| `ibm/granite-3-2b-instruct` | Faster, lighter responses |

> **Note:** The app works in **Demo Mode** without credentials — you get predefined helpful responses to test the UI.

---

## Project Structure

```
fitness-buddy-ai/
│
├── app.py                  # Flask application & all routes
├── models.py               # SQLAlchemy database models
├── agent.py                # AI agent + AGENT_INSTRUCTIONS
├── watsonx_client.py       # IBM watsonx.ai Granite client
├── knowledge_base.py       # RAG fitness knowledge corpus
│
├── templates/
│   ├── base.html           # Base template (navbar, footer, dark mode)
│   ├── index.html          # Landing page
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   ├── dashboard.html      # Main dashboard with charts
│   ├── chat.html           # AI chatbot interface
│   ├── workout.html        # Workout planner
│   ├── nutrition.html      # Nutrition assistant
│   ├── profile.html        # Fitness profile editor
│   └── goals.html          # Goal tracker
│
├── static/
│   ├── css/styles.css      # Custom CSS (dark mode, animations)
│   └── js/main.js          # Dark mode, CSRF, toasts, animations
│
├── instance/               # SQLite DB (auto-created)
├── requirements.txt
├── .env                    # Your secrets (never commit!)
├── .env.example            # Template for .env
└── README.md
```

---

## Customising the AI Agent

Open [`agent.py`](agent.py) and edit the `AGENT_INSTRUCTIONS` string to customise:

```python
AGENT_INSTRUCTIONS = """
You are FitBuddy, an expert AI fitness coach...

## PERSONALITY & COMMUNICATION STYLE
- Warm, motivating, and encouraging...

## INDIAN LIFESTYLE & CULTURAL SENSITIVITY
- Respect vegetarian/vegan lifestyle...

## SAFETY RULES (NON-NEGOTIABLE)
- NEVER recommend dangerous crash diets...
"""
```

**Sections you can customise:**
- `PERSONALITY & COMMUNICATION STYLE` — tone, emoji usage, response format
- `FITNESS COACHING EXPERTISE` — workout philosophy, periodisation approach
- `NUTRITION GUIDANCE` — dietary preferences, supplement recommendations
- `INDIAN LIFESTYLE & CULTURAL SENSITIVITY` — local foods, traditions, seasons
- `SAFETY RULES` — medical disclaimers, prohibited advice
- `SCOPE & BOUNDARIES` — what topics to answer or redirect

---

## RAG Knowledge Base

The [`knowledge_base.py`](knowledge_base.py) contains 15+ curated fitness entries across categories:

- `workout` — training principles, HIIT, yoga, home workouts
- `nutrition` — Indian diet, calorie deficit, meal planning, supplements  
- `bmi` — Asian/Indian BMI cut-offs
- `recovery` — sleep, stretching, mobility
- `mental` — habit formation, motivation
- `safety` — injury prevention, warm-up

**Add your own entries:**

```python
FITNESS_KNOWLEDGE.append({
    "id": "custom001",
    "category": "workout",
    "tags": ["your", "tags"],
    "title": "Your Custom Entry",
    "content": "Your fitness knowledge content here...",
})
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Send chat message, get AI response |
| POST | `/api/chat/clear` | Clear chat history |
| GET | `/api/motivate` | Get AI motivation quote |
| POST | `/api/workout/generate` | Generate AI workout plan |
| POST | `/api/workout/<id>/delete` | Delete workout plan |
| POST | `/api/nutrition/meal-plan` | Generate AI 7-day meal plan |
| POST | `/api/nutrition/analyze` | Analyse food calories with AI |
| POST | `/api/nutrition/log` | Log a meal |
| GET | `/api/nutrition/hydration` | Get hydration tips |
| POST | `/api/goals/add` | Add a new fitness goal |
| POST | `/api/goals/<id>/update` | Update goal progress |
| POST | `/api/goals/<id>/delete` | Delete a goal |
| POST | `/api/progress/log` | Log weight/body fat |
| GET | `/api/progress/data` | Get progress chart data |
| POST | `/api/bmi/analyze` | AI BMI analysis |

---

## Deployment on IBM Cloud

### Option 1: IBM Cloud Foundry

```bash
# Install IBM Cloud CLI
# https://cloud.ibm.com/docs/cli

# Login
ibmcloud login

# Target org and space
ibmcloud target --cf

# Create manifest.yml
cat > manifest.yml << EOF
applications:
  - name: fitness-buddy-ai
    memory: 512M
    instances: 1
    buildpack: python_buildpack
    command: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2
    env:
      IBM_API_KEY: YOUR_KEY
      WATSONX_PROJECT_ID: YOUR_PROJECT_ID
      WATSONX_URL: https://us-south.ml.cloud.ibm.com
      GRANITE_MODEL_ID: ibm/granite-3-8b-instruct
      SECRET_KEY: YOUR_SECRET_KEY
      FLASK_ENV: production
      FLASK_DEBUG: "False"
EOF

# Deploy
ibmcloud cf push
```

### Option 2: IBM Code Engine (Container)

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p instance
EXPOSE 8080
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120"]
```

```bash
# Build and push
docker build -t fitness-buddy-ai .
docker tag fitness-buddy-ai icr.io/YOUR_NAMESPACE/fitness-buddy-ai:latest
docker push icr.io/YOUR_NAMESPACE/fitness-buddy-ai:latest

# Deploy to Code Engine
ibmcloud ce application create \
  --name fitness-buddy \
  --image icr.io/YOUR_NAMESPACE/fitness-buddy-ai:latest \
  --port 8080 \
  --env IBM_API_KEY=YOUR_KEY \
  --env WATSONX_PROJECT_ID=YOUR_PROJECT_ID \
  --env SECRET_KEY=YOUR_SECRET
```

### Option 3: Production with Gunicorn

```bash
# Install gunicorn (included in requirements.txt)
gunicorn app:app \
  --bind 0.0.0.0:5000 \
  --workers 4 \
  --worker-class sync \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `IBM_API_KEY` | Yes* | IBM Cloud IAM API Key |
| `WATSONX_PROJECT_ID` | Yes* | watsonx.ai Project ID |
| `WATSONX_URL` | No | Endpoint URL (default: us-south) |
| `GRANITE_MODEL_ID` | No | Granite model (default: granite-3-8b-instruct) |
| `SECRET_KEY` | Yes | Flask session secret key |
| `FLASK_ENV` | No | `development` or `production` |
| `FLASK_DEBUG` | No | `True` or `False` |

*\* App works in Demo Mode without these, but uses predefined responses.*

---

## Security Notes

- ✅ Passwords hashed with Werkzeug (PBKDF2+SHA256)
- ✅ CSRF protection on all POST forms and AJAX
- ✅ SQLAlchemy ORM (prevents SQL injection)
- ✅ Flask-Login session management
- ✅ API keys loaded from `.env` (never hardcoded)
- ⚠️ Add HTTPS in production (nginx or Cloud load balancer)
- ⚠️ Set `FLASK_DEBUG=False` in production
- ⚠️ Use a strong random `SECRET_KEY` in production

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, Flask 3.0 |
| AI | IBM watsonx.ai, Granite 3.0 |
| Database | SQLite (dev), PostgreSQL-ready |
| ORM | SQLAlchemy 2.0 + Flask-SQLAlchemy |
| Auth | Flask-Login + Flask-WTF CSRF |
| Frontend | Bootstrap 5.3, Chart.js 4, Marked.js |
| Icons | Bootstrap Icons 1.11 |
| Fonts | Inter (Google Fonts) |
| Deployment | Gunicorn, IBM Cloud Foundry / Code Engine |

---

## License

MIT License — free to use, modify, and deploy.

---

*Built with ❤️ for the Indian fitness community. Always consult a doctor before starting any new fitness program.*
#   F i t n e s s - B u d d y - A I  
 #   F i t n e s s - b u d d y  
 