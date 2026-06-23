# CX Tech N2 — Service Desk Dashboard

Streamlit dashboard for the CX Tech Level 2 team, pulling live data from Jira.

---

## Local setup (VSCode)

### 1. Clone or copy the repo to your machine

### 2. Create a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add your Jira credentials
```bash
cp .env.example .env
```
Edit `.env` and fill in your Jira email and API token.
Get a token at: https://id.atlassian.com/manage-profile/security/api-tokens

### 5. Run the app
```bash
streamlit run app.py
```

The dashboard opens at http://localhost:8501

---

## Deploying to Streamlit Community Cloud

### 1. Push the repo to GitHub (private repo is fine)
Make sure `.env` and `.streamlit/secrets.toml` are in `.gitignore` — they are already.

### 2. Go to https://share.streamlit.io
- Click **New app**
- Select your GitHub repo and branch
- Set **Main file path** to `app.py`
- Click **Deploy**

### 3. Add secrets (replaces .env in production)
Once deployed, go to **⋮ → Settings → Secrets** and add:
```toml
JIRA_EMAIL = "your.name@gympass.com"
JIRA_TOKEN = "your_jira_api_token_here"
```

### 4. Restrict access to your team
In the app settings, go to **Sharing** and set:
- **Who can view this app**: Specific people
- Add each teammate's `@gympass.com` email address

They'll be prompted to log in with their Google account before accessing the app.

---

## Updating the dashboard

1. Edit `app.py` in VSCode
2. `git add . && git commit -m "your message" && git push`
3. Streamlit Community Cloud redeploys automatically within ~30 seconds

---

## Repo structure

```
cx-n2-dashboard/
├── app.py              # Main dashboard
├── requirements.txt    # Python dependencies
├── .env.example        # Template for local credentials
├── .gitignore          # Keeps secrets out of git
└── README.md
```
