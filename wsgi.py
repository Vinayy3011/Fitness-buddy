"""
Procfile-equivalent gunicorn runner for IBM Cloud / Heroku deployments.
Run: python run.py   (development)
     gunicorn wsgi:app  (production)
"""
from app import app, create_tables

if __name__ == "__main__":
    create_tables()
    app.run(debug=False)
