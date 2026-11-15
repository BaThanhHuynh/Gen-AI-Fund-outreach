"""GenAI Fund outreach: find people on GitHub, review drafted X messages, send them by hand, track replies.

Run: streamlit run app.py. Business rules live in outreach/; this file only shows data and calls those functions.
"""
import json
import re
from datetime import datetime, timezone

import streamlit as st

from outreach import auth, config, db, discover, fit, llm, review, sender, x_discover, x_sync
from outreach.github import GitHubError, GitHubRateLimited, get_github
from outreach.xclient import get_x

st.set_page_config(page_title="GenAI Fund outreach", layout="wide")
conn = db.connect()
if "recovered" not in st.session_state:  # once per browser session: API sends that never got an answer -> unknown
    st.session_state.recovered = sender.recover_stuck(conn)


def get_app_x(db_conn):
    """Return X client for current thread, sharing simulated inbox in session_state across reruns."""
    x = get_x(db_conn)
    if config.X_MODE == "fake":
        if "fake_inbox" not in st.session_state:
            st.session_state.fake_inbox = []
        x.inbox = st.session_state.fake_inbox
    return x


def rows(sql: str, *params) -> list:
    return conn.execute(sql, params).fetchall()


def act(fn, *args) -> None:
    """Run one button's action: show its error text, or rerun so every list shows the new state."""
    try:
        fn(*args)
    except Exception as e:  # SendBlocked / ValueError / X and auth errors: the person needs the reason, not a traceback
        st.error(str(e))
    else:
        st.rerun()


def manual_buttons(mid: int, where: str) -> None:
    for col, (label, outcome) in zip(st.columns(3), [("I sent it", "sent"), ("Not sent", "not_sent"),
                                                     ("Already in contact", "existing")]):
        if col.button(label, key=f"{where}_{outcome}_{mid}"):
            act(sender.confirm_manual, conn, mid, outcome)


SAFE_SOURCE = re.compile(r"bio|location|repo:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+|post:[A-Za-z0-9_.-]+")  # source ids come from a model


def source_url(login: str, source_id: str, x_username: str = "") -> str:
    if source_id.startswith("repo:"):
        return f"https://github.com/{source_id[5:]}"
    elif source_id.startswith("post:"):
        pid = source_id[5:]
        return f"https://x.com/{x_username}/status/{pid}" if x_username else f"https://x.com/i/web/status/{pid}"
    return f"https://github.com/{login}" if login else f"https://x.com/{x_username}"


def today_start_utc() -> str:
    midnight = datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
    return midnight.astimezone(timezone.utc).isoformat()


if note := st.session_state.pop("flash", None):
    st.info(note)

with st.sidebar:
    st.subheader("WORKFLOW MODE")
    mode = st.radio(
        "Approach",
        [
            "🛡️ GitHub Builder Mode ($0 Cost & Safety)",
            "⚡ X Native Mode (Official Take-Home Spec)",
        ],
        index=0,
        key="app_workflow_mode",
        help="Switch between zero-cost GitHub discovery ($0, platform-safe) and direct X-native discovery & automation."
    )
    is_x_native = mode.startswith("⚡")
    st.markdown("---")
    st.subheader("TEST MODE (OFFLINE)" if config.X_MODE == "fake" else "LIVE (REAL DATA)")
    if is_x_native:
        st.caption("Mode: Direct X Discovery & Automation")
        st.write("Channel: X API v2 (Direct)")
        me = db.kv_get(conn, "me")
        if me:
            st.write(f"Connected as @{me['username']}")
        elif st.button("Connect X account", key="connect_x_btn"):
            act(auth.login, conn)
    else:
        st.caption("Mode: GitHub Discovery & Manual Outreach")
        if config.SEND_CHANNEL == "manual":
            st.write("Channel: Manual — you send in X")
        else:
            st.write("Channel: X API")
            me = db.kv_get(conn, "me")
            if me:
                st.write(f"Connected as @{me['username']}")
            elif st.button("Connect X account", key="connect_x_btn"):
                act(auth.login, conn)
    if config.X_MODE == "fake" or config.LLM_PROVIDER == "template":
        writer = "template"
    else:
        writer = f"ollama: {config.OLLAMA_MODEL}" if config.LLM_PROVIDER == "ollama" else "anthropic"
    st.write(f"Drafts: {writer}")
    st.write(f"Sent in last 24h: {sender.sends_in_last_24h(conn)} / {config.DAILY_SEND_CAP}")
    if config.SEND_MODE == "allowlist":
        st.write("ALLOWLIST: only " + (", ".join(f"@{a}" for a in config.SEND_ALLOWLIST) or "nobody"))
    else:
        st.write("Send mode: LIVE")
    st.write(f"Spend today: ${db.spend_since(conn, today_start_utc()):.2f}")

