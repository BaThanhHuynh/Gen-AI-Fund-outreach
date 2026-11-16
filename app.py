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
    for col, (label, outcome) in zip(st.columns(3), [("Tôi đã gửi", "sent"), ("Chưa gửi", "not_sent"),
                                                     ("Đã liên hệ từ trước", "existing")]):
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
    st.subheader("CHẾ ĐỘ LÀM VIỆC")
    mode = st.radio(
        "Cách làm",
        [
            "Chế độ GitHub (miễn phí)",
            "Chế độ X gốc (có phí)",
        ],
        index=0,
        key="app_workflow_mode",
        help="Chuyển giữa tìm người qua GitHub (0 USD, an toàn với nền tảng) và tìm người, gửi tin trực tiếp trên X."
    )
    is_x_native = "X gốc" in mode

    st.markdown("---")
    st.subheader("KÊNH GỬI (SEND CHANNEL)")

    def set_send_channel(ch: str):
        config.SEND_CHANNEL = ch
        st.session_state.send_channel = ch
        st.session_state.app_send_channel_radio = ch

    if "app_send_channel_radio" not in st.session_state:
        st.session_state.app_send_channel_radio = st.session_state.get("send_channel", config.SEND_CHANNEL)

    def on_channel_radio_change():
        ch = st.session_state.app_send_channel_radio
        config.SEND_CHANNEL = ch
        st.session_state.send_channel = ch

    selected_channel = st.radio(
        "Phương thức gửi tin",
        ["manual", "api"],
        format_func=lambda c: "Thủ công (Manual - $0)" if c == "manual" else "Tự động (X API v2)",
        key="app_send_channel_radio",
        on_change=on_channel_radio_change,
        help="Thủ công: Tự copy tin nhắn và mở profile X để bấm gửi ($0, an toàn tuyệt đối). Tự động: Bắn trực tiếp qua X API (cần credit X)."
    )
    config.SEND_CHANNEL = selected_channel
    st.session_state.send_channel = selected_channel

    if selected_channel == "api":
        me = db.kv_get(conn, "me")
        if me:
            st.success(f"Đã kết nối X: @{me['username']}")
        elif st.button("Kết nối tài khoản X", key="connect_x_btn"):
            act(auth.login, conn)
    else:
        st.caption("Kênh thủ công: an toàn $0, không tốn phí X API")

    st.markdown("---")
    st.subheader("CHẾ ĐỘ THỬ (KHÔNG CẦN MẠNG)" if config.X_MODE == "fake" else "CHẠY THẬT (DỮ LIỆU THẬT)")
    if is_x_native:
        st.caption("Chế độ: tìm người và gửi tin trực tiếp trên X")
    else:
        st.caption("Chế độ: tìm người qua GitHub, trích dẫn repos")
    if config.X_MODE == "fake" or config.LLM_PROVIDER == "template":
        writer = "mẫu có sẵn (template)"
    else:
        writer = f"ollama: {config.OLLAMA_MODEL}" if config.LLM_PROVIDER == "ollama" else "anthropic"
    st.write(f"Soạn nháp bằng: {writer}")
    st.write(f"Đã gửi trong 24 giờ qua: {sender.sends_in_last_24h(conn)} / {config.DAILY_SEND_CAP}")
    if config.SEND_MODE == "allowlist":
        st.write("DANH SÁCH CHO PHÉP: chỉ " + (", ".join(f"@{a}" for a in config.SEND_ALLOWLIST) or "không ai"))
    else:
        st.write("Chế độ gửi: THẬT (live)")
    st.write(f"Chi phí hôm nay: ${db.spend_since(conn, today_start_utc()):.2f}")

find_tab, review_tab, send_tab, track_tab = st.tabs(["Tìm người", "Duyệt tin", "Gửi tin", "Theo dõi"])

