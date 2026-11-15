# GenAI Fund Outreach

A compliant, local-first tool for discovering AI and robotics builders in Southeast Asia, drafting warm personalized messages with verbatim evidence, and running safe outreach on X.

Built for the **GenAI Fund Forward Deployed Engineer (FDE) Take-Home Assignment**.

---

## Highlights

- **Dual-Mode Architecture:** Switch seamlessly on the Streamlit sidebar between:
  1. **🛡️ GitHub Builder Mode ($0 Cost & Platform-Safe — Recommended):** Finds authentic builders through the GitHub API (repositories, commits, SEA locations), crafts drafts quoting real code/repo descriptions, and uses a human-in-the-loop manual send ($0 cost, 100% compliant with X anti-bot rules).
  2. **⚡ X Native Mode (Official Take-Home Spec):** Discovers people directly on X (tweet keywords and X seed account networks), quotes recent posts/tweets verbatim, sends DMs automatically via the connected X API, and auto-syncs replies directly from the X DM inbox.
- **Evidence-Based Personalization:** Every draft quotes verifiable facts from the candidate's bio, repository, or recent post. Quotes must match source text word for word, or message approval is strictly blocked.
- **Never Double-Message Anyone:** Guaranteed by SQLite database constraints (`UNIQUE(prospect_id)`) and atomic status reservations (`UPDATE ... WHERE status='approved'`). Even parallel clicks or multiple browser tabs cannot trigger duplicate sends.
- **Built-in Safety & Limits:** Daily send cap (default: 20/day), safety allowlist (`SEND_MODE=allowlist`), and immediate `Do not contact` toggles.
- **Zero-Cost Default:** $0 operating cost with local SQLite storage, free GitHub API token, and built-in template drafting (or local Ollama). Optional paid APIs (Claude, X API v2) supported when configured.
- **Robust Test Coverage:** 146 automated tests passing offline with blocked network calls.

---

## System Requirements

