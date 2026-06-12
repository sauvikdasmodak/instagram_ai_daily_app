# Azure deployment for instagram_ai_daily_app

## 1. Create GitHub Actions variables

Repository > Settings > Secrets and variables > Actions > Variables:

- AZURE_RESOURCE_GROUP = rg-instagram-ai-daily
- AZURE_LOCATION = canadacentral
- AZURE_APP_SERVICE_PLAN = asp-instagram-ai-daily
- AZURE_WEBAPP_NAME = instagram-ai-daily-sauvik
- OPENAI_MODEL = gpt-4.1-mini
- GRAPH_API_VERSION = v25.0

The web app name must be globally unique. If `instagram-ai-daily-sauvik` is taken, use another name.

## 2. Create GitHub Actions secrets

Repository > Settings > Secrets and variables > Actions > Secrets:

- AZURE_CLIENT_ID
- AZURE_TENANT_ID
- AZURE_SUBSCRIPTION_ID
- FLASK_SECRET_KEY
- OPENAI_API_KEY
- IG_ACCESS_TOKEN
- IG_USER_ID

## 3. Create Azure federated identity for GitHub Actions

In Azure Cloud Shell, replace subscription values and run:

```bash
az ad app create --display-name instagram-ai-daily-github-actions
APP_ID=$(az ad app list --display-name instagram-ai-daily-github-actions --query '[0].appId' -o tsv)
az ad sp create --id $APP_ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
az role assignment create --assignee $APP_ID --role Contributor --scope /subscriptions/$SUBSCRIPTION_ID

az ad app federated-credential create --id $APP_ID --parameters '{
  "name": "github-main",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:sauvikdasmodak/instagram_ai_daily_app:ref:refs/heads/main",
  "description": "GitHub Actions deployment from main branch",
  "audiences": ["api://AzureADTokenExchange"]
}'

echo "AZURE_CLIENT_ID=$APP_ID"
echo "AZURE_SUBSCRIPTION_ID=$SUBSCRIPTION_ID"
az account show --query tenantId -o tsv
```

Use the output values in the GitHub secrets.

## 4. Add files to repo

Copy `startup.sh` to the repo root.
Copy `.github/workflows/azure-webapp.yml` into `.github/workflows/`.

Commit and push to `main`. The workflow will create the Azure resources and deploy the app.

## 5. Verify

Open:

- https://YOUR_WEBAPP_NAME.azurewebsites.net
- https://YOUR_WEBAPP_NAME.azurewebsites.net/health

## Notes

- The app uses the scheduler inside `app.py`, so the Azure startup command runs `startup.sh`, which runs `python app.py`.
- Use the B1 plan or higher. Free tier can sleep, which breaks daily scheduling reliability.
- Instagram publishing requires that generated images be accessible via public HTTPS. The pipeline sets `PUBLIC_MEDIA_BASE_URL` to the Azure static generated image folder.
