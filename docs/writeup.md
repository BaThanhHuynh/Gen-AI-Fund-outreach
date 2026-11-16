# GenAI Fund outreach tool — write-up

## Approach

The brief's test is "if we can't use it to run outreach ourselves, it doesn't pass", so the order was: works for real
→ never double-messages → real evidence → polish.

- **Find people through GitHub, not X.** The X API has no free tier. GitHub's official API is free, searches bios and
  locations, and many profiles list an X account. Builders show their work there, so every reason in the rule-based
  fit score points at a bio line, a location or a real repository.
- **A person presses Send.** The tool reserves the message in SQLite (one atomic, committed `UPDATE`) before it shows
  the X link, then copies the text and records the outcome.
- **Template or local model drafts.** Every quote must match its source word for word, or the draft cannot be
  approved until a person rewrites it. Real profiles only go to a local model (Ollama) or a paid API, never to a free
  cloud model whose terms let the provider read inputs.
- **Dual-mode architecture.** To give evaluators the exact assignment spec alongside our production recommendation,
  the tool provides a sidebar switcher:
  1. *GitHub Builder Mode ($0 & Safety):* The zero-cost, compliant path described above.
  2. *X Native Mode (Literal Spec):* Direct discovery via X tweet search and X seed accounts, quoting X posts verbatim,
     X API sending (allowlisted accounts only; anyone else is sent by hand), and DM inbox reply sync. Paid per call,
     and so far run only on sample data and mocked X responses.

## Trade-offs

- **$0 and compliance cost clicks:** copy, open, paste, send, confirm; in GitHub mode replies are marked by hand,
  because reading DMs through the API is paid.
- **Reach:** only people who list an X handle on GitHub. In two real searches, 254 of 264 and 480 of 510 GitHub
  accounts checked had none. This is the design's biggest limit.
- **Template drafts never invent anything but read alike;** the tool warns when two are nearly the same.

## Platform rules and the tool's position

Cold outreach is a grey area on both platforms; the tool stays on the careful side.

- **X automation rules** forbid unsolicited DMs "in a bulk or automated manner". The optional X API channel therefore
  only sends to accounts on `SEND_ALLOWLIST`, even in live mode, and the tool never automates x.com.
- **GitHub's Acceptable Use Policy** forbids using API data for spam. A handle published on a profile invites contact,
  but it is not a clear licence.
- **Guards:** a person approves every message; one message per person, ever (database `UNIQUE` plus an atomic claim;
  an ambiguous API result becomes `unknown` and is never resent); 20 sends per 24 hours; no follow-ups; a
  do-not-contact flag; an allowlist on by default.

## What comes next

A first run of X Native mode against the live X API; arXiv / OpenAlex discovery; follow-ups a person schedules;
multi-user deployment; a queued API send.

## Cost

$0 by default (GitHub mode). The X API channel costs about $0.035 per message (user lookup $0.010 + conversation
check $0.010 + send $0.015). X Native mode, estimated from X's per-resource prices: about $0.15 per search, $0.035
per account added, up to $1.00 per reply sync. Claude drafting is billed per token and logged in the `usage` table. The live run cost $0.00: the table
stayed empty.

## How AI tools were used and checked

Claude wrote the plan and reviewed stages 1–2. Antigravity wrote stages 1–2b; from stage 3 Claude also wrote the code,
and each stage was reviewed by a fresh Claude subagent that had not written it: it read the diff and tried failure
cases, and from stage 4 it also reran the tests with the network blocked. These reviews sent stage 2 back (its live
check had not been run), caught a test that called the real network, and found 3 must-fix UI bugs, such as a second browser tab silently
clearing a do-not-contact flag. X Native mode was added last; a Claude review of it found a reply-sync crash, an X 400
on reading fewer than 5 posts, keywords joined with AND in the X search, and a hidden X connect button.
Every code fix came with a test that failed first. 151 tests, none touching the network.
In the product, the evidence check and human approval keep model output from going out unchecked. The live run sent
one real DM, to my own test account, which replied.