find_tab, review_tab, send_tab, track_tab = st.tabs(["Find", "Review", "Send", "Track"])

with find_tab:
    camps = {c["id"]: c for c in rows("SELECT * FROM campaigns ORDER BY id DESC")}
    with st.expander("New campaign", expanded=not camps):
        name = st.text_input("Name", key="c_name")
        segment = st.text_area("Who are you looking for?", key="c_segment")
        keywords = st.text_input("Keywords, comma-separated (used to search and to score)", key="c_keywords")
        context = st.text_area("Sender context: who we are and what we want from the conversation", key="c_context")
        if st.button("Create campaign", key="c_create"):
            if all(v.strip() for v in (name, segment, keywords, context)):
                with conn:
                    conn.execute("INSERT INTO campaigns (name, segment, keywords, sender_context, created_at) "
                                 "VALUES (?, ?, ?, ?, ?)", (name.strip(), segment.strip(), keywords.strip(),
                                                            context.strip(), db.now()))
                st.rerun()
            st.error("Fill in all four fields.")
    cid = st.selectbox("Campaign", list(camps), format_func=lambda i: camps[i]["name"]) if camps else None

    if cid:
        def find_people(fn, *args) -> None:
            try:
                c = fn(conn, get_github(), cid, *args)
            except GitHubRateLimited as e:
                st.error("GitHub rate limit reached. People found so far are saved. Try again after "
                         f"{datetime.fromtimestamp(e.reset_at):%H:%M} (your local time).")
            except GitHubError as e:
                st.error(str(e))
            else:
                st.success(f"{c['new']} new, {c['existing']} already known, {c['no_x_handle']} people had no X "
                           f"handle ({c['checked']} GitHub accounts checked).")

        def logins(raw: str) -> list[str]:
            return [s.strip().lstrip("@") for s in raw.split(",") if s.strip()]

        if is_x_native:
            st.markdown("##### ⚡ Direct Discovery on X (Tweets & Bios)")
            st.caption("Search recent builder tweets, discover who X seed accounts follow, or import X handles.")
            x_query = st.text_input("Keywords on X (searches tweets & bios)",
                                    value=camps[cid]["keywords"], key="x_search_q")
            col_x1, _ = st.columns([1, 1])
            if col_x1.button("Search on X", key="x_search"):
                try:
                    c = x_discover.discover_by_x_search(conn, get_app_x(conn), cid, x_query, max_results=10)
                    st.success(f"{c['new']} new prospects, {c['existing']} already known ({c['checked']} X accounts checked).")
                except Exception as e:
                    st.error(f"X search failed: {e}")

            x_seeds = st.text_input("Seed X accounts (comma-separated, e.g. alex_builder, sarah_robotics)", key="x_seeds")
            if st.button("Find people they follow on X", key="x_seed_go") and logins(x_seeds):
                try:
                    c = x_discover.discover_by_x_seeds(conn, get_app_x(conn), cid, logins(x_seeds))
                    st.success(f"{c['new']} new prospects, {c['existing']} already known ({c['checked']} accounts checked).")
                except Exception as e:
                    st.error(f"X seed search failed: {e}")

            x_adds = st.text_input("Add X accounts (comma-separated)", key="x_adds")
            if st.button("Add on X", key="x_add_go") and logins(x_adds):
                try:
                    c = x_discover.import_x_usernames(conn, get_app_x(conn), cid, logins(x_adds))
                    st.success(f"{c['new']} new prospects, {c['existing']} already known ({c['checked']} accounts checked).")
                except Exception as e:
                    st.error(f"X import failed: {e}")

            if st.button("Score", key="score"):
                st.success(f"Scored {fit.score_campaign(conn, cid)} people based on X tweets & bio.")

            people = rows("SELECT * FROM prospects WHERE campaign_id = ? ORDER BY fit_score DESC, id", cid)
            if people:
                st.dataframe([{"X Profile": f"https://x.com/{p['x_username']}",
                               "Score": p["fit_score"],
                               "Type": p["fit_category"],
                               "Why / Evidence": "; ".join(r["claim"] for r in json.loads(p["fit_reasons"] or "[]"))}
                              for p in people],
                             column_config={"X Profile": st.column_config.LinkColumn()}, hide_index=True)
        else:
            phrases = [k.strip() for k in camps[cid]["keywords"].split(",") if k.strip()]
            st.caption(f"Search GitHub runs {len(discover.search_queries(phrases))} searches "
                       "(each keyword × each Southeast Asian location).")
            if st.button("Search GitHub", key="search"):
                find_people(discover.discover_by_segment, phrases)
            seeds = st.text_input("Seed GitHub accounts (comma-separated)", key="seeds")
            if st.button("Find people they follow", key="seed_go") and logins(seeds):
                find_people(discover.discover_by_seeds, logins(seeds))
            adds = st.text_input("Add GitHub accounts (comma-separated)", key="adds")
            if st.button("Add", key="add_go") and logins(adds):
                find_people(discover.import_logins, logins(adds))
            if st.button("Score", key="score"):
                st.success(f"Scored {fit.score_campaign(conn, cid)} people.")

            people = rows("SELECT * FROM prospects WHERE campaign_id = ? ORDER BY fit_score DESC, id", cid)
            if people:
                st.dataframe([{"GitHub": f"https://github.com/{p['github_login']}",
                               "X": f"https://x.com/{p['x_username']}", "Score": p["fit_score"],
                               "Type": p["fit_category"],
                               "Why": "; ".join(r["claim"] for r in json.loads(p["fit_reasons"] or "[]"))}
                              for p in people],
                             column_config={"GitHub": st.column_config.LinkColumn(),
                                            "X": st.column_config.LinkColumn()}, hide_index=True)

