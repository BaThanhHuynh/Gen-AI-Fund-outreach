# Demo script (3–5 minutes)

Setup before recording: `.env` with `X_MODE=real`, `SEND_CHANNEL=manual`, `SEND_MODE=allowlist`,
`SEND_ALLOWLIST=<test account B>`, `LLM_PROVIDER=template`. App running (`streamlit run app.py`). Logged in to X as
account A in one browser tab, as B on a phone or second browser.

Start clean, because the live test run already used B (one message per person, ever):
- Rename `data/outreach.db` (it keeps the test run); the app creates an empty one.
- B must not have messaged A: delete the A–B conversation from the test run in both inboxes, or use a new test account B.

| # | Time | Show | Say |
|---|---|---|---|
| 1 | 0:00–0:30 | Terminal: `python -m outreach.doctor` (all `PASS`) | "One command checks the setup: GitHub token and send channel. The default GitHub mode needs no X API keys." |
| 2 | 0:30–1:10 | **Find**: campaign (segment, keywords such as `robotics, machine learning`), `Search GitHub`. Point at the counter "n people had no X handle" | "People come from GitHub's official API: bio keywords plus a Southeast Asian location. We only keep people who list an X account, and the tool says how many it dropped." |
| 3 | 1:10–1:50 | `Score`, then the profile table: score, category, reasons | "The score is rules, not a model. Every reason names its source: the bio, the location or a real repo." |
| 4 | 1:50–2:40 | **Review**: `Draft next N`. Open one draft: quote next to its source link. Edit a word and `Approve`. Then show a draft whose quote does not match its source: `Approve` refuses with `evidence not verified — edit the text first` | "Drafts must quote real evidence word for word. If a quote is not in the source, approving is blocked until a person rewrites it." |
| 5 | 2:40–3:30 | **Send**: B's message → `Start`. Copy button, `Open @B on X`, press Message, paste, send as A. Show B receiving it. Back in the app: `I sent it` | "The tool reserves the message before it opens X, so a double click cannot send twice. I press Send myself: that keeps us inside X's automation rules and costs nothing." |
| 6 | 3:30–3:50 | B is gone from **Review** and **Send**: the database keeps one message per person, so there is nothing to start again. Show a real person who is not on the allowlist: blocked with `not on SEND_ALLOWLIST (safety mode)`, no X link opened | "One message per person, ever. And while we test, only our own accounts can be contacted." |
| 7 | 3:50–4:20 | B replies on the phone. **Track** → `Mark replied` with a note → it appears under Needs attention → `Mark handled`. Point at sent / replied / reply rate and `Spend today: $0.00` | "Replies don't show up by themselves, because reading DMs through the API is paid. You mark them, and the tool keeps the list of what needs you." |
| 8 | 4:20–5:00 | Sidebar mode switcher → `⚡ X Native Mode`, then README's "Costs and paid features" table | "The sidebar switches to X Native mode, which follows the brief literally: search X, follow X seed accounts, send through the X API and sync replies from the DM inbox. Every call is paid, about 15 cents per search and up to a dollar per sync, and it has only run on sample data and mocks, so I demoed GitHub mode. Its limits are on purpose, to stay at zero dollars and inside X's rules. Only people who list an X handle on GitHub are reachable: in a real search, 480 of 510 had none. For people we don't know, a person presses Send; in both modes the API only sends to our allowlist, because X forbids automated unsolicited DMs. And in GitHub mode replies are marked by hand, as you saw." |

Notes for recording:
- Step 2: a real search can take several minutes with no progress shown. Run it before recording and cut the wait,
  or use `Add GitHub accounts` with a few logins.
- Step 4, refused approval: `template` drafts copy their quote straight from the source, so they always verify. An
  unverified quote only comes from a model (`ollama` / `anthropic`). If no draft on screen is unverified, show
  `python -m pytest -q tests/test_review.py -k approve_requires_verified_evidence` passing and the warning text in
  the Review tab code instead, and say so.
- Hide tokens: never open `.env` on screen; `doctor` prints no secret values.
- Blur or skip real people's names in step 2–3 if needed; do not message anyone except B.