with find_tab:
    camps = {c["id"]: c for c in rows("SELECT * FROM campaigns ORDER BY id DESC")}
    with st.expander("Chiến dịch mới", expanded=not camps):
        name = st.text_input("Tên", key="c_name")
        segment = st.text_area("Bạn đang tìm ai?", key="c_segment")
        keywords = st.text_input("Từ khoá, cách nhau bằng dấu phẩy (dùng để tìm và chấm điểm)", key="c_keywords")
        context = st.text_area("Giới thiệu người gửi: chúng ta là ai, muốn gì từ cuộc trò chuyện", key="c_context")
        if st.button("Tạo chiến dịch", key="c_create"):
            if all(v.strip() for v in (name, segment, keywords, context)):
                with conn:
                    conn.execute("INSERT INTO campaigns (name, segment, keywords, sender_context, created_at) "
                                 "VALUES (?, ?, ?, ?, ?)", (name.strip(), segment.strip(), keywords.strip(),
                                                            context.strip(), db.now()))
                st.rerun()
            st.error("Hãy điền đủ cả bốn ô.")
    cid = st.selectbox("Chiến dịch", list(camps), format_func=lambda i: camps[i]["name"]) if camps else None

    if cid:
        def find_people(fn, *args) -> None:
            try:
                c = fn(conn, get_github(), cid, *args)
            except GitHubRateLimited as e:
                st.error("GitHub đã chạm giới hạn số lần gọi. Những người tìm được đến giờ đã được lưu. Thử lại sau "
                         f"{datetime.fromtimestamp(e.reset_at):%H:%M} (giờ trên máy bạn).")
            except GitHubError as e:
                st.error(str(e))
            else:
                st.success(f"{c['new']} người mới, {c['existing']} người đã có, {c['no_x_handle']} người không có "
                           f"tài khoản X (đã kiểm {c['checked']} tài khoản GitHub).")

        def logins(raw: str) -> list[str]:
            return [s.strip().lstrip("@") for s in raw.split(",") if s.strip()]

        if is_x_native:
            st.markdown("##### Tìm người trực tiếp trên X (bài đăng và tiểu sử)")
            st.caption("Tìm bài đăng gần đây của người làm AI/robot, xem các tài khoản X gốc đang theo dõi ai, "
                       "hoặc thêm tài khoản X có sẵn.")
            x_query = st.text_input("Câu tìm kiếm trên X (cú pháp của X: OR giữa các cụm từ)",
                                    value=x_discover.search_query(camps[cid]["keywords"]), key="x_search_q")
            col_x1, _ = st.columns([1, 1])
            if col_x1.button("Tìm trên X", key="x_search"):
                try:
                    c = x_discover.discover_by_x_search(conn, get_app_x(conn), cid, x_query, max_results=10)
                    st.success(f"{c['new']} người mới, {c['existing']} người đã có (đã kiểm {c['checked']} tài khoản X).")
                except Exception as e:
                    st.error(f"Tìm trên X thất bại: {e}")

            x_seeds = st.text_input("Tài khoản X gốc (cách nhau bằng dấu phẩy, vd. alex_builder, sarah_robotics)",
                                    key="x_seeds")
            if st.button("Tìm người họ theo dõi trên X", key="x_seed_go") and logins(x_seeds):
                try:
                    c = x_discover.discover_by_x_seeds(conn, get_app_x(conn), cid, logins(x_seeds))
                    st.success(f"{c['new']} người mới, {c['existing']} người đã có (đã kiểm {c['checked']} tài khoản).")
                except Exception as e:
                    st.error(f"Tìm từ tài khoản X gốc thất bại: {e}")

            x_adds = st.text_input("Thêm tài khoản X (cách nhau bằng dấu phẩy)", key="x_adds")
            if st.button("Thêm từ X", key="x_add_go") and logins(x_adds):
                try:
                    c = x_discover.import_x_usernames(conn, get_app_x(conn), cid, logins(x_adds))
                    st.success(f"{c['new']} người mới, {c['existing']} người đã có (đã kiểm {c['checked']} tài khoản).")
                except Exception as e:
                    st.error(f"Thêm tài khoản X thất bại: {e}")

            if st.button("Chấm điểm", key="score"):
                st.success(f"Đã chấm điểm {fit.score_campaign(conn, cid)} người dựa trên bài đăng và tiểu sử X.")

            people = rows("SELECT * FROM prospects WHERE campaign_id = ? ORDER BY fit_score DESC, id", cid)
            if people:
                st.dataframe([{"Hồ sơ X": f"https://x.com/{p['x_username']}",
                               "Điểm": p["fit_score"],
                               "Loại": p["fit_category"],
                               "Lý do / bằng chứng": "; ".join(r["claim"] for r in json.loads(p["fit_reasons"] or "[]"))}
                              for p in people],
                             column_config={"Hồ sơ X": st.column_config.LinkColumn()}, hide_index=True)
        else:
            phrases = [k.strip() for k in camps[cid]["keywords"].split(",") if k.strip()]
            st.caption(f"«Tìm trên GitHub» chạy {len(discover.search_queries(phrases))} lượt tìm "
                       "(mỗi từ khoá × mỗi địa điểm ở Đông Nam Á).")
            if st.button("Tìm trên GitHub", key="search"):
                find_people(discover.discover_by_segment, phrases)
            seeds = st.text_input("Tài khoản GitHub gốc (cách nhau bằng dấu phẩy)", key="seeds")
            if st.button("Tìm người họ theo dõi", key="seed_go") and logins(seeds):
                find_people(discover.discover_by_seeds, logins(seeds))
            adds = st.text_input("Thêm tài khoản GitHub (cách nhau bằng dấu phẩy)", key="adds")
            if st.button("Thêm", key="add_go") and logins(adds):
                find_people(discover.import_logins, logins(adds))
            if st.button("Chấm điểm", key="score"):
                st.success(f"Đã chấm điểm {fit.score_campaign(conn, cid)} người.")

            people = rows("SELECT * FROM prospects WHERE campaign_id = ? ORDER BY fit_score DESC, id", cid)
            if people:
                st.dataframe([{"GitHub": f"https://github.com/{p['github_login']}",
                               "X": f"https://x.com/{p['x_username']}", "Điểm": p["fit_score"],
                               "Loại": p["fit_category"],
                               "Lý do": "; ".join(r["claim"] for r in json.loads(p["fit_reasons"] or "[]"))}
                              for p in people],
                             column_config={"GitHub": st.column_config.LinkColumn(),
                                            "X": st.column_config.LinkColumn()}, hide_index=True)

