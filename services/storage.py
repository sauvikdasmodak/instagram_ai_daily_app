import json
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
CONFIG_PATH = DATA_DIR / "config.json"
POSTS_PATH = DATA_DIR / "posts.json"


def load_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_config() -> dict:
    return load_json(CONFIG_PATH, {})


def save_config(config: dict) -> None:
    save_json(CONFIG_PATH, config)


def load_posts() -> list:
    return load_json(POSTS_PATH, [])


def save_posts(posts: list) -> None:
    save_json(POSTS_PATH, posts)


def add_post(post: dict) -> None:
    posts = load_posts()
    posts.insert(0, post)
    save_posts(posts)


def update_post(post_id: str, **updates: Any) -> dict | None:
    posts = load_posts()
    found = None
    for post in posts:
        if post.get("id") == post_id:
            post.update(updates)
            found = post
            break
    save_posts(posts)
    return found


def get_post(post_id: str) -> dict | None:
    for post in load_posts():
        if post.get("id") == post_id:
            return post
    return None