with review_tab:
    if not cid:
        st.info("Create a campaign in Find first.")
    else:
        n = st.number_input("How many drafts", min_value=1, max_value=50, value=5, key="draft_n")
        if st.button(f"Draft next {n}", key="draft"):
            bar, tried, drafter = st.progress(0.0, "Drafting…"), [], llm.get_drafter(conn)

            def draft_one(*args):  # moves the bar per person: a local model can take a minute per draft
                tried.append(1)
                bar.progress(min(len(tried) / n, 1.0), f"Drafting person {len(tried)}…")
                return drafter(*args)

            try:  # one pass, so a person whose draft failed is not retried (each call can be slow or paid)
                made = llm.draft_for_campaign(conn, draft_one, cid, limit=n)
            except Exception as e:  # Ollama down, Anthropic key or quota: stop the batch and say why
                st.error(f"Drafting stopped: {e}")
            else:
                st.success(f"{made} new drafts." if made else "Nobody left to draft (score below the minimum, "
                                                              "do-not-contact, or already has a message).")

        drafts = rows("SELECT m.*, p.name, p.github_login, p.x_username, p.bio, p.location, p.company, "
                      "p.fit_score, p.fit_category, p.fit_reasons FROM messages m "
                      "JOIN prospects p ON p.id = m.prospect_id "
                      "WHERE p.campaign_id = ? AND m.status IN ('draft', 'failed') "
                      "ORDER BY p.fit_score DESC, m.id", cid)
        texts = [d["text"] for d in drafts]
        for i, d in enumerate(drafts):
            mid = d["id"]
            with st.container(border=True):
                # plain text: profile fields are untrusted, and no X link before Start reserves the message
                st.text(f"{d['name'] or d['github_login'] or d['x_username']} · @{d['x_username']} · "
                        f"score {d['fit_score']} ({d['fit_category']})")
                if d['github_login']:
                    st.markdown(f"[GitHub profile](https://github.com/{d['github_login']})")
                st.text(" · ".join(x for x in (d["bio"], d["location"], d["company"]) if x))
                if d["status"] == "failed":
                    st.error(f"Sending failed: {d['error']}. Edit and approve again, or reject.")
                for r in json.loads(d["fit_reasons"] or "[]"):
                    st.text(f"• {r['claim']}")
                for ev in json.loads(d["evidence"]):
                    sid = str(ev.get("source_id"))
                    st.text(f"“{ev.get('quote')}”")
                    if SAFE_SOURCE.fullmatch(sid):
                        st.markdown(f"— [{sid}]({source_url(d['github_login'], sid, d['x_username'])})")
                    else:
                        st.text(f"— {sid}")
                text = st.text_area("Message", d["text"], key=f"text_{mid}")
                for problem in llm.draft_problems(text, texts[:i] + texts[i + 1:]):
                    st.warning(problem)
                if not d["evidence_ok"]:
                    st.warning("The quotes were not found in their sources. Edit the text before approving.")
                ok_col, no_col = st.columns(2)
                if ok_col.button("Approve", key=f"approve_{mid}"):
                    try:
                        if text.strip() != d["text"]:
                            review.set_text(conn, mid, text)
                        reason = review.approve(conn, mid)
                    except ValueError as e:
                        reason = str(e)
                    if reason:
                        st.error(reason)
                    else:
                        st.rerun()
                if no_col.button("Reject", key=f"reject_{mid}"):
                    act(review.reject, conn, mid)