with review_tab:
    if not cid:
        st.info("Hãy tạo chiến dịch ở tab «Tìm người» trước.")
    else:
        n = st.number_input("Số bản nháp", min_value=1, max_value=50, value=5, key="draft_n")
        if st.button(f"Soạn {n} bản nháp tiếp theo", key="draft"):
            bar, tried, drafter = st.progress(0.0, "Đang soạn…"), [], llm.get_drafter(conn)

            def draft_one(*args):  # moves the bar per person: a local model can take a minute per draft
                tried.append(1)
                bar.progress(min(len(tried) / n, 1.0), f"Đang soạn cho người thứ {len(tried)}…")
                return drafter(*args)

            try:  # one pass, so a person whose draft failed is not retried (each call can be slow or paid)
                made = llm.draft_for_campaign(conn, draft_one, cid, limit=n)
            except Exception as e:  # Ollama down, Anthropic key or quota: stop the batch and say why
                st.error(f"Dừng soạn nháp: {e}")
            else:
                st.success(f"{made} bản nháp mới." if made else "Không còn ai để soạn nháp (điểm dưới mức tối thiểu, "
                                                                "đã đánh dấu không liên hệ, hoặc đã có tin nhắn).")

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
                        f"điểm {d['fit_score']} ({d['fit_category']})")
                if d['github_login']:
                    st.markdown(f"[Hồ sơ GitHub](https://github.com/{d['github_login']})")
                st.text(" · ".join(x for x in (d["bio"], d["location"], d["company"]) if x))
                if d["status"] == "failed":
                    st.error(f"Gửi thất bại: {d['error']}. Sửa rồi duyệt lại, hoặc từ chối.")
                for r in json.loads(d["fit_reasons"] or "[]"):
                    st.text(f"• {r['claim']}")
                for ev in json.loads(d["evidence"]):
                    sid = str(ev.get("source_id"))
                    st.text(f"“{ev.get('quote')}”")
                    if SAFE_SOURCE.fullmatch(sid):
                        st.markdown(f"— [{sid}]({source_url(d['github_login'], sid, d['x_username'])})")
                    else:
                        st.text(f"— {sid}")
                text = st.text_area("Tin nhắn", d["text"], key=f"text_{mid}")
                for problem in llm.draft_problems(text, texts[:i] + texts[i + 1:]):
                    st.warning(problem)
                if not d["evidence_ok"]:
                    st.warning("Không tìm thấy câu trích trong nguồn của nó. Hãy sửa nội dung trước khi duyệt.")
                ok_col, no_col = st.columns(2)
                if ok_col.button("Duyệt", key=f"approve_{mid}"):
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
                if no_col.button("Từ chối", key=f"reject_{mid}"):
                    act(review.reject, conn, mid)

