# Instagram AI Daily Post Scheduler

A local Flask app that generates daily AI-themed Instagram posts, creates a square JPG image, stores drafts, and can publish through the official Meta Instagram Graph API.

## What it does

- Generates AI topics and captions.
- Creates Instagram-ready 1080x1080 JPG images.
- Lets you edit and approve captions.
- Schedules daily post generation.
- Can publish to Instagram through the official Graph API.
- Runs without pandas, Streamlit, MoviePy, or browser automation.

## Important truth

Instagram does not support safe password-based automation. Do not build a bot that logs in with your Instagram password. Use Meta's official Instagram Graph API.

For API publishing, you need:

- Instagram professional account, usually Business or Creator depending on your Meta API setup.
- Meta developer app.
- Correct permissions such as `instagram_content_publish`.
- Long-lived access token.
- Instagram user ID.
- A public HTTPS URL for the generated JPG image.

Meta cannot fetch a file from `http://127.0.0.1`. Local preview works, but publishing requires a public image URL. Deploy the app or host the generated image folder publicly.

## Windows setup

```powershell
cd "$env:USERPROFILE\Downloads\instagram_ai_daily_app"
py -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
copy .env.example .env
python app.py --port 8508
```

Open:

```text
http://127.0.0.1:8508
```

## Configuration

Edit `.env`:

```env
IG_ACCESS_TOKEN=your_long_lived_token
IG_USER_ID=your_instagram_user_id
GRAPH_API_VERSION=v25.0
PUBLIC_MEDIA_BASE_URL=https://your-domain.com/static/generated
```

Optional OpenAI captions:

```env
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4.1-mini
```

The app works without an OpenAI key by using its built-in content generator.

## How publishing works

The app calls:

1. `POST /{ig-user-id}/media` with `image_url` and `caption`.
2. `POST /{ig-user-id}/media_publish` with the returned container ID.

## Safer workflow

Recommended setting:

- Auto-generate: ON
- Require manual approval: ON
- Auto-publish: OFF until your account and token are tested

After a week of reliable generation, you can decide whether to enable auto-publish.