with send_tab:
    approved = rows("SELECT m.id, m.text, p.x_username FROM messages m JOIN prospects p ON p.id = m.prospect_id "
                    "WHERE m.status = 'approved' ORDER BY m.id")
    if not approved:
        st.info("No approved messages.")
    for m in approved:
        mid = m["id"]
        with st.container(border=True):
            st.markdown(f"**@{m['x_username']}**")
            st.text(m["text"])
            reason = sender.check_can_send(conn, mid)
            if reason:
                st.caption(f"Can't send: {reason}")
            elif is_x_native:
                c_s1, c_s2, c_s3 = st.columns([2, 1, 1])
                if c_s1.button("⚡ Send via X API", key=f"api_{mid}"):
                    try:
                        st.session_state.flash = f"@{m['x_username']}: {sender.send_api(conn, get_app_x(conn), mid)}"
                    except Exception as e:
                        st.error(str(e))
                    else:
                        st.rerun()
                if c_s2.button("Send manual", key=f"start_{mid}"):
                    act(sender.open_manual, conn, mid)
                if c_s3.button("Reject", key=f"send_reject_{mid}"):
                    act(review.reject, conn, mid)
            elif config.SEND_CHANNEL == "manual":
                if st.button("Start", key=f"start_{mid}"):
                    act(sender.open_manual, conn, mid)
            elif st.button("Send via X API", key=f"api_{mid}"):
                try:
                    st.session_state.flash = f"@{m['x_username']}: {sender.send_api(conn, get_app_x(conn), mid)}"
                except Exception as e:  # SendBlocked reason, or the X error that stopped the pre-send checks
                    st.error(str(e))
                else:
                    st.rerun()
            if not is_x_native and st.button("Reject", key=f"send_reject_{mid}"):
                act(review.reject, conn, mid)

    waiting = rows("SELECT m.id, m.text, p.x_username FROM messages m JOIN prospects p ON p.id = m.prospect_id "
                   "WHERE m.status = 'sending' AND m.channel = 'manual' ORDER BY m.id")
    if waiting:
        st.subheader("Waiting for you to send")
    for m in waiting:
        with st.container(border=True):
            st.code(m["text"], language=None, wrap_lines=True)
            st.link_button(f"Open @{m['x_username']} on X", f"https://x.com/{m['x_username']}")
            st.write("Click Message on their profile, paste, send — then confirm below.")
            manual_buttons(m["id"], "send")

