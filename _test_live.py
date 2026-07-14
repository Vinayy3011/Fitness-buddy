"""Live watsonx.ai integration test."""
import os, sys
from dotenv import load_dotenv
load_dotenv(".env", override=True)

from watsonx_client import WatsonxClient
client = WatsonxClient()

print(f"model_id        : {client.model_id}")
print(f"is_ready        : {client.is_ready}")
print(f"uses_llama_fmt  : {client.uses_llama_format}")

if not client.is_ready:
    print("\nFAIL: client not ready — check stderr above for init error.")
    sys.exit(1)

from agent import FitnessAgent
agent = FitnessAgent(client)

# Build a minimal Llama-format prompt and call the model
profile = {
    "age": 28, "gender": "male", "height_cm": 175, "weight_kg": 80,
    "fitness_level": "beginner", "activity_level": "moderately_active",
    "primary_goal": "weight_loss", "diet_preference": "vegetarian",
    "bmi": 26.1, "bmi_category": "Overweight", "tdee": 2300,
}
print("\nSending test message to watsonx.ai...")
reply = agent.chat("Give me one quick tip for weight loss.", profile, [])

print(f"\nResponse ({len(reply)} chars):\n{'-'*60}")
print(reply[:600])
print(f"\nLive API call: OK")
