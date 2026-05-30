# Getting your Gmail OAuth credentials for GitHub Actions

You need three secrets: `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`.
This takes about 10 minutes to set up once.

---

## Step 1 — Create a Google Cloud project (skip if you already have one)

1. Go to https://console.cloud.google.com
2. Click the project dropdown at the top → **New Project**
3. Name it `japan-trip-poller` → **Create**

---

## Step 2 — Enable the Gmail API

1. In your new project, go to **APIs & Services → Library**
2. Search for **Gmail API** → click it → **Enable**

---

## Step 3 — Create OAuth credentials

1. Go to **APIs & Services → Credentials**
2. Click **+ Create Credentials → OAuth client ID**
3. If prompted, configure the consent screen first:
   - User type: **External** → Create
   - App name: `Japan Trip Poller`, your email, save and continue (skip scopes for now)
   - Add yourself as a **test user** → save
4. Back in Credentials → **+ Create Credentials → OAuth client ID**
   - Application type: **Desktop app**
   - Name: `Japan Trip Poller`
   - Click **Create**
5. Copy and save the **Client ID** and **Client Secret** — these are your first two secrets.

---

## Step 4 — Get a refresh token

The easiest way is the Google OAuth Playground:

1. Go to https://developers.google.com/oauthplayground
2. Click the gear icon (top right) → check **Use your own OAuth credentials**
3. Enter your Client ID and Client Secret → Close
4. In the left panel, scroll to find **Gmail API v1**, expand it
5. Check these scopes:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.labels`
   - `https://www.googleapis.com/auth/gmail.modify`
6. Click **Authorize APIs** → sign in with jacobreidroyston@gmail.com → Allow
7. Click **Exchange authorization code for tokens**
8. Copy the **Refresh token** — this is your third secret.

> The refresh token doesn't expire as long as the app is used at least once every 6 months.

---

## Step 5 — Add secrets to GitHub

Go to https://github.com/ser-duncan/japan-trip-ios/settings/secrets/actions

Add three secrets:

| Secret name           | Value                        |
|-----------------------|------------------------------|
| `GMAIL_CLIENT_ID`     | from Step 3                  |
| `GMAIL_CLIENT_SECRET` | from Step 3                  |
| `GMAIL_REFRESH_TOKEN` | from Step 4                  |

Also add (if not already set):

| Secret name              | Value                                                         |
|--------------------------|---------------------------------------------------------------|
| `ANTHROPIC_API_KEY`      | from console.anthropic.com → API Keys                        |
| `SUPABASE_ACCESS_TOKEN`  | from supabase.com/dashboard → account icon → Access Tokens   |

---

## Step 6 — Test it

Once secrets are added:

1. Go to https://github.com/ser-duncan/japan-trip-ios/actions
2. Click **Japan Trip Inbox Poller** in the left list
3. Click **Run workflow** → **Run workflow**
4. Watch the logs — should complete in under 2 minutes

After a successful manual run, the cron will fire automatically every 30 minutes.
