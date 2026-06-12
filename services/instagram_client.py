from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class InstagramResult:
    ok: bool
    message: str
    data: dict[str, Any]


class InstagramClient:
    def __init__(self):
        self.access_token = os.getenv("IG_ACCESS_TOKEN", "").strip()
        self.ig_user_id = os.getenv("IG_USER_ID", "").strip()
        self.version = os.getenv("GRAPH_API_VERSION", "v25.0").strip() or "v25.0"
        self.base_url = f"https://graph.facebook.com/{self.version}"

    def ready(self) -> tuple[bool, str]:
        if not self.access_token:
            return False, "Missing IG_ACCESS_TOKEN in .env"
        if not self.ig_user_id:
            return False, "Missing IG_USER_ID in .env"
        return True, "Instagram API settings found"

    def create_media_container(self, image_url: str, caption: str) -> InstagramResult:
        ready, message = self.ready()
        if not ready:
            return InstagramResult(False, message, {})
        try:
            response = requests.post(
                f"{self.base_url}/{self.ig_user_id}/media",
                data={
                    "image_url": image_url,
                    "caption": caption,
                    "access_token": self.access_token,
                },
                timeout=60,
            )
            data = response.json()
            if not response.ok or "id" not in data:
                return InstagramResult(False, "Failed to create media container", data)
            return InstagramResult(True, "Media container created", data)
        except Exception as exc:
            return InstagramResult(False, f"Container error: {exc}", {})

    def publish_container(self, creation_id: str) -> InstagramResult:
        ready, message = self.ready()
        if not ready:
            return InstagramResult(False, message, {})
        try:
            response = requests.post(
                f"{self.base_url}/{self.ig_user_id}/media_publish",
                data={
                    "creation_id": creation_id,
                    "access_token": self.access_token,
                },
                timeout=60,
            )
            data = response.json()
            if not response.ok or "id" not in data:
                return InstagramResult(False, "Failed to publish media container", data)
            return InstagramResult(True, "Published to Instagram", data)
        except Exception as exc:
            return InstagramResult(False, f"Publish error: {exc}", {})

    def publish_image(self, image_url: str, caption: str) -> InstagramResult:
        container = self.create_media_container(image_url, caption)
        if not container.ok:
            return container
        # Small delay gives Meta time to process the media container.
        time.sleep(3)
        creation_id = container.data.get("id")
        return self.publish_container(creation_id)

    def check_account(self) -> InstagramResult:
        ready, message = self.ready()
        if not ready:
            return InstagramResult(False, message, {})
        try:
            response = requests.get(
                f"{self.base_url}/{self.ig_user_id}",
                params={"fields": "id,username,account_type,media_count", "access_token": self.access_token},
                timeout=30,
            )
            data = response.json()
            if not response.ok:
                return InstagramResult(False, "Account check failed", data)
            return InstagramResult(True, "Account connected", data)
        except Exception as exc:
            return InstagramResult(False, f"Account check error: {exc}", {})
