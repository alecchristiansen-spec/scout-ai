import base64
import os
from datetime import datetime
from typing import List

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///usage.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

APP_NAME = "Scout"
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
MAX_IMAGE_BYTES = 8 * 1024 * 1024
FREE_LIMIT = 5  # change this later to 20 or whatever you want

MODE_INSTRUCTIONS = {
    "simple": (
        "Explain things for a college student in plain language. "
        "Keep it concise, practical, and easy to understand."
    ),
    "detailed": (
        "Give a fuller explanation with context, but keep it readable. "
        "Use short sections and practical examples."
    ),
    "steps": (
        "Act like a calm tech coach. Give numbered steps, one action per step, "
        "and end with a short 'what to do next' section."
    ),
}

BASE_SYSTEM_PROMPT = """
You are Scout, an AI assistant for college students.
Your job is to help with tech troubleshooting, school productivity, research,
and everyday questions.

Rules:
- Be helpful, direct, and practical.
- Prefer simple explanations unless the user asks for more detail.
- If an image is uploaded, analyze what is actually visible before giving advice.
- If you are unsure, say so clearly.
- Do not claim you performed actions you did not perform.
""".strip()


class Usage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(100), unique=True, nullable=False)
    count = db.Column(db.Integer, default=0, nullable=False)
    last_reset = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


def _guess_mime(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".webp"):
        return "image/webp"
    if lower.endswith(".gif"):
        return "image/gif"
    return "image/jpeg"


def _get_user_ip() -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _get_or_create_usage(ip: str) -> Usage:
    user = Usage.query.filter_by(ip=ip).first()
    if not user:
        user = Usage(ip=ip, count=0)
        db.session.add(user)
        db.session.commit()
    return user


def _reset_if_needed(user: Usage) -> None:
    if (datetime.utcnow() - user.last_reset).days >= 30:
        user.count = 0
        user.last_reset = datetime.utcnow()
        db.session.commit()


@app.route("/")
def index():
    return render_template("index.html", app_name=APP_NAME, free_limit=FREE_LIMIT)


@app.route("/health")
def health():
    key_loaded = bool(os.getenv("OPENAI_API_KEY"))
    return jsonify({
        "ok": True,
        "api_key_loaded": key_loaded,
        "model": DEFAULT_MODEL,
        "free_limit": FREE_LIMIT,
    })


@app.route("/api/usage")
def get_usage():
    ip = _get_user_ip()
    user = _get_or_create_usage(ip)
    _reset_if_needed(user)

    remaining = max(FREE_LIMIT - user.count, 0)
    return jsonify({
        "count": user.count,
        "limit": FREE_LIMIT,
        "remaining": remaining,
    })


@app.route("/api/chat", methods=["POST"])
def api_chat():
    if not os.getenv("OPENAI_API_KEY"):
        return jsonify({
            "error": "OPENAI_API_KEY is not set. Add it to your environment or .env file."
        }), 500

    ip = _get_user_ip()
    user = _get_or_create_usage(ip)
    _reset_if_needed(user)

    if user.count >= FREE_LIMIT:
        return jsonify({
            "output_text": "You hit your free limit.",
            "limit_reached": True,
            "remaining": 0,
            "count": user.count,
            "limit": FREE_LIMIT,
        }), 200

    user_message = request.form.get("message", "").strip()
    mode = request.form.get("mode", "simple").strip().lower()
    research_enabled = request.form.get("research", "false").lower() == "true"

    if not user_message and "image" not in request.files:
        return jsonify({"error": "Please enter a message or upload an image."}), 400

    input_content: List[dict] = []

    if user_message:
        input_content.append({
            "type": "input_text",
            "text": user_message,
        })

    image_file = request.files.get("image")
    if image_file and image_file.filename:
        image_bytes = image_file.read()
        if len(image_bytes) > MAX_IMAGE_BYTES:
            return jsonify({"error": "Image is too large. Keep it under 8 MB."}), 400

        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        mime = _guess_mime(image_file.filename)
        input_content.append({
            "type": "input_image",
            "image_url": f"data:{mime};base64,{image_b64}",
            "detail": "auto",
        })

    tools = []
    if research_enabled:
        tools.append({"type": "web_search"})

    instructions = (
        BASE_SYSTEM_PROMPT
        + "\n\nResponse mode: "
        + MODE_INSTRUCTIONS.get(mode, MODE_INSTRUCTIONS["simple"])
    )

    try:
        response = client.responses.create(
            model=DEFAULT_MODEL,
            instructions=instructions,
            input=[{
                "role": "user",
                "content": input_content,
            }],
            tools=tools if tools else None,
        )

        user.count += 1
        db.session.commit()

        remaining = max(FREE_LIMIT - user.count, 0)

        return jsonify({
            "output_text": response.output_text,
            "model": DEFAULT_MODEL,
            "used_research": research_enabled,
            "limit_reached": False,
            "remaining": remaining,
            "count": user.count,
            "limit": FREE_LIMIT,
        })
    except Exception as exc:
        return jsonify({"error": f"OpenAI API error: {exc}"}), 500


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)