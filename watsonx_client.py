"""
IBM watsonx.ai Model Client
Supports IBM Granite and Llama 3 models via ibm-watsonx-ai SDK.
Uses the modern /ml/v1/text/chat API (model.chat) for all models.
"""
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class WatsonxClient:
    """Thin wrapper around ibm-watsonx-ai ModelInference (chat API)."""

    def __init__(self):
        self.api_key    = os.getenv("IBM_API_KEY", "")
        self.project_id = os.getenv("WATSONX_PROJECT_ID", "")
        self.url        = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
        self.model_id   = os.getenv("GRANITE_MODEL_ID", "ibm/granite-3-8b-instruct")
        self._model     = None
        self._ready     = False
        self._init_model()

    # ── Initialisation ───────────────────────────────────────────────────────
    def _init_model(self):
        demo_values = {"", "your_ibm_cloud_api_key_here", "demo", "test"}
        if not self.api_key or self.api_key.lower() in demo_values:
            logger.warning("IBM_API_KEY not configured — running in demo mode.")
            return
        if not self.project_id or self.project_id.lower() in {"", "your_watsonx_project_id_here", "demo", "test"}:
            logger.warning("WATSONX_PROJECT_ID not configured — running in demo mode.")
            return
        try:
            from ibm_watsonx_ai import Credentials
            from ibm_watsonx_ai.foundation_models import ModelInference

            credentials = Credentials(api_key=self.api_key, url=self.url)
            self._model = ModelInference(
                model_id=self.model_id,
                credentials=credentials,
                project_id=self.project_id,
            )
            self._ready = True
            logger.info("WatsonxClient ready (chat API): model=%s", self.model_id)
        except Exception as exc:
            logger.error("Failed to initialise WatsonxClient: %s", exc)

    # ── Public API ───────────────────────────────────────────────────────────
    @property
    def is_ready(self) -> bool:
        return self._ready

    def generate(self, messages: list, max_tokens: int = 1024) -> str:
        """
        Generate a response using the chat completions API.

        :param messages: OpenAI-style list of dicts, e.g.
                         [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        :param max_tokens: maximum tokens to generate
        """
        if not self._ready:
            # Extract last user message for demo routing
            user_text = ""
            for m in reversed(messages):
                if m.get("role") == "user":
                    user_text = m.get("content", "")
                    break
            return self._demo_response(user_text)
        try:
            params = {"max_completion_tokens": max_tokens, "temperature": 0.7}
            response = self._model.chat(messages=messages, params=params)
            text = response["choices"][0]["message"]["content"]
            return text.strip() if text else "I could not generate a response."
        except Exception as exc:
            logger.error("Generation error: %s", exc)
            return f"⚠️ Error communicating with IBM watsonx.ai: {exc}"

    def stream(self, messages: list, max_tokens: int = 1024):
        """
        Yield text chunks using the streaming chat API.
        Each yielded value is a string fragment (may be empty for heartbeat chunks).
        Falls back to yielding the full demo response as one chunk.
        """
        if not self._ready:
            user_text = ""
            for m in reversed(messages):
                if m.get("role") == "user":
                    user_text = m.get("content", "")
                    break
            yield self._demo_response(user_text)
            return
        try:
            params = {"max_completion_tokens": max_tokens, "temperature": 0.7}
            for chunk in self._model.chat_stream(messages=messages, params=params):
                choices = chunk.get("choices") or []
                if not choices:
                    continue  # final [DONE] sentinel has empty choices
                delta = choices[0].get("delta", {}).get("content", "") or ""
                if delta:
                    yield delta
        except Exception as exc:
            logger.error("Stream error: %s", exc)
            yield f"⚠️ Error communicating with IBM watsonx.ai: {exc}"

    # ── Demo / Fallback ──────────────────────────────────────────────────────
    @staticmethod
    def _demo_response(prompt: str) -> str:
        """Friendly fallback when API keys are not configured."""
        prompt_lower = prompt.lower()
        if any(w in prompt_lower for w in ["workout", "exercise", "train"]):
            return (
                "🏋️ **Demo Mode** — IBM watsonx.ai not configured yet.\n\n"
                "Here's a quick sample workout plan:\n"
                "- **Monday**: Upper body strength (push-ups, rows, shoulder press)\n"
                "- **Wednesday**: Lower body (squats, lunges, calf raises)\n"
                "- **Friday**: Full-body HIIT (20 min circuit)\n\n"
                "Configure your IBM_API_KEY and WATSONX_PROJECT_ID in `.env` to unlock full AI responses."
            )
        if any(w in prompt_lower for w in ["diet", "nutrition", "food", "meal", "eat", "calorie"]):
            return (
                "🥗 **Demo Mode** — IBM watsonx.ai not configured yet.\n\n"
                "Quick nutrition tip: Aim for 30% protein, 40% complex carbs, 30% healthy fats. "
                "Indian staples like dal, paneer, curd, and whole grains are excellent choices.\n\n"
                "Configure your IBM_API_KEY and WATSONX_PROJECT_ID in `.env` to unlock full AI responses."
            )
        if any(w in prompt_lower for w in ["bmi", "weight", "height"]):
            return (
                "📊 **Demo Mode** — BMI = weight(kg) / height(m)²\n"
                "Healthy BMI range for Indians: 18.5 – 22.9\n\n"
                "Configure your IBM_API_KEY and WATSONX_PROJECT_ID in `.env` to unlock full AI responses."
            )
        return (
            "👋 **Demo Mode** — IBM watsonx.ai not configured yet.\n\n"
            "I'm your AI Fitness Buddy! I can help with:\n"
            "• Personalised workout plans\n• Nutrition and meal planning\n"
            "• BMI & calorie calculations\n• Fitness goal tracking\n"
            "• Hydration and recovery tips\n\n"
            "To activate full AI: add your `IBM_API_KEY` and `WATSONX_PROJECT_ID` to `.env`."
        )


# Singleton instance
watsonx = WatsonxClient()
