# X Social Outreach

A local tool that finds people building AI and robotics in Southeast Asia, drafts a personal intro message for each one
(quoting real evidence word for word), and sends it on X safely and within the platform's rules.

> The app's interface is in Vietnamese. This README names each control exactly as it appears on screen, with an
> English translation in parentheses the first time it appears.

---

## Highlights

- **Two workflow modes**, picked under **CHẾ ĐỘ LÀM VIỆC** (workflow mode) in the Streamlit sidebar:
  1. **Chế độ GitHub (miễn phí)** (GitHub mode, free, recommended): finds real people through the GitHub API (repositories,
     commits, a Southeast Asian location). Drafts quote their repository descriptions or bio. You press Send on X
     yourself, so it costs $0 and no DM is sent automatically.
  2. **Chế độ X gốc (có phí)** (X Native mode, paid, follows the brief literally): finds people on X (keywords in posts,
     and the networks of seed X accounts) and quotes their recent posts word for word. Sends DMs through the X API v2
     with an OAuth 2.0 connection (only to accounts in `SEND_ALLOWLIST`), then reads the DM inbox to see who replied.
     Needs an X developer account with prepaid API credit (see [Costs](#costs-and-paid-features)). **So far tested only
     with sample data and mocked X responses, never against the live X API.**
- **Switch the send channel at any time:** under **KÊNH GỬI (SEND CHANNEL)** in the sidebar, or with the one-click button at
  the top of the **Gửi tin** (Send) tab:
  - *Thủ công (Manual - $0)*: copy the message and open the recipient's X profile, then press Send yourself. Costs
    nothing.
  - *Tự động (X API v2)* (automatic): send directly through the X API v2 to accounts on the allowlist. Needs an X
    developer account with credit.
- **Personalized with evidence:** every draft quotes one checkable fact from the person's bio, repository or recent
  post. The quote must match its source word for word; if it does not, the draft cannot be approved.
- **Never messages anyone twice:** SQLite enforces it with a `UNIQUE(prospect_id)` constraint (one message per person)
  and by reserving the message in a single statement (`UPDATE ... WHERE status='approved'`). A double click or several
  browser tabs cannot send twice.
- **Safety limits built in:** a daily cap (default 20 per 24 hours), an allowlist (`SEND_MODE=allowlist`), and a
  "do not contact" switch that takes effect at once.
- **$0 by default (GitHub mode):** local SQLite storage, a free GitHub token, and template drafts (or a local Ollama
  model). Paid APIs (Claude, X API v2) are optional.
- **Starts empty:** a fresh clone has 0 campaigns, 0 prospects and 0 messages. The database is created on your
  machine on first run.
- **Tested:** 151 automated tests, all of which run with the network blocked.

---

## Requirements

- **Python** 3.11 or newer.
- **GitHub token (free):** a *fine-grained personal access token* with *Public repositories (read-only)* access.
- **OS:** Windows, macOS or Linux.
- **Drafting** (pick one in `.env`):
  - `template` (default, **$0**): a fixed message template with the verbatim quote filled in. No AI model needed.
  - `ollama` (**$0**, runs locally): uses [Ollama](https://ollama.com) (`ollama pull qwen3:4b`).
  - `anthropic` (paid cloud API): uses Claude through the Anthropic API.

---

## Quick start (under 5 minutes)

### 1. Get the code
```bash
git clone <repository-url> genaifund-outreach
cd genaifund-outreach
```
*(On Windows, use a short path such as `C:\projects\genaifund-outreach` to avoid the long-path limit during install.)*

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

### 4. Configure
Create `.env` from the template:
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

### 5. Check the setup
```bash
python -m outreach.doctor
```
Every line should show `PASS`. It never prints secret values.

### 6. Start the app
```bash
streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.

---

## Step-by-step use

Pick a mode under **CHẾ ĐỘ LÀM VIỆC** at the top of the sidebar. The four tabs are **Tìm người** (Find),
**Duyệt tin** (Review), **Gửi tin** (Send) and **Theo dõi** (Track).

### Mode 1: GitHub ($0, safe)
1. **Tìm người** (Find):
   - Create or pick a campaign under **Chiến dịch mới** (new campaign), for example with the keywords
     `robotics, machine learning`.
   - Press **Tìm trên GitHub** (search GitHub: each keyword in each Southeast Asian location), **Tìm người họ theo dõi**
     (who they follow: from a few seed GitHub accounts to their network), or **Thêm** (add GitHub accounts you already
     know).
   - Press **Chấm điểm** (score) to compute a rule-based fit score from real evidence (bio, repositories, activity,
     stars).
2. **Duyệt tin** (Review):
   - Choose how many drafts, then press **Soạn N bản nháp tiếp theo** (draft the next N).
   - Read each draft next to its evidence and the link to the source.
   - Edit if needed, then press **Duyệt** (approve) or **Từ chối** (reject). A quote that does not match its source
     cannot be approved.
3. **Gửi tin** (Send):
   - The top of the tab shows the current channel and a one-click switch: **Chuyển sang Tự động (X API)** (switch to
     API) or **Chuyển sang Thủ công ($0)** (switch to manual).
   - Each approved message offers both ways to send, ordered by the channel you picked:
     - **Manual channel:** **Bắt đầu gửi** (start sending) reserves the message in SQLite, copies the text and opens the
       recipient's X profile (**Mở @user trên X**). After sending on X, come back and press **Tôi đã gửi** (I sent it),
       **Chưa gửi** (not sent) or **Đã liên hệ từ trước** (already contacted before).
     - **API channel:** **Gửi qua X API** (send through the X API) sends directly to people in `SEND_ALLOWLIST`;
       **Tự tay gửi** (send by hand) uses the manual flow above.
   - **Từ chối** (reject) withdraws an approved message at any time before it is sent.
4. **Theo dõi** (Track):
   - Live counts: **Đã gửi** (sent), **Đã trả lời** (replied), **Tỉ lệ trả lời** (reply rate).
   - When someone replies, pick them under **Đánh dấu đã trả lời** (mark as replied) and note what they said; the
     message moves to **Cần xử lý** (needs attention).
   - When done, press **Đã xử lý xong** (handled), or turn on **Không liên hệ người này** (do not contact this person).

### Mode 2: X Native (paid, follows the brief)
Before a real run: create an X developer App with DM read/write permission and API credit, register
`http://127.0.0.1:8765/callback` as its callback URL, put `X_CLIENT_ID` / `X_CLIENT_SECRET` in `.env`, then press
**Kết nối tài khoản X** (connect X account) in the sidebar. The button shows in this mode whichever send channel you
pick, because searching X needs the login. Every X call below uses credit: see [Costs](#costs-and-paid-features).

1. **Find people on X:**
   - The search box is filled from the campaign keywords in X's query syntax, for example
     `("robotics" OR "embodied AI") -is:retweet`. Press **Tìm trên X** (search X: posts from the last 7 days and their
     authors).
   - Enter seed X accounts and press **Tìm người họ theo dõi trên X** (who they follow on X), or add accounts directly
     with **Thêm từ X** (add from X).
   - Press **Chấm điểm** (score) to rank by X bio and AI/robotics posts.
2. **Review:**
   - Drafts quote an X post or bio word for word, with a link to the checked evidence.
   - Edit if needed, then press **Duyệt** (approve).
3. **Send:**
   - **Gửi qua X API** sends from your connected account, but only to accounts in `SEND_ALLOWLIST` (X forbids
     automated unsolicited DMs). For anyone else, use the manual flow (**Bắt đầu gửi** or **Tự tay gửi**), as in mode 1.
4. **Track and fetch replies:**
   - Press **Lấy trả lời từ X** (fetch replies from X): the app reads the 100 newest DM events through the X API. If a
     recipient has written back, their message is marked replied and moves to **Cần xử lý** (needs attention). You can
     still use **Đánh dấu đã trả lời** (mark as replied) by hand.

## Try it without any keys (sample data)

1. In `.env`, set `X_MODE=fake` and `SEND_ALLOWLIST=alex_builder,sarah_robotics` (two people in the sample data).
2. Run `streamlit run app.py`. The sidebar shows `CHẾ ĐỘ THỬ (KHÔNG CẦN MẠNG)` (test mode, no network): sample GitHub and
   X profiles, template drafts, no network, no keys. Both modes work.
3. **Tìm người** → create a campaign with the keywords `robotics, robot learning` → `Tìm trên GitHub` (or `Tìm trên X`)
   → `Chấm điểm` · **Duyệt tin** → `Soạn N bản nháp tiếp theo` → `Duyệt` · **Gửi tin** → `Bắt đầu gửi` → `Tôi đã gửi`
   (or `Gửi qua X API`) · **Theo dõi** → `Đánh dấu đã trả lời` → `Đã xử lý xong`.

Sample data lives in `data/fake.db`; delete it to start over. Set `X_MODE=real` again for real data
(`data/outreach.db`).

## Contacting real people (`SEND_MODE=live`)

`SEND_MODE=allowlist` (the default) blocks everyone not in `SEND_ALLOWLIST`. Keep it while testing.

`SEND_MODE=live` allows sending to **any approved person, but only through the manual channel**: you still read and
approve every draft, press Send on X yourself, and stay under `DAILY_SEND_CAP` (default 20 messages per 24 hours).

The X API channel (in both modes) only ever sends to `SEND_ALLOWLIST`, even in live mode. X's automation rules forbid
automated DMs to people who have not agreed to be contacted, even when a person approved each message.

## Costs and paid features

GitHub mode + manual send + template drafts costs **$0**. Everything below is optional and paid. X prices are
per-resource estimates kept in `outreach/config.py` (`PRICES`: read a post $0.005, read a user $0.010, read a DM event
$0.010, send a DM $0.015); check X's current pricing before relying on them.

| Feature | Needs | Estimated cost | Status |
|---|---|---|---|
| X Native: Tìm trên X (search X) | X App + Kết nối tài khoản X | up to 10 posts + 10 authors ≈ $0.15 per click | Tested with sample data and mocks only |
| X Native: Tìm người họ theo dõi trên X (who they follow) | same | seed lookup $0.010 + up to 40 accounts × ($0.010 + 5 posts × $0.005) ≈ up to $1.41 per seed account | Tested with sample data and mocks only |
| X Native: Thêm từ X (add from X) | same | $0.010 + 5 posts × $0.005 = $0.035 per account | Tested with sample data and mocks only |
| Gửi qua X API (both modes) | X App + Kết nối tài khoản X | $0.025 per message (existing-conversation check $0.010 + send $0.015), plus $0.010 if the X user id is not known yet | Tested with mocks only. Sends to allowlisted accounts only |
| X Native: Lấy trả lời từ X (fetch replies) | same | up to 100 DM events × $0.010 = up to $1.00 per click | Tested with sample data and mocks only |
| Claude drafting | `LLM_PROVIDER=anthropic`, `ANTHROPIC_API_KEY`, `LLM_MODEL`, `LLM_PRICE_IN` / `LLM_PRICE_OUT` (USD per million tokens) | per token; the sidebar shows `Chi phí hôm nay` (today's cost) | Tested with mocks only |

Real people's profiles are only sent to a local model (Ollama) or a paid API (Anthropic). Free cloud models are left
out on purpose: their terms let the provider read your inputs.

## Limits and blocked actions

When the tool refuses something, it shows the reason in English, usually after `Không gửi được:` (cannot send). What
each reason means and what to do:

| Reason shown | Why | What to do |
|---|---|---|
| `not on SEND_ALLOWLIST (safety mode)` | `SEND_MODE=allowlist` is on | Add the person's X handle to `SEND_ALLOWLIST`, or switch to `SEND_MODE=live` (manual channel) |
| `daily cap reached (n/cap)` | `DAILY_SEND_CAP` messages were sent or are being sent in the last 24 hours | Wait, or raise `DAILY_SEND_CAP` |
| `marked do-not-contact` | You turned on "do not contact" for this person | Turn it off in **Theo dõi** if it was a mistake |
| `not approved` | Only approved messages can be sent | Approve it in **Duyệt tin** |
| `evidence not verified — edit the text first` | A quote in the draft does not match its source word for word | Compare the draft with the evidence and fix it; whether to approve is then your call |
| `existing conversation` | You pressed `Đã liên hệ từ trước`, or the API found an earlier conversation between you | Nothing: the tool will never message this person again |
| `api channel is limited to SEND_ALLOWLIST (X automation rules)` | See above | Use the manual channel |
| `recipient does not accept DMs from this account` | API channel: X says this person does not accept DMs from you | Skip this person |
| Status `unknown` under **Cần xử lý** | API channel: X did not answer in time, so the tool cannot tell whether the DM went out | Check the conversation on X, then press `Tin đã đi` (it was sent) or `Tin chưa đi` (it was not). The tool never resends by itself |
| GitHub rate limit, with a retry time | GitHub allows 30 searches per minute and 5,000 calls per hour per token | Wait until the time shown. People already found are kept |

Known limits:
- X Native mode has only run on sample data and mocked X responses, never against the live X API.
- GitHub mode only reaches people who list an X account on their GitHub profile. In two real searches, 254 of 264 and
  480 of 510 GitHub accounts checked had none.
- Searching X only sees posts from the last 7 days.
- `Lấy trả lời từ X` only detects the first reply to each message. If the person writes again after you pressed
  `Đã xử lý xong`, mark it with `Đánh dấu đã trả lời` by hand. Without that feature (mode 1), replies are always marked
  by hand.
- Quotes are at most 120 characters, cut at a word boundary, so they can stop mid-sentence. Fix them when you review.
- Only people with a fit score of 40 or more get a draft. There are no automatic follow-up messages.
- Both modes share one prospect list per campaign.
- A real GitHub search checks every account it finds and can take several minutes. The page shows no progress until
  it finishes.

---

## Running the tests

Run all 151 tests (no network needed):
```bash
pytest -q
```
Every test runs with network calls blocked, so results do not depend on outside services.

---

## Platform rules and why the tool is careful

Cold outreach touches platform rules, so the tool does the following:
1. **X automation rules:** X forbids sending DMs in bulk or automatically to people who did not ask for them.
   - **GitHub mode** keeps sending manual: $0, and a person presses Send for every DM.
   - **The X API channel** only sends automatically to accounts in `SEND_ALLOWLIST`, so it cannot message strangers in
     bulk by mistake.
2. **GitHub's Acceptable Use Policy:** GitHub API data is only used to contact relevant people in the field; no
   scraping, no spam.
3. **No invented facts:** every quote must appear word for word in the source repository or bio (`evidence_ok=1`);
   otherwise the app blocks approval until a person checks and fixes it.
4. **No duplicates, ever:** the messages table in SQLite has a `UNIQUE(prospect_id)` constraint. Nobody can receive
   two intro messages.

---

## Configuration (`.env`)

| Variable | Default | Meaning |
|:---|:---|:---|
| `X_MODE` | `real` | `real`: real GitHub and X APIs; `fake`: sample data, no network (for trying it out). |
| `GITHUB_TOKEN` | `""` | GitHub token (public repositories, read-only). |
| `SEND_CHANNEL` | `manual` | `manual` (copy the message and open X) or `api` (X API v2). Can be switched in the app. |
| `SEND_MODE` | `allowlist` | `allowlist` (only people in `SEND_ALLOWLIST` can receive messages) or `live`. |
| `SEND_ALLOWLIST` | `""` | Comma-separated X handles allowed to receive messages while testing. |
| `DAILY_SEND_CAP` | `20` | Maximum messages in the last 24 hours. |
| `LLM_PROVIDER` | `template` | `template` ($0), `ollama` ($0, local) or `anthropic` (paid API). |
| `OLLAMA_MODEL` | `qwen3:4b` | Ollama model name when `LLM_PROVIDER=ollama`. |
| `ANTHROPIC_API_KEY` | `""` | API key, required when `LLM_PROVIDER=anthropic`. |
| `LLM_MODEL`, `LLM_PRICE_IN`, `LLM_PRICE_OUT` | see `.env.example` | Claude model and its price in USD per million input / output tokens, for the cost log. |
| `X_CLIENT_ID` | `""` | OAuth 2.0 Client ID for the X API. |
| `X_CLIENT_SECRET` | `""` | OAuth 2.0 Client Secret for the X API. |
| `X_REDIRECT_URI` | `http://127.0.0.1:8765/callback` | Where X sends you back after login; must match the URI registered in the X Developer Portal. |

---

## Troubleshooting

| Symptom | Cause | Fix |
|:---|:---|:---|
| `X API error 402: Payment Required ("credits depleted")` | The X developer account has no credit left (about $0.015 per DM) | Add prepaid credit at [developer.x.com](https://developer.x.com), or switch to the manual channel (**Thủ công ($0)**) and send from the browser for free. |
| `doctor: Missing required configuration keys: GITHUB_TOKEN` | `.env` has no token | Add a valid GitHub token to `.env`. |
| `doctor: GitHub rejected GITHUB_TOKEN` | Wrong or expired token | Create a new one at [github.com/settings/tokens](https://github.com/settings/tokens). |
| `Không gửi được: not on SEND_ALLOWLIST (safety mode)` | The allowlist is on | Add the person's X handle to `SEND_ALLOWLIST` in `.env`. |
| `evidence not verified — edit the text first` | A quote does not match its source word for word | Edit the draft in **Duyệt tin** so it matches the evidence. |
| `daily cap reached` | The 24-hour cap is reached | Wait for the 24-hour window to pass, or change `DAILY_SEND_CAP` in `.env`. |
| `X_CLIENT_ID / X_CLIENT_SECRET are empty` | `.env` has no X App OAuth keys | Copy the Client ID and Client Secret (the App's *Keys and tokens* → OAuth 2.0) into `.env`, then restart the app. |
| X shows `You weren't able to give access to the App` | The X App is set up wrong | In the App's *User authentication settings*: turn on OAuth 2.0, type *Web App*, permission *Read and write and Direct message*, Callback URI exactly `http://127.0.0.1:8765/callback`. |
| `streamlit is not recognized` | The virtual environment is not active | Run `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (macOS/Linux). |

---

## Privacy and a clean start

- **A fresh clone starts empty:** `data/` and every `*.db` file are in `.gitignore`, so anyone who clones the repository
  starts with 0 campaigns, 0 prospects and 0 messages. `data/` and `outreach.db` are created on the first run.
- **Secrets stay local:** keys and tokens live only in `.env` on your machine and are never committed. The repository
  only holds the safe template `.env.example`.
- **No Streamlit telemetry:** usage statistics are turned off in `.streamlit/config.toml`.