with send_tab:
    # Quick channel status and switcher
    col_mode_info, col_toggle = st.columns([3, 2])
    with col_mode_info:
        st.markdown(f"**Kênh gửi đang chọn:** {'**Tự động (X API v2)**' if config.SEND_CHANNEL == 'api' else '**Thủ công ($0 - Copy & Mở X)**'}")
    with col_toggle:
        if config.SEND_CHANNEL == "manual":
            st.button("Chuyển sang Tự động (X API)", key="quick_switch_to_api", on_click=set_send_channel, args=("api",))
        else:
            st.button("Chuyển sang Thủ công ($0)", key="quick_switch_to_manual", on_click=set_send_channel, args=("manual",))

    approved = rows("SELECT m.id, m.text, p.x_username FROM messages m JOIN prospects p ON p.id = m.prospect_id "
                    "WHERE m.status = 'approved' ORDER BY m.id")
    if not approved:
        st.info("Chưa có tin nhắn nào được duyệt.")
    for m in approved:
        mid = m["id"]
        with st.container(border=True):
            st.markdown(f"**@{m['x_username']}**")
            st.text(m["text"])
            reason = sender.check_can_send(conn, mid)
            if reason:
                st.caption(f"Không gửi được: {reason}")
            elif config.SEND_CHANNEL == "api":
                c_s1, c_s2 = st.columns([2, 1])
                if c_s1.button("Gửi qua X API", key=f"api_{mid}"):
                    try:
                        st.session_state.flash = f"@{m['x_username']}: {sender.send_api(conn, get_app_x(conn), mid)}"
                    except Exception as e:
                        st.error(str(e))
                    else:
                        st.rerun()
                if c_s2.button("Tự tay gửi", key=f"start_{mid}"):
                    act(sender.open_manual, conn, mid)
            else:  # config.SEND_CHANNEL == "manual"
                c_s1, c_s2 = st.columns([2, 1])
                if c_s1.button("Bắt đầu gửi", key=f"start_{mid}"):
                    act(sender.open_manual, conn, mid)
                if c_s2.button("Gửi qua X API", key=f"api_{mid}"):
                    try:
                        st.session_state.flash = f"@{m['x_username']}: {sender.send_api(conn, get_app_x(conn), mid)}"
                    except Exception as e:
                        st.error(str(e))
                    else:
                        st.rerun()

            if st.button("Từ chối", key=f"send_reject_{mid}"):
                act(review.reject, conn, mid)

    waiting = rows("SELECT m.id, m.text, p.x_username FROM messages m JOIN prospects p ON p.id = m.prospect_id "
                   "WHERE m.status = 'sending' AND m.channel = 'manual' ORDER BY m.id")
    if waiting:
        st.subheader("Đang chờ bạn gửi")
    for m in waiting:
        with st.container(border=True):
            st.code(m["text"], language=None, wrap_lines=True)
            st.link_button(f"Mở @{m['x_username']} trên X", f"https://x.com/{m['x_username']}")
            st.write("Bấm nút Message (Nhắn tin) trên trang của họ, dán tin, gửi — rồi xác nhận bên dưới.")
            manual_buttons(m["id"], "send")