- **Python:** 3.11 or newer.
- **GitHub Token (free):** Fine-grained personal access token with *Public repositories (read-only)* access.
- **Operating System:** Windows, macOS, or Linux.
- **Drafting Provider (choose one in `.env`):**
  - `template` (default, **$0**): Fixed message filled with verbatim evidence quote. No LLM needed.
  - `ollama` (**$0** local model): Runs locally via [Ollama](https://ollama.com) (`ollama pull qwen3:4b`).
  - `anthropic` (paid cloud API): Uses Claude via Anthropic API.

---

## Quickstart (Under 5 Minutes)

### 1. Clone the repository and enter the folder
```bash
git clone <repository-url> genaifund-outreach
cd genaifund-outreach
```
*(On Windows, use a short folder path such as `C:\projects\genaifund-outreach` to prevent path length limits).*

### 2. Create and activate a virtual environment
```bash
python -m venv .venv
```
- **Windows (PowerShell):** `.\.venv\Scripts\Activate.ps1`
- **macOS / Linux:** `source .venv/bin/activate`

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure your environment
Create your local `.env` file from the example:
- **Windows:** `copy .env.example .env`
- **macOS / Linux:** `cp .env.example .env`

Open `.env` and add your free GitHub token:
```env
X_MODE=real
GITHUB_TOKEN=github_pat_...
SEND_CHANNEL=manual
SEND_MODE=allowlist
SEND_ALLOWLIST=your_x_handle
DAILY_SEND_CAP=20
```

### 5. Run the diagnostic tool
Verify your setup in 2 seconds:
```bash
python -m outreach.doctor
```
Every line should display `PASS`.

### 6. Launch the Streamlit application
```bash
streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.

---

## Workflow Walkthrough

Use the **Workflow Mode** selector at the top of the sidebar to switch modes:

### Mode 1: 🛡️ GitHub Builder Mode ($0 & Safety)
1. **Find:**
   - Create or select a campaign (e.g., keywords: `robotics, machine learning`).
   - Click **Search GitHub** (scans keywords across Southeast Asian locations), **Seed GitHub accounts** (finds builder networks), or **Add GitHub accounts**.
   - Click **Score** to compute rule-based fit scores based on real evidence (bios, repositories, activity, stars).
2. **Review:**
   - Select batch size and click **Draft next N**.
   - Review drafts side-by-side with exact evidence sources and URLs.
   - Edit text if needed, then click **Approve** or **Reject**. Quotes not matching source text block approval.
3. **Send:**
   - Approved messages appear ready for delivery.
   - Click **Start**: the tool reserves the message atomically in SQLite, copies the message text to your clipboard, and provides a direct link to open the candidate's X profile.
   - Paste and send the message on X, then confirm: **I sent it**, **Not sent**, or **Already in contact**.
4. **Track:**
   - Live metrics: Sent count, Replied count, Reply rate.
   - Inbound replies: Click **Mark replied** with a conversation note to queue under **Needs attention**.
   - Resolve conversations with **Mark handled** or toggle **Do not contact**.

### Mode 2: ⚡ X Native Mode (Official Take-Home Spec)
1. **Find on X:**
   - Enter query keywords and click **Search on X** (fetches recent builder tweets and author bios).
   - Enter X seed handles and click **Find people they follow on X**.
   - Click **Score** to rank prospects based on their X bio and AI/robotics tweets.
2. **Review:**
   - Drafts quote the candidate's tweets or X bio verbatim with verified evidence links.
   - Edit and click **Approve**.
3. **Send via X API:**
   - Click **⚡ Send via X API** to dispatch direct messages automatically from your connected account.
4. **Track & Auto-Sync:**
   - Click **🔄 Sync Replies from X**: Automatically queries the X API DM inbox, detects replies, updates message records, and routes them to **Needs attention**.

---

## Test Suite

Run the full offline test suite (146 tests) to verify system integrity:
```bash
pytest -q
```
All unit and smoke tests run with network calls disabled to ensure strict isolation.

---

## Platform Compliance & Safety Rationale

Cold outreach operates in a sensitive regulatory and platform environment:
1. **X Automation Rules:** X strictly forbids unsolicited bulk or automated DMs. 
   - The **GitHub Builder Mode** keeps sending manual to ensure $0 cost and 100% platform safety for fund accounts.
   - The **X API Channel** restricts automated dispatch strictly to accounts listed in `SEND_ALLOWLIST`, preventing accidental mass messaging.
2. **GitHub Acceptable Use Policy:** GitHub API data is collected strictly for relevant ecosystem outreach without scraping or spamming.
3. **Anti-Hallucination Guard:** Language models cannot invent facts. Any quote generated must exist verbatim inside source repositories or bios (`evidence_ok=1`), or approval is rejected until human verification.
4. **Permanent Deduping:** Message records use a `UNIQUE(prospect_id)` constraint in SQLite. No prospect can ever receive a duplicate outreach message.

---

## Configuration Reference (`.env`)

| Variable | Default | Description |
|:---|:---|:---|
| `X_MODE` | `real` | `real` for live GitHub and X APIs; `fake` for offline unit testing. |
| `GITHUB_TOKEN` | `""` | GitHub Personal Access Token (read-only public repos). |
| `SEND_CHANNEL` | `manual` | `manual` (clipboard + profile link) or `api` (X API v2). |
| `SEND_MODE` | `allowlist` | `allowlist` (only `SEND_ALLOWLIST` can receive messages) or `live`. |
| `SEND_ALLOWLIST` | `""` | Comma-separated X handles permitted during testing. |
| `DAILY_SEND_CAP` | `20` | Maximum messages allowed within a rolling 24-hour window. |
| `LLM_PROVIDER` | `template` | `template` ($0), `ollama` ($0 local), or `anthropic` (paid API). |
| `OLLAMA_MODEL` | `qwen3:4b` | Ollama model name when `LLM_PROVIDER=ollama`. |
| `ANTHROPIC_API_KEY`| `""` | API key required when `LLM_PROVIDER=anthropic`. |
| `X_CLIENT_ID` | `""` | OAuth 2.0 Client ID for X API DM channel. |
| `X_CLIENT_SECRET` | `""` | OAuth 2.0 Client Secret for X API DM channel. |
| `X_REDIRECT_URI` | `http://127.0.0.1:8765/callback` | OAuth redirect URI registered in the X Developer Portal. |

---

## Troubleshooting

| Symptom | Cause | Solution |
|:---|:---|:---|
| `doctor: Missing required configuration keys: GITHUB_TOKEN` | Token missing in `.env` | Add a valid GitHub personal access token to `.env`. |
| `doctor: GitHub rejected GITHUB_TOKEN` | Invalid/expired token | Generate a new token at [github.com/settings/tokens](https://github.com/settings/tokens). |
| `Can't send: not on SEND_ALLOWLIST (safety mode)` | Safety allowlist active | Add the X username to `SEND_ALLOWLIST` in `.env`. |
| `evidence not verified — edit the text first` | Quoted evidence does not match source text verbatim | Edit the draft text in the Review tab to match the cited evidence. |
| `daily cap reached` | Hit rolling 24-hour send threshold | Wait for the window to reset, or adjust `DAILY_SEND_CAP` in `.env`. |
| `streamlit is not recognized` | Virtual environment inactive | Run `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (macOS/Linux). |

---

## Data Privacy & Storage

All data is stored exclusively on your local machine in SQLite (`data/outreach.db`). Credentials and tokens remain strictly inside `.env` and are never committed to version control. Streamlit telemetry is disabled via `.streamlit/config.toml`.
