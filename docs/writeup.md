# GenAI Fund outreach tool — write-up

## Approach

The brief's test is "if we can't use it to run outreach ourselves, it doesn't pass", so I ranked: works for real →
never double-messages → personalised with real evidence → polish. A narrow tool that is safe beat a wide one.

- **Finding people through GitHub, not X.** The X API has no free tier (user lookup $0.010, DM send $0.015). GitHub's
  official REST API is free, searches bios and locations (`in:bio`, `location:`), and many profiles list an X account.
  Builders also show their work there, so every reason in the rule-based fit score points at a bio line, a location
  or a real repository.
- **A person presses Send.** The tool reserves the message in SQLite (one atomic `UPDATE`, committed) *before* it
  shows the X link, copies the text and records the outcome. Sending through the X API is built as an option but
  limited to allowlisted accounts (see rules below).
- **Drafts from a template or a local model.** `template` quotes one verbatim sentence; Ollama runs a 4B model on the
  laptop. Real people's profiles go only to a local model or a paid API, never to a free cloud model whose terms let
  the provider read inputs. Every quote is checked word for word against its source; an unverified draft cannot be
  approved until a person rewrites it.

## Trade-offs

- **$0 and compliance, paid for with clicks.** Each message takes a copy, a click and a paste in X, plus a
  confirmation in the tool. Replies are marked by hand, because reading DMs through the API is paid.
- **Reach.** Only people who list an X handle on GitHub are found. In two real searches, 254 of 264 and 480 of 510
  GitHub accounts checked had none. That is the largest limit of this design.
- **Template drafts are safe but plain.** They never invent anything, but they read alike; the tool warns when two
  drafts are nearly the same.

## Platform rules and the tool's position

Cold outreach is a grey area on both platforms, and the tool is built to stay on the careful side of it.

- **X automation rules** forbid sending unsolicited DMs "in a bulk or automated manner". So the API channel only
  sends to accounts on `SEND_ALLOWLIST`, even in live mode; strangers can only be messaged by a person in X itself.
  The tool never automates x.com.
- **GitHub's Acceptable Use Policy** forbids using API data for spam and limits personal data to the purpose the user
  allowed. Someone who publishes an X handle on their profile can reasonably be contacted there, but it is not a
  clear licence.
- **Guards:** a person approves every message; one message per person, ever (database `UNIQUE` plus an atomic claim;
  an ambiguous API result becomes `unknown` and is never resent); a 20-per-24-hours cap; no follow-ups; a
  do-not-contact flag; an allowlist that is on by default.

## What comes next

Discovery through X API search (`search_recent` exists, not wired in) and through arXiv / OpenAlex; automatic reply
detection; follow-ups that a person schedules; multi-user deployment; a queued API send.

## Cost

$0 by default (GitHub, template or Ollama, manual sending). The X API channel costs about $0.035 per message: user
lookup $0.010 + conversation check $0.010 + send $0.015. Claude drafting is billed per token and recorded in the
`usage` table; it was not used in the live run, which cost $0.00 (the `usage` table stayed empty).

## How I used AI tools, and how the output was checked

Claude wrote the plan and reviewed every stage. Antigravity wrote the code for stages 1–2b; from stage 3 on (my
decision on 13 Nov) Claude wrote the code too. Each stage ended with a review by a fresh Claude subagent that had not
written that code: it read the diff, reran the tests, ran them again with the network blocked, and tried failure
cases. Those reviews sent stage 2 back (its live check had not been run), found a test that called the real network
(stage 3), and found 3 must-fix UI bugs in stage 6, among them a second browser tab silently clearing a
do-not-contact flag. Every fix came with a test that failed first. The suite has 140 tests and none touches the
network. Inside the product, the evidence check and the human approval step keep model output from going out
unchecked.