with track_tab:
    n_sent, n_replied = rows("SELECT COUNT(*), COUNT(replied_at) FROM messages WHERE status = 'sent'")[0]
    a, b, c = st.columns(3)
    a.metric("Đã gửi", n_sent)
    b.metric("Đã trả lời", n_replied)
    c.metric("Tỉ lệ trả lời", f"{n_replied / n_sent:.0%}" if n_sent else "—")

    if is_x_native:
        st.subheader("Tự lấy câu trả lời từ X")
        st.caption("Đọc các tin nhắn riêng (DM) mới nhất qua X API để tự biết ai đã trả lời và cập nhật bảng theo dõi.")
        if st.button("Lấy trả lời từ X", key="sync_x_replies_btn"):
            try:
                res = x_sync.sync_x_replies(conn, get_app_x(conn))
                if res.get("error"):
                    st.error(f"Lỗi khi lấy trả lời: {res['error']}")
                elif res["new_replies"] > 0:
                    st.success(f"Có {res['new_replies']} trả lời mới từ: {', '.join(f'@{u}' for u in res['replied_users'])}.")
                    st.rerun()
                else:
                    st.info(f"Đã kiểm {res['checked_events']} tin nhắn DM. Chưa có trả lời mới.")
            except Exception as e:
                st.error(f"Lấy trả lời thất bại: {e}")

    handles = {p["id"]: p["x_username"] for p in rows("SELECT id, x_username FROM prospects")}
    st.subheader("Cần xử lý")
    items = sender.needs_attention(conn)
    if not items:
        st.success("Không có gì cần bạn xử lý.")
    for m in items:
        mid = m["id"]
        with st.container(border=True):
            st.markdown(f"**@{handles[m['prospect_id']]}** · {m['status']} · {m['channel'] or ''}")
            for line in (m["error"], m["reply_text"] and f"Trả lời: {m['reply_text']}"):
                if line:
                    st.text(line)
            if m["status"] == "sending":
                manual_buttons(mid, "track")
            elif m["status"] == "unknown":
                st.write("X không phản hồi kịp. Hãy xem hộp thư X của bạn, rồi chọn:")
                yes, no = st.columns(2)
                if yes.button("Tin đã đi", key=f"was_sent_{mid}"):
                    act(sender.resolve_unknown, conn, mid, True)
                if no.button("Tin chưa đi", key=f"was_not_sent_{mid}"):
                    act(sender.resolve_unknown, conn, mid, False)
            elif st.button("Đã xử lý xong", key=f"handled_{mid}"):
                act(sender.mark_handled, conn, mid)

    unreplied = rows("SELECT id, prospect_id FROM messages WHERE status = 'sent' AND replied_at IS NULL "
                     "ORDER BY sent_at DESC")
    if unreplied:
        st.subheader("Đánh dấu đã trả lời")
        who = {r["id"]: handles[r["prospect_id"]] for r in unreplied}
        pick = st.selectbox("Ai đã trả lời?", list(who), format_func=lambda i: f"@{who[i]}", key="reply_pick")
        # keys per message: after a click the note box empties and a second click cannot hit the next person
        reply_note = st.text_input("Ghi chú: họ đã nói gì", key=f"reply_note_{pick}")
        if st.button("Đánh dấu đã trả lời", key=f"reply_{pick}"):
            act(sender.mark_replied, conn, pick, reply_note)

    st.subheader("Nhật ký gửi")
    log = rows('SELECT p.x_username AS "Tài khoản X", m.status AS "Trạng thái", m.channel AS "Kênh", '
               'm.claimed_at AS "Bắt đầu lúc", m.sent_at AS "Gửi lúc", m.replied_at AS "Trả lời lúc", '
               'm.error AS "Lỗi" '
               "FROM messages m JOIN prospects p ON p.id = m.prospect_id "
               "WHERE m.status IN ('sending', 'sent', 'failed', 'blocked', 'unknown') "
               "ORDER BY COALESCE(m.sent_at, m.claimed_at) DESC")
    if log:  # a statement, not a conditional expression: Streamlit "magic" would print the expression's value
        st.dataframe([dict(r) for r in log], hide_index=True)
    else:
        st.caption("Chưa gửi tin nào.")

    st.subheader("Không liên hệ")
    dnc = {p["id"]: p for p in rows("SELECT id, x_username, do_not_contact FROM prospects ORDER BY x_username")}
    if dnc:
        pid = st.selectbox("Người", list(dnc), format_func=lambda i: f"@{dnc[i]['x_username']}", key="dnc_pick")
        cur = bool(dnc[pid]["do_not_contact"])  # in the key: a change from another tab rebuilds the toggle
        on = st.toggle("Không liên hệ người này", value=cur, key=f"dnc_{pid}_{int(cur)}")
        if on != cur:
            sender.set_do_not_contact(conn, pid, on)
            st.rerun()
