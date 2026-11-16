# GenAI Fund Outreach

A compliant, local-first tool for discovering AI and robotics builders in Southeast Asia, drafting warm personalized messages with verbatim evidence, and running safe outreach on X.

Built for the **GenAI Fund Forward Deployed Engineer (FDE) Take-Home Assignment**.

---

## Highlights

- **Dual-Mode Architecture:** Switch seamlessly on the Streamlit sidebar between:
  1. **🛡️ GitHub Builder Mode ($0 Cost & Platform-Safe — Recommended):** Finds authentic builders through the GitHub API (repositories, commits, SEA locations), crafts drafts quoting real code/repo descriptions, and uses a human-in-the-loop manual send ($0 cost; a person presses Send in X, so no automated DMs).
  2. **⚡ X Native Mode (Official Take-Home Spec):** Discovers people directly on X (tweet keywords and X seed account networks), quotes recent posts/tweets verbatim, sends DMs through the connected X API to accounts on `SEND_ALLOWLIST` (anyone else: manual send), and syncs replies from the X DM inbox. Needs a paid X developer App (see [Costs](#costs-and-paid-features)). **Tested with sample data and mocks only, not yet against the live X API.**
- **Evidence-Based Personalization:** Every draft quotes verifiable facts from the candidate's bio, repository, or recent post. Quotes must match source text word for word, or message approval is strictly blocked.
- **Never Double-Message Anyone:** Guaranteed by SQLite database constraints (`UNIQUE(prospect_id)`) and atomic status reservations (`UPDATE ... WHERE status='approved'`). Even parallel clicks or multiple browser tabs cannot trigger duplicate sends.
- **Built-in Safety & Limits:** Daily send cap (default: 20/day), safety allowlist (`SEND_MODE=allowlist`), and immediate `Do not contact` toggles.
- **Zero-Cost Default (GitHub mode):** $0 operating cost with local SQLite storage, free GitHub API token, and built-in template drafting (or local Ollama). Optional paid APIs (Claude, X API v2) supported when configured.
- **Robust Test Coverage:** 149 automated tests passing offline with blocked network calls.

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
Before you start (real mode): create an X developer App with DM read/write permission and API credits, register
`http://127.0.0.1:8765/callback` as its callback URL, put `X_CLIENT_ID` / `X_CLIENT_SECRET` in `.env`, then click
**Connect X account** in the sidebar. Every X call below costs credits: see [Costs](#costs-and-paid-features).

1. **Find on X:**
   - The search box is prefilled from the campaign keywords as an X query, e.g.
     `("robotics" OR "embodied AI") -is:retweet`. Click **Search on X** (posts from the last 7 days and their authors).
   - Enter X seed handles and click **Find people they follow on X**.
   - Click **Score** to rank prospects based on their X bio and AI/robotics tweets.
2. **Review:**
   - Drafts quote the candidate's tweets or X bio verbatim with verified evidence links.
   - Edit and click **Approve**.
3. **Send:**
   - **⚡ Send via X API** sends from your connected account, only to accounts on `SEND_ALLOWLIST` (X forbids
     automated DMs to people who did not ask for them). For anyone else use **Send manual**, as in Mode 1.
4. **Track & Sync:**
   - Click **🔄 Sync Replies from X**: reads the newest 100 DM events, marks a sent message as replied when its
     recipient wrote to you, and routes it to **Needs attention**. `Mark replied` still works by hand.

## Try it without any keys (sample data)

1. In `.env` set `X_MODE=fake` and `SEND_ALLOWLIST=alex_builder,sarah_robotics` (two of the sample people).
2. `streamlit run app.py`. The sidebar says `TEST MODE (OFFLINE)`: sample GitHub and X profiles, template drafts,
   no network, no keys. Both modes work.
3. **Find** → create a campaign with keywords `robotics, robot learning` → `Search GitHub` (or `Search on X`) →
   `Score` · **Review** → `Draft next N` → `Approve` · **Send** → `Start` → `I sent it` (or `⚡ Send via X API`) ·
   **Track** → `Mark replied` → `Mark handled`.

Sample data lives in `data/fake.db`; delete that file to start over. Set `X_MODE=real` again for live data
(`data/outreach.db`).

## Contacting real people (`SEND_MODE=live`)

`SEND_MODE=allowlist` (the default) blocks everyone who is not in `SEND_ALLOWLIST`. Keep it while you test.

`SEND_MODE=live` lets you send to **any approved person, on the manual channel only**: you still read and approve
every draft and press Send in X yourself, within `DAILY_SEND_CAP` (default 20 per 24 hours).

The X API channel (both modes) always stays limited to `SEND_ALLOWLIST`, even in live mode. X's automation rules
forbid automated DMs to people who have not asked to be contacted, even when a person approved each message.

## Costs and paid features

GitHub mode with the manual channel and template drafts costs **$0**. Everything below is optional and paid.
X prices are the per-resource estimates in `outreach/config.py` (`PRICES`: post read $0.005, user read $0.010,
DM event read $0.010, DM sent $0.015); check X's current pricing before you rely on them.

| Feature | Setting | Estimated cost | Status |
|---|---|---|---|
| X Native: Search on X | X App + Connect X account | up to 10 posts + 10 authors ≈ $0.15 per click | Sample data and mocks only |
| X Native: Find people they follow | same | seed lookup $0.010 + up to 40 accounts × ($0.010 + 5 posts × $0.005) ≈ up to $1.41 per seed | Sample data and mocks only |
| X Native: Add on X | same | $0.010 + 5 posts × $0.005 = $0.035 per account | Sample data and mocks only |
| Send through the X API (both modes) | Mode 2, or `SEND_CHANNEL=api` in Mode 1 | $0.025 per message (conversation check $0.010 + send $0.015), +$0.010 when the X user id is not known yet | Mocks only. Allowlisted recipients only |
| X Native: Sync Replies | same | up to 100 DM events × $0.010 = up to $1.00 per click | Sample data and mocks only |
| Draft with Claude | `LLM_PROVIDER=anthropic`, `ANTHROPIC_API_KEY`, `LLM_MODEL`, `LLM_PRICE_IN` / `LLM_PRICE_OUT` (USD per million tokens) | Per token; the sidebar shows `Spend today` | Mocks only |

Profiles of real people are sent only to a local model (Ollama) or to a paid API (Anthropic). Free cloud models are
not supported on purpose: their terms let the provider read what you send.

## Limits and blocked actions

When the tool refuses something it shows the reason. What each reason means and how to clear it:

| Shown reason | Why | What to do |
|---|---|---|
| `not on SEND_ALLOWLIST (safety mode)` | `SEND_MODE=allowlist` | Add the X username to `SEND_ALLOWLIST`, or switch to `SEND_MODE=live` (manual channel) |
| `daily cap reached (n/cap)` | `DAILY_SEND_CAP` messages already sent or in progress in the last 24 hours | Wait, or raise `DAILY_SEND_CAP` |
| `marked do-not-contact` | You switched on `Do not contact` for this person | Switch it off in **Track** if that was a mistake |
| `not approved` | Only approved messages can be sent | Approve it in **Review** |
| `evidence not verified — edit the text first` | A quote in the draft is not word for word in its source | Read the draft against the evidence and edit it; approving is then your call |
| `existing conversation` | You pressed `Already in contact`, or the API found an earlier conversation | None: the tool never messages that person again |
| `api channel is limited to SEND_ALLOWLIST (X automation rules)` | See above | Use the manual channel |
| `recipient does not accept DMs from this account` | API channel: X says their DMs are closed to you | Skip the person |
| Status `unknown` in **Needs attention** | API channel: X did not answer in time, so the tool cannot tell whether the DM went out | Check the conversation in X, then press `It was sent` or `It was not sent`. The tool never resends by itself |
| GitHub rate limit, with a retry time | GitHub allows 30 searches per minute and 5,000 calls per hour per token | Wait until the time shown. People already found are saved |

Known limits:
- X Native mode has run only on sample data and mocked X responses, never against the live X API.
- GitHub mode finds only people who list an X account on their GitHub profile. In two real searches, 254 of 264 and
  480 of 510 GitHub accounts checked had none.
- X search covers posts from the last 7 days only.
- Sync Replies detects the first reply to each message; a later reply after `Mark handled` needs `Mark replied` by hand.
  Without Sync (Mode 1), replies are always marked by hand.
- Drafts quote at most 120 characters, cut at a word boundary, so a quote can end mid-sentence. Edit it in review.
- People need a fit score of at least 40 to get a draft. There are no automatic follow-ups.
- Both modes share one prospect list per campaign.
- A real GitHub search checks every account it finds and can take several minutes. The page shows no progress
  until it finishes.

---

## Test Suite

Run the full offline test suite (149 tests) to verify system integrity:
```bash
pytest -q
```
All unit and smoke tests run with network calls disabled to ensure strict isolation.

---

## Platform Compliance & Safety Rationale

Cold outreach operates in a sensitive regulatory and platform environment:
1. **X Automation Rules:** X strictly forbids unsolicited bulk or automated DMs. 
   - The **GitHub Builder Mode** keeps sending manual: $0 cost, and a person presses Send for every DM.
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