with track_tab:
    n_sent, n_replied = rows("SELECT COUNT(*), COUNT(replied_at) FROM messages WHERE status = 'sent'")[0]
    a, b, c = st.columns(3)
    a.metric("Sent", n_sent)
    b.metric("Replied", n_replied)
    c.metric("Reply rate", f"{n_replied / n_sent:.0%}" if n_sent else "—")

    if is_x_native:
        st.subheader("⚡ Auto-Sync Replies from X")
        st.caption("Fetch newest DM events via X API to automatically detect who replied and update tracking.")
        if st.button("🔄 Sync Replies from X", key="sync_x_replies_btn"):
            try:
                res = x_sync.sync_x_replies(conn, get_app_x(conn))
                if res.get("error"):
                    st.error(f"Sync error: {res['error']}")
                elif res["new_replies"] > 0:
                    st.success(f"Synced {res['new_replies']} new replies from: {', '.join(f'@{u}' for u in res['replied_users'])}!")
                    st.rerun()
                else:
                    st.info(f"Checked {res['checked_events']} DM events. No new replies found.")
            except Exception as e:
                st.error(f"Sync failed: {e}")
                if hasattr(fake_x, "simulate_reply"):
                    fake_x.simulate_reply(target["x_user_id"], "Excited to connect! Let's chat about AI & robotics.")
                    st.success(f"Simulated an incoming reply from @{target['x_username']}. Now click 'Sync Replies from X'!")

    handles = {p["id"]: p["x_username"] for p in rows("SELECT id, x_username FROM prospects")}
    st.subheader("Needs attention")
    items = sender.needs_attention(conn)
    if not items:
        st.success("Nothing needs your attention.")
    for m in items:
        mid = m["id"]
        with st.container(border=True):
            st.markdown(f"**@{handles[m['prospect_id']]}** · {m['status']} · {m['channel'] or ''}")
            for line in (m["error"], m["reply_text"] and f"Reply: {m['reply_text']}"):
                if line:
                    st.text(line)
            if m["status"] == "sending":
                manual_buttons(mid, "track")
            elif m["status"] == "unknown":
                st.write("X did not answer in time. Check your X inbox, then:")
                yes, no = st.columns(2)
                if yes.button("It was sent", key=f"was_sent_{mid}"):
                    act(sender.resolve_unknown, conn, mid, True)
                if no.button("It was not sent", key=f"was_not_sent_{mid}"):
                    act(sender.resolve_unknown, conn, mid, False)
            elif st.button("Mark handled", key=f"handled_{mid}"):
                act(sender.mark_handled, conn, mid)

    unreplied = rows("SELECT id, prospect_id FROM messages WHERE status = 'sent' AND replied_at IS NULL "
                     "ORDER BY sent_at DESC")
    if unreplied:
        st.subheader("Mark replied")
        who = {r["id"]: handles[r["prospect_id"]] for r in unreplied}
        pick = st.selectbox("Who replied?", list(who), format_func=lambda i: f"@{who[i]}", key="reply_pick")
        # keys per message: after a click the note box empties and a second click cannot hit the next person
        reply_note = st.text_input("Note: what they said", key=f"reply_note_{pick}")
        if st.button("Mark replied", key=f"reply_{pick}"):
            act(sender.mark_replied, conn, pick, reply_note)

    st.subheader("Send log")
    log = rows("SELECT p.x_username, m.status, m.channel, m.claimed_at, m.sent_at, m.replied_at, m.error "
               "FROM messages m JOIN prospects p ON p.id = m.prospect_id "
               "WHERE m.status IN ('sending', 'sent', 'failed', 'blocked', 'unknown') "
               "ORDER BY COALESCE(m.sent_at, m.claimed_at) DESC")
    if log:  # a statement, not a conditional expression: Streamlit "magic" would print the expression's value
        st.dataframe([dict(r) for r in log], hide_index=True)
    else:
        st.caption("Nothing sent yet.")

    st.subheader("Do not contact")
    dnc = {p["id"]: p for p in rows("SELECT id, x_username, do_not_contact FROM prospects ORDER BY x_username")}
    if dnc:
        pid = st.selectbox("Person", list(dnc), format_func=lambda i: f"@{dnc[i]['x_username']}", key="dnc_pick")
        cur = bool(dnc[pid]["do_not_contact"])  # in the key: a change from another tab rebuilds the toggle
        on = st.toggle("Do not contact", value=cur, key=f"dnc_{pid}_{int(cur)}")
        if on != cur:
            sender.set_do_not_contact(conn, pid, on)
            st.rerun()
