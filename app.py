from __future__ import annotations

import argparse
import os
import random
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

from services.content_generator import generate_post
from services.image_builder import build_post_image
from services.instagram_client import InstagramClient
from services.storage import add_post, get_post, load_config, load_posts, save_config, update_post

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "local-dev-secret")

scheduler = BackgroundScheduler()


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def current_public_media_base(config: dict) -> str:
    return (config.get("public_media_base_url") or os.getenv("PUBLIC_MEDIA_BASE_URL", "")).strip().rstrip("/")


def public_url_for_file(filename: str, config: dict) -> str | None:
    base = current_public_media_base(config)
    if not base:
        return None
    return f"{base}/{quote(filename)}"


def generate_and_store(topic: str | None = None) -> dict:
    config = load_config()
    topics = config.get("topics") or [config.get("default_topic", "AI")]
    selected_topic = topic or config.get("default_topic") or random.choice(topics)
    if selected_topic == "__random__":
        selected_topic = random.choice(topics)

    post_id = uuid.uuid4().hex[:10]
    generated = generate_post(
        topic=selected_topic,
        hashtags=config.get("hashtags", []),
        tone=config.get("tone", "informative and motivating"),
    )
    filename = build_post_image(
        title=generated["title"],
        subtitle=generated["subtitle"],
        brand_name=config.get("brand_name", "AI Daily Spark"),
        handle=config.get("instagram_handle", ""),
        post_id=post_id,
    )
    post = {
        "id": post_id,
        "topic": selected_topic,
        "title": generated["title"],
        "subtitle": generated["subtitle"],
        "caption": generated["caption"],
        "provider": generated.get("provider", "unknown"),
        "image_filename": filename,
        "status": "draft",
        "created_at": now_iso(),
        "published_at": None,
        "instagram_media_id": None,
        "last_error": None,
    }
    add_post(post)
    return post


def scheduled_job() -> None:
    config = load_config()
    if not config.get("auto_generate", True):
        return
    post = generate_and_store("__random__")
    if config.get("auto_publish") and not config.get("require_manual_approval", True):
        publish_post(post["id"])


def reschedule_daily_job() -> None:
    config = load_config()
    daily_time = config.get("daily_time", "08:30")
    hour, minute = [int(x) for x in daily_time.split(":")[:2]]
    if scheduler.get_job("daily_ai_post"):
        scheduler.remove_job("daily_ai_post")
    scheduler.add_job(
        scheduled_job,
        "cron",
        hour=hour,
        minute=minute,
        id="daily_ai_post",
        replace_existing=True,
    )


def publish_post(post_id: str):
    config = load_config()
    post = get_post(post_id)
    if not post:
        return False, "Post not found", None
    image_url = public_url_for_file(post["image_filename"], config)
    if not image_url:
        msg = "No public_media_base_url configured. Meta cannot fetch local files. Deploy the app or host generated images over HTTPS."
        update_post(post_id, last_error=msg)
        return False, msg, None
    client = InstagramClient()
    result = client.publish_image(image_url=image_url, caption=post["caption"])
    if result.ok:
        update_post(
            post_id,
            status="published",
            published_at=now_iso(),
            instagram_media_id=result.data.get("id"),
            last_error=None,
        )
    else:
        update_post(post_id, status="error", last_error=f"{result.message}: {result.data}")
    return result.ok, result.message, result.data


@app.route("/")
def index():
    config = load_config()
    posts = load_posts()
    public_base = current_public_media_base(config)
    account = InstagramClient().check_account()
    next_run = None
    job = scheduler.get_job("daily_ai_post")
    if job and job.next_run_time:
        next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S %Z")
    return render_template("index.html", config=config, posts=posts[:20], public_base=public_base, account=account, next_run=next_run)


@app.post("/generate")
def generate_route():
    topic = request.form.get("topic") or "__random__"
    post = generate_and_store(topic)
    flash(f"Draft generated: {post['title']}", "success")
    return redirect(url_for("view_post", post_id=post["id"]))


@app.route("/post/<post_id>")
def view_post(post_id):
    post = get_post(post_id)
    if not post:
        flash("Post not found", "error")
        return redirect(url_for("index"))
    config = load_config()
    image_url = public_url_for_file(post["image_filename"], config)
    return render_template("post.html", post=post, config=config, image_url=image_url)


@app.post("/post/<post_id>/publish")
def publish_route(post_id):
    ok, message, data = publish_post(post_id)
    flash(message, "success" if ok else "error")
    return redirect(url_for("view_post", post_id=post_id))


@app.post("/post/<post_id>/approve")
def approve_route(post_id):
    update_post(post_id, status="approved", last_error=None)
    flash("Post marked as approved", "success")
    return redirect(url_for("view_post", post_id=post_id))


@app.post("/post/<post_id>/update-caption")
def update_caption_route(post_id):
    caption = request.form.get("caption", "").strip()
    update_post(post_id, caption=caption)
    flash("Caption updated", "success")
    return redirect(url_for("view_post", post_id=post_id))


@app.route("/settings", methods=["GET", "POST"])
def settings():
    config = load_config()
    if request.method == "POST":
        config["brand_name"] = request.form.get("brand_name", "AI Daily Spark").strip()
        config["instagram_handle"] = request.form.get("instagram_handle", "").strip().lstrip("@")
        config["default_topic"] = request.form.get("default_topic", "Practical AI for everyday work").strip()
        config["tone"] = request.form.get("tone", "informative and motivating").strip()
        config["daily_time"] = request.form.get("daily_time", "08:30").strip()
        config["public_media_base_url"] = request.form.get("public_media_base_url", "").strip().rstrip("/")
        config["auto_generate"] = bool(request.form.get("auto_generate"))
        config["auto_publish"] = bool(request.form.get("auto_publish"))
        config["require_manual_approval"] = bool(request.form.get("require_manual_approval"))
        topics = [x.strip() for x in request.form.get("topics", "").splitlines() if x.strip()]
        hashtags = [x.strip().lstrip("#") for x in request.form.get("hashtags", "").replace(",", "\n").splitlines() if x.strip()]
        if topics:
            config["topics"] = topics
        if hashtags:
            config["hashtags"] = hashtags
        save_config(config)
        reschedule_daily_job()
        flash("Settings saved and scheduler updated", "success")
        return redirect(url_for("settings"))
    return render_template("settings.html", config=config)


@app.route("/health")
def health():
    return {"ok": True, "time": now_iso()}


@app.template_filter("nl2br")
def nl2br(value):
    return (value or "").replace("\n", "<br>")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=os.getenv("APP_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("APP_PORT", "8508")))
    args = parser.parse_args()

    reschedule_daily_job()
    scheduler.start()
    print(f"Starting Instagram AI Daily app on http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False, use_reloader=False)
