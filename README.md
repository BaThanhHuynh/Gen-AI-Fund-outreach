# GenAI Fund Outreach

A small local tool for finding AI and robotics builders in Southeast Asia and starting a conversation with them on X.

- **Find** people through the official GitHub API: by keywords in their bio and a Southeast Asian location, by
  seed accounts (people several seeds follow), or by GitHub username.
- **Explain** why each person fits with a rule-based score. Every reason points to real evidence: their bio,
  location or a repository.
- **Draft** a personal DM that quotes that evidence. A quote must match its source word for word, or the draft
  cannot be approved until a person edits it.
- **Send** only what a person approved. By default you press Send in X yourself; the tool copies the text, opens
  their X profile and records what you did.
- **Never double-message anyone.** One message per person, ever, enforced by the database.
- **Track** what was sent, who replied and what needs your attention.

Default cost: **$0**. Everything runs on your machine; the only data store is one SQLite file.

## Requirements

- Python 3.11 or newer.
- A free GitHub token (only for real searches; the sample-data mode needs no keys).
- For drafting, one of:
  - `template` (default, $0): a fixed message filled with one verbatim quote. No model needed.
  - `ollama` ($0): a local model through [Ollama](https://ollama.com). Install Ollama, then `ollama pull qwen3:4b`.
    Slow on small machines.
- Optional paid features are listed under [Optional paid features](#optional-paid-features).

## Install

1. Get the code and enter the folder. On Windows, use a short folder path (about 80 characters or less, such as
   `C:\Users\you\genaifund-outreach`): some installed files have very long names, and Windows refuses paths over 260
   characters unless long paths are enabled.
   ```bash
   git clone <this repository URL> genaifund-outreach
   cd genaifund-outreach
   ```
2. Create a virtual environment and activate it:
   ```bash
   python -m venv .venv
   ```
   Windows: `.venv\Scripts\activate` · macOS / Linux: `source .venv/bin/activate`
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create your settings file (Windows: `copy` instead of `cp`):
   ```bash
   cp .env.example .env
   ```
5. Check the setup. Every line should say `PASS`:
   ```bash
   python -m outreach.doctor
   ```

## Dual-Mode Architecture

The Streamlit app includes a **Workflow Mode** selector in the sidebar:

1. **🛡️ GitHub Builder Mode ($0 Cost & Safety - Practical Recommendation):**
   - Finds builders on GitHub (official API, $0, filtering SEA locations and repositories).
   - Quotes verified evidence from repos or bio.
   - Outreach is manual (opens X profile with copied text, preserving platform safety and costing $0).
   - Replies are tracked with manual confirmation.
2. **⚡ X Native Mode (Official Take-Home Spec):**
   - Discovers prospects directly on X via tweet searches and X seed accounts (`following`).
   - Quotes evidence verbatim from their recent X posts or bio.
   - Sends DMs automatically via connected X account / X API.
   - Automatically synchronizes incoming replies from X DM inbox with one click (`Sync Replies from X`).

Both modes run seamlessly in sample data mode (`X_MODE=fake`, $0, offline) and live mode.

## Try it without any keys (sample data)

The new `.env` starts with `X_MODE=fake`: fake GitHub profiles, template drafts, no network, no keys.

1. In `.env`, set `SEND_ALLOWLIST=alex_builder,sarah_robotics` (two of the sample people) so the send flow is not
   blocked by safety mode.
2. Start the app:
   ```bash
   streamlit run app.py
   ```
3. The sidebar says `SAMPLE DATA`. Walk through the tabs:
   **Find** → create a campaign with keywords `robotics, robot learning` (both people above then score 40 or more)
   → `Search GitHub` → `Score` ·
   **Review** → `Draft next N` → edit → `Approve` ·
   **Send** → `Start` → `I sent it` ·
   **Track** → `Mark replied` → `Mark handled`.

Sample data lives in `data/fake.db`. Delete that file to start over.

## Run it for real

1. Create a GitHub token at <https://github.com/settings/personal-access-tokens>: fine-grained, *Public
   repositories (read-only)*, no other permissions.
2. In `.env` set:
   ```
   X_MODE=real
   GITHUB_TOKEN=<your token>
   SEND_MODE=allowlist
   SEND_ALLOWLIST=<an X account you own, for testing>
   ```
3. Run `python -m outreach.doctor` again. It checks the token (and Ollama, when `LLM_PROVIDER=ollama`).
4. `streamlit run app.py`. The sidebar now says `LIVE`. Real data is kept in `data/outreach.db`.

How a send works (manual channel, the default):

1. **Send** tab → `Start`. The message is reserved first, so a second click or a second tab cannot send it again.
2. Copy the text with the copy button, click `Open @… on X`, press **Message** on their profile, paste, send.
3. Come back and confirm: `I sent it`, `Not sent` (frees the message, does not count toward the cap) or
   `Already in contact` (you had talked before; the message is blocked).

Replies do not appear automatically. When someone answers, use `Mark replied` in **Track**; it then shows under
**Needs attention** until you `Mark handled`.

## Contacting real people (`SEND_MODE=live`)

`SEND_MODE=allowlist` (the default) blocks everyone who is not in `SEND_ALLOWLIST`. Keep it while you test.

`SEND_MODE=live` lets you send to **any approved person, on the manual channel only**: you still read and approve
every draft and press Send in X yourself, within `DAILY_SEND_CAP` (default 20 per 24 hours).

The X API channel always stays limited to `SEND_ALLOWLIST`, even in live mode. X's automation rules forbid automated
DMs to people who have not asked to be contacted, even when a person approved each message.

## Optional paid features

| Feature | Setting | Cost | Status |
|---|---|---|---|
| Send through the X API | `SEND_CHANNEL=api`, `X_CLIENT_ID`, `X_CLIENT_SECRET`, then `python -m outreach.auth` to log in. Register `http://127.0.0.1:8765/callback` as the App's callback URL | X API credits: about $0.035 per message (user lookup $0.010 + conversation check $0.010 + send $0.015). Needs an X developer App with DM read/write permission | **Tested with mocks only.** Allowlisted recipients only |
| Draft with Claude | `LLM_PROVIDER=anthropic`, `ANTHROPIC_API_KEY`, `LLM_MODEL`, `LLM_PRICE_IN` / `LLM_PRICE_OUT` (USD per million tokens, from Anthropic's pricing page) | Per token; the sidebar shows `Spend today` | Tested with mocks only |

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
- Only people who list an X account on their GitHub profile can be found. In two real searches, 254 of 264 and 480
  of 510 GitHub accounts checked had none.
- Drafts quote at most 120 characters, cut at a word boundary, so a quote can end mid-sentence. Edit it in review.
- People need a fit score of at least 40 to get a draft.
- There are no automatic follow-ups and no automatic reply detection.
- A real search checks every GitHub account it finds and can take several minutes. The page shows no progress
  until it finishes.

## Troubleshooting

| Problem | Fix |
|---|---|
| `doctor` says `Missing required configuration keys: GITHUB_TOKEN` | Set `GITHUB_TOKEN` in `.env`, or go back to `X_MODE=fake` |
| `GitHub rejected GITHUB_TOKEN` | The token is wrong or expired; create a new one |
| `Ollama is not running at http://127.0.0.1:11434` | Start Ollama, or set `LLM_PROVIDER=template` |
| `Model qwen3:4b is not installed` | `ollama pull qwen3:4b`, or pick an installed model with `OLLAMA_MODEL` |
| Every send says `not on SEND_ALLOWLIST` | Expected in safety mode; see the table above |
| A manual send is stuck at `Waiting for you to send` | Confirm it with one of the three buttons, in **Send** or **Needs attention** |
| `streamlit` is not found | Activate the virtual environment first |
| `pip` stops with `OSError: [Errno 2] No such file or directory` and a hint about Windows Long Path support | The folder path is too long: clone into a shorter path, or [enable long paths](https://pip.pypa.io/warnings/enable-long-paths), then run `pip install -r requirements.txt` again |

## Where your data lives

Only on your machine, in one SQLite file: `data/outreach.db` (real) or `data/fake.db` (sample data). Keys live only in
`.env`; on the API channel, the X login tokens are also kept in the SQLite file. Both are excluded from git. Nothing
is sent anywhere except GitHub (search), X (only when you open a profile, or on the API channel) and the drafting
model you chose. Streamlit's usage statistics are switched off in `.streamlit/config.toml`.

## Tests

```bash
python -m pytest -q
```

The tests never touch the network: GitHub, X, Ollama and Claude are replaced by fakes.
