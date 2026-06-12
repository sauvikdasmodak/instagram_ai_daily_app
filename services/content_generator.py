from __future__ import annotations

import os
import random
import re
from datetime import date
from typing import Iterable

import requests

EVERGREEN_AI_INSIGHTS = [
    "AI works best when it supports a clear human decision, not when it replaces thinking.",
    "The strongest AI users are not the people with the fanciest tools; they are the people with the clearest questions.",
    "A good prompt is really a good brief: context, goal, constraints, examples, and success criteria.",
    "Responsible AI is not a blocker. It is how teams make AI useful, trusted, and scalable.",
    "The future belongs to people who can combine domain knowledge with AI fluency.",
    "Automation creates value when it removes repetitive work and gives people more time for judgment.",
    "AI agents need guardrails, monitoring, and clear handoffs. Autonomy without governance becomes risk.",
    "Small, focused AI experiments often beat large unclear AI programs.",
    "The best AI habit is simple: document what works, measure the outcome, and improve the workflow.",
    "AI will not remove the need to learn. It makes learning faster for people who stay curious."
]

HOOKS = [
    "AI thought for today",
    "One AI idea worth using today",
    "A simple AI mindset shift",
    "Today’s AI reminder",
    "AI career note",
    "Build this AI habit"
]

CALLS_TO_ACTION = [
    "Save this if you are building your AI skills.",
    "Follow for simple, practical AI ideas.",
    "Try this once today and notice the difference.",
    "Share this with someone learning AI.",
    "Build one useful AI habit at a time."
]


def clean_hashtag(tag: str) -> str:
    tag = re.sub(r"[^A-Za-z0-9_]", "", tag.strip().lstrip("#"))
    return f"#{tag}" if tag else ""


def fallback_post(topic: str, hashtags: Iterable[str], tone: str = "") -> dict:
    insight = random.choice(EVERGREEN_AI_INSIGHTS)
    hook = random.choice(HOOKS)
    cta = random.choice(CALLS_TO_ACTION)
    angle = random.choice([
        "Start with one workflow you repeat every week.",
        "Use AI to make your first draft faster, then use your judgment to make it better.",
        "Ask better questions before asking for faster answers.",
        "Measure the result: time saved, quality improved, or risk reduced.",
        "Keep humans in the loop where decisions affect customers, money, safety, or trust."
    ])

    caption = (
        f"{hook}: {topic}\n\n"
        f"{insight}\n\n"
        f"Practical move: {angle}\n\n"
        f"Motivation: You do not need to master every AI tool. You need to build the habit of learning, testing, and applying AI where it creates real value.\n\n"
        f"{cta}\n\n"
        + " ".join(filter(None, [clean_hashtag(h) for h in hashtags]))
    )
    title = topic[:54].strip()
    subtitle = insight
    return {"title": title, "subtitle": subtitle, "caption": caption, "provider": "built-in"}


def generate_with_openai(topic: str, hashtags: list[str], tone: str) -> dict | None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip() or "gpt-4.1-mini"
    prompt = f"""
Create one Instagram post about this AI topic: {topic}
Tone: {tone}
Audience: professionals learning AI and technology leadership.
Requirements:
- Sounds informative and motivating, not hype.
- No fake statistics, no unverifiable breaking news.
- Caption 900-1400 characters.
- Include one practical action.
- End with a soft follow/save/share CTA.
- Include these hashtags only if relevant: {', '.join(hashtags)}
Return JSON with keys: title, subtitle, caption.
""".strip()

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You create accurate, evergreen, professional social media content about AI."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.75,
                "response_format": {"type": "json_object"}
            },
            timeout=45,
        )
        response.raise_for_status()
        data = response.json()
        import json
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        if not all(parsed.get(k) for k in ["title", "subtitle", "caption"]):
            return None
        parsed["provider"] = f"openai:{model}"
        return parsed
    except Exception:
        return None


def generate_post(topic: str, hashtags: list[str], tone: str) -> dict:
    generated = generate_with_openai(topic, hashtags, tone)
    if generated:
        return generated
    return fallback_post(topic, hashtags, tone)
