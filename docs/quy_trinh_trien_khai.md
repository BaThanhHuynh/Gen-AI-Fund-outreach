# Quy trình triển khai — Công cụ tìm người và nhắn tin trên X cho GenAI Fund

> **Dành cho Antigravity và người điều khiển nó.** Mỗi lần chỉ làm **một giai đoạn** theo vòng 4 bước ở
> mục 0, rồi **dừng** để Claude rà soát. Ô `- [ ]` dùng để đánh dấu tiến độ.

**Mục tiêu:** Một công cụ GenAI Fund tự chạy được trên máy mình: tìm người làm AI / robotics trên X, giải
thích vì sao họ hợp, soạn tin nhắn riêng dựa trên bằng chứng thật để người duyệt, gửi tin đã duyệt qua X API
chính thức, không bao giờ nhắn trùng, và cho thấy đã gửi gì, ai trả lời, việc gì cần xử lý.

**Kiến trúc:** Một ứng dụng Streamlit chạy cục bộ, một tệp SQLite là nguồn sự thật duy nhất. Giao diện chỉ
gọi hàm trong gói `outreach/`. Mọi luật an toàn (chống trùng, trần gửi, danh sách cho phép) nằm ở ràng buộc
của cơ sở dữ liệu và ở `sender.py`, không nằm ở giao diện. `XClient` (thật) và `FakeXClient` (giả lập) có
cùng phương thức, nên test và chế độ dùng thử không bao giờ ra mạng.

**Công nghệ:** Python ≥ 3.11 · Streamlit · `sqlite3` (thư viện chuẩn) · httpx · anthropic · python-dotenv ·
pytest. Không thêm thư viện nào khác khi chưa hỏi.

**Đề bài:** `docs/assignment.md` (bản sao nguyên văn). **Hạn nộp: Thứ Ba 17/11/2026, 12:00 (GMT+7).**

---

## 0. Cách dùng tệp này

### Vòng 4 bước cho mỗi giai đoạn

| Bước | Ai | Làm gì | Xong khi |
|---|---|---|---|
| A. Kế hoạch | Antigravity | Đọc mục 0, 3, 4, 5 và đúng giai đoạn đang làm. Viết Implementation Plan cho riêng giai đoạn đó. Mở trang tài liệu X / Anthropic hiện hành để đối chiếu; chỗ nào tệp này sai thì nêu ra. | Người dùng duyệt kế hoạch |
| B. Mã | Antigravity | Viết test trước, chạy cho thấy test hỏng, rồi mới viết mã cho test qua. Chỉ đụng các tệp giai đoạn liệt kê. | Mọi test của giai đoạn đã viết |
| C. Kiểm | Antigravity | Chạy `pytest -q` (toàn bộ) và lệnh kiểm riêng của giai đoạn. | Tất cả qua; hỏng 2 lần cùng một lỗi thì dừng và báo |
| D. Báo cáo | Antigravity | Ghi `docs/bao_cao/gd-N.md`, cập nhật `docs/knowledge/trang_thai.md`, commit, gắn tag `gd-N`. **Dừng.** | Tag tồn tại |
| E. Rà soát | Claude | Đọc báo cáo, đọc `git diff gd-(N-1)..gd-N`, tự chạy lại test. Ghi kết luận vào `docs/bao_cao/gd-N-ra-soat.md`. | Không còn mục «phải sửa» → tag `gd-N-ok` |

`docs/bao_cao/gd-N.md` gồm đúng 5 mục: **Đã làm** · **Kết quả kiểm** (dán nguyên văn output) · **Lệch so với
kế hoạch** (và vì sao) · **Chưa kiểm được** · **Câu hỏi cho người dùng**.

### Câu lệnh dán cho Antigravity

Bắt đầu một giai đoạn (thay `N`):

```
Đọc docs/quy_trinh_trien_khai.md (mục 0, 3, 4, 5 và «Giai đoạn N»), docs/assignment.md và
docs/knowledge/trang_thai.md. Thực hiện ĐÚNG Giai đoạn N theo vòng 4 bước ở mục 0, không làm sang giai
đoạn khác. Trình Implementation Plan và chờ tôi duyệt trước khi viết mã. Xong thì ghi
docs/bao_cao/gd-N.md, cập nhật trang_thai.md, commit, gắn tag gd-N rồi DỪNG.
```

Sửa sau khi Claude rà soát:

```
Đọc docs/bao_cao/gd-N-ra-soat.md. Sửa từng mục «phải sửa» theo thứ tự, mỗi mục một commit kèm test tái
hiện lỗi. Chạy lại pytest -q, dán output vào cuối docs/bao_cao/gd-N.md rồi DỪNG.
```

Gọi Claude rà soát (trong Claude Code, mở tại thư mục repo): `Rà soát giai đoạn N`.

---

## 1. Đề bài đòi gì

Câu quyết định: **«If we can't use it to run outreach ourselves, it doesn't pass.»** Thứ tự ưu tiên vì thế
là: dùng được thật → không nhắn trùng → cá nhân hoá có bằng chứng → đẹp. Đề cũng nói thẳng: bản hẹp mà
chắc tốt hơn bản rộng mà dở dang.

| # | Đề bài yêu cầu | Công cụ phải làm | GĐ |
|---|---|---|---|
| R1 | «give it a target segment or seed accounts» | Hai lối vào: cụm từ khoá của một nhóm đối tượng; hoặc danh sách tài khoản hạt giống | 3 |
| R2 | «finds people and explains why they fit» | Điểm phù hợp kèm lý do; mỗi lý do trỏ về bio hoặc một bài đăng có thật | 4 |
| R3 | «drafts personalised DMs for us to review and approve» | Bản nháp đặt cạnh bằng chứng; sửa, duyệt, từ chối. Chưa duyệt thì không gửi | 4, 6 |
| R4 | «real evidence, not invented familiarity» | Mỗi câu trích phải khớp nguyên văn nguồn; không khớp thì không cho duyệt | 4 |
| R5 | «sends approved messages from our connected account within X's rules and limits» | Đăng nhập OAuth bằng tài khoản của họ; trần gửi mỗi 24 giờ; dừng khi X báo quá giới hạn; chỉ gửi người nhận được DM | 2, 5 |
| R6 | «never double-messages anyone» | Ràng buộc UNIQUE trong CSDL + giữ chỗ nguyên tử + không tự gửi lại khi kết quả mơ hồ | 1, 5 |
| R7 | «what was sent, who replied and what needs our attention» | Tab Track: đã gửi · đã trả lời · cần chú ý | 5, 6 |
| R8 | «use it without you beside us», cài dưới 15 phút | README, lệnh `doctor` tự kiểm cấu hình, chế độ giả lập không cần khoá | 2, 7 |
| R9 | «Make limitations and blocked actions clear» | Hành động nào bị chặn đều hiện lý do và cách gỡ | 5, 6 |
| R10 | «Test real sending only with accounts you control» | Danh sách cho phép gửi, bật mặc định | 5 |
| R11 | «Do not … include secrets in your submission» | Khoá chỉ nằm trong `.env` ngoài git; có lệnh quét trước khi nộp | 1, 7 |
| R12 | «Keep costs low and name any paid tools» | Báo giá trước khi chạy, sổ ghi chi phí thật, không tải lại người đã biết | 3, 7 |
| R13 | Video 3–5 phút, bài viết một trang | Kịch bản quay và bản nháp bài viết | 7 |

**Bốn cái bẫy không ghi trong đề nhưng sẽ bị chấm** (tiêu chí «good judgment about platform rules, failures
and cost»):

1. **Luật của X đòi sự đồng ý trước khi gửi DM tự động.** Công cụ này không gửi tự động: người đọc và bấm
   duyệt từng tin, trần gửi thấp, không có tin nhắc lại tự động, có cờ «không liên hệ nữa». Bài viết phải
   nói thẳng đây là vùng xám và GenAI Fund là bên quyết định mức độ.
2. **Phần lớn người lạ đóng DM.** Trường `receives_your_dm` cho biết trước. Người không nhận được DM vẫn
   hiện trong danh sách, kèm nhãn và gợi ý làm tay (theo dõi, trả lời công khai trước).
3. **Tin nhắn mã hoá (X Chat) có thể làm đường đọc DM cũ không thấy câu trả lời.** Giai đoạn 2 thử thật để
   biết; dù kết quả ra sao, luôn có nút «đánh dấu đã trả lời» và «đã gửi tay» để công cụ vẫn dùng được.
4. **Tiền đọc dữ liệu X lớn hơn tiền mô hình ngôn ngữ.** Lọc bằng quy tắc miễn phí trước, rồi mới tốn tiền
   tải bài đăng và gọi mô hình.

---

## 2. Sự thật về nền tảng (đã kiểm ngày 12/11/2026)

| Điều | Giá trị | Nguồn | Độ chắc |
|---|---|---|---|
| Cách tính tiền X API | Trả theo lượt dùng, mua credit trước; không thấy gói miễn phí | `docs.x.com/x-api/getting-started/pricing` | Đã đọc trang chính thức |
| Đọc 1 bài đăng | 0,005 USD | 〃 | 〃 |
| Đọc 1 hồ sơ người dùng, 1 dòng following | 0,010 USD | 〃 | 〃 |
| Đọc 1 sự kiện DM | 0,010 USD | 〃 | 〃 |
| Gửi 1 DM («DM Interaction: Create») | 0,015 USD | 〃 | 〃 |
| Giới hạn gửi DM | 200 / 15 phút và 1.000 / 24 giờ mỗi người dùng; 15.000 / 24 giờ mỗi app | Trang API DM của X | Vừa — `doctor` kiểm lại |
| Biết trước ai nhận được DM | Trường `receives_your_dm` của đối tượng User | `docs.x.com/x-api/fundamentals/data-dictionary` | Đã đọc |
| Chính sách nhà phát triển | «Always get explicit consent before sending people automated replies or Direct Messages» · «Immediately respect requests to opt-out of being contacted by you» · «Never perform bulk, aggressive, or spammy actions» | `docs.x.com/developer-terms/policy` | Đã đọc |
| X Chat | Có API riêng `/2/chat/...`, bắt buộc đăng ký khoá mã hoá. Đường cũ `/2/dm_events` được báo là không thấy tin trong hội thoại đã mã hoá | `docs.x.com/xchat`, diễn đàn `devcommunity.x.com` (02/2026) | **Chưa chắc hiện trạng** |

**Chưa kiểm được, giai đoạn 2 phải trả lời bằng lần chạy thật:** (a) trả lời của người nhận có hiện trong
`GET /2/dm_events` không; (b) người dùng đi kèm trong `expansions=author_id` có bị tính 0,010 USD mỗi người
không; (c) đường dẫn `https://x.com/messages/compose?recipient_id=…&text=…` còn mở đúng khung soạn tin không;
(d) trang `help.x.com/en/rules-and-policies/x-automation` chặn truy cập tự động — người dùng tự mở đọc.

Địa chỉ dùng trong mã (đối chiếu lại với tài liệu trước khi viết): gốc API `https://api.x.com/2` · xin quyền
`https://x.com/i/oauth2/authorize` · đổi mã lấy token `https://api.x.com/2/oauth2/token`.

---

## 3. Thiết kế đã chốt

### Cấu trúc tệp

```
app.py                  Giao diện Streamlit, 4 tab
outreach/
  config.py             Đọc .env; hằng số: trần gửi, đơn giá, đường dẫn CSDL
  db.py                 Schema, connect(), kv, sổ chi phí
  xclient.py            XClient (httpx): refresh token, 8 lời gọi API, lỗi có kiểu
  fake_x.py             FakeXClient + fake_llm: dữ liệu mẫu, không ra mạng
  auth.py               python -m outreach.auth — đăng nhập X qua trình duyệt (PKCE)
  doctor.py             python -m outreach.doctor — tự kiểm khoá, quyền, giới hạn
  discover.py           Tìm người theo từ khoá / hạt giống, lọc sơ bộ, báo giá
  llm.py                Chấm điểm phù hợp, soạn tin, kiểm bằng chứng
  review.py             Sửa, duyệt, từ chối bản nháp
  sender.py             Gửi tối đa một lần, đối soát, đồng bộ trả lời, mục cần chú ý
tests/                  conftest.py + một tệp test cho mỗi mô-đun + test_app_smoke.py
docs/                   assignment.md · tệp này · knowledge/trang_thai.md · bao_cao/ · writeup.md · demo_script.md
.env.example · .gitignore · requirements.txt · README.md
```

### Cơ sở dữ liệu (SQLite, tạo trong `db.init_db`)

```sql
CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL);   -- token OAuth, trạng thái PKCE, «me»

CREATE TABLE IF NOT EXISTS campaigns (
  id INTEGER PRIMARY KEY, name TEXT NOT NULL,
  segment TEXT NOT NULL,          -- mô tả người cần tìm, đưa cho mô hình
  keywords TEXT NOT NULL,         -- từ khoá lọc bio, cách nhau bằng dấu phẩy
  sender_context TEXT NOT NULL,   -- chúng tôi là ai và muốn gì ở cuộc trò chuyện
  created_at TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS prospects (
  x_user_id TEXT PRIMARY KEY,     -- khoá là id, không phải username (username đổi được)
  username TEXT NOT NULL, name TEXT, bio TEXT, location TEXT, followers INTEGER,
  protected INTEGER NOT NULL DEFAULT 0,
  can_dm INTEGER,                 -- receives_your_dm: 1 / 0 / NULL (chưa biết)
  campaign_id INTEGER NOT NULL REFERENCES campaigns(id),
  source TEXT NOT NULL,           -- 'segment:<query>' hoặc 'seed:<username>'
  fit_score INTEGER, fit_category TEXT, fit_reasons TEXT,   -- JSON [{claim, source_id}]
  do_not_contact INTEGER NOT NULL DEFAULT 0,
  fetched_at TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS posts (
  post_id TEXT PRIMARY KEY,
  x_user_id TEXT NOT NULL REFERENCES prospects(x_user_id),
  text TEXT NOT NULL, created_at TEXT);

CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY,
  x_user_id TEXT NOT NULL UNIQUE REFERENCES prospects(x_user_id),  -- mỗi người đúng một dòng, mãi mãi
  text TEXT NOT NULL,
  evidence TEXT NOT NULL,         -- JSON [{source_id, quote}]
  evidence_ok INTEGER NOT NULL, edited INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL CHECK (status IN
    ('draft','approved','rejected','sending','sent','failed','blocked','unknown')),
  error TEXT, dm_event_id TEXT, dm_conversation_id TEXT,
  claimed_at TEXT, sent_at TEXT,
  reply_text TEXT, reply_event_id TEXT, replied_at TEXT,
  handled_at TEXT, created_at TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS usage (ts TEXT NOT NULL, kind TEXT NOT NULL, units INTEGER NOT NULL, cost_usd REAL NOT NULL);
```

`source_id` ở mọi nơi là chuỗi `"bio"` hoặc một `post_id`. Mốc thời gian là chuỗi UTC ISO-8601, chỉ tạo ở
`db.now()`.

### Vòng đời một tin nhắn

```
draft ─duyệt→ approved ─giữ chỗ→ sending ─2xx→ sent ─có trả lời→ sent + replied_at
  └─từ chối→ rejected               ├─ 403 ────────────→ blocked   chắc chắn chưa gửi, kết thúc
                                    ├─ 400 / 401 ──────→ failed    chắc chắn chưa gửi, người được duyệt lại
                                    ├─ 429 ────────────→ approved  chắc chắn chưa gửi, dừng cả hàng đợi
                                    └─ timeout / mất mạng / 5xx → unknown   KHÔNG tự gửi lại
```

Ba luật không được phá: (1) chỉ `approved` mới được gửi; (2) đổi `approved → sending` bằng một câu
`UPDATE … WHERE id=? AND status='approved'`, kiểm `rowcount == 1`, **commit trước khi gọi X**; (3) `unknown`
chỉ rời trạng thái khi API tìm thấy đúng tin đó, hoặc khi người bấm chọn «đã gửi» / «chưa gửi».

### Cấu hình (`.env.example`, chú thích trong tệp viết bằng tiếng Anh)

```
X_MODE=fake                     # fake: sample data, no keys needed · real: live X API
X_CLIENT_ID=
X_CLIENT_SECRET=
X_REDIRECT_URI=http://127.0.0.1:8765/callback
ANTHROPIC_API_KEY=
LLM_MODEL=claude-fable-5-2
LLM_PRICE_IN=0                  # USD per million input tokens — copy from Anthropic's pricing page
LLM_PRICE_OUT=0
SEND_MODE=allowlist             # allowlist: only SEND_ALLOWLIST can receive · live: any approved prospect
SEND_ALLOWLIST=                 # comma-separated usernames
DAILY_SEND_CAP=20
```

Hằng số trong `config.py`: `PRICES = {"post_read": 0.005, "user_read": 0.010, "dm_read": 0.010,
"dm_send": 0.015}` (USD mỗi đơn vị, ghi chú nguồn và ngày) · `MAX_DM_CHARS = 500` · `MIN_QUOTE_CHARS = 15` ·
`SCOPES = "tweet.read users.read follows.read dm.read dm.write offline.access"` · CSDL: `data/fake.db` khi
`X_MODE=fake`, `data/outreach.db` khi `real`.

### Những thứ cố ý không làm

Tin nhắc lại tự động · nhiều người dùng · triển khai lên máy chủ · tiến trình chạy nền · ORM · hỗ trợ nhiều
nhà cung cấp mô hình · API X Chat mã hoá (chỉ làm nếu giai đoạn 2 cho thấy bắt buộc và Claude đồng ý). Mỗi
mục này ghi một dòng vào phần «what comes next» của bài viết.

---

## 4. Ràng buộc toàn cục (áp cho mọi giai đoạn)

- Mã, giao diện, README, bài viết: **tiếng Anh**. Báo cáo trong `docs/bao_cao/`: tiếng Việt.
- Khoá chỉ nằm trong `.env`. Không in giá trị khoá ra màn hình hay log. Không commit `.env`, `data/`, token.
- Test không bao giờ ra mạng: `XClient` nhận `transport` (dùng `httpx.MockTransport`), mô hình nhận hàm giả.
- Gọi X thật chỉ qua `doctor` và giao diện ở `X_MODE=real`. Trong lúc phát triển, `SEND_MODE` luôn là
  `allowlist` và danh sách chỉ chứa tài khoản của chính mình.
- Chỉ dùng X API chính thức. Không cào trang, không điều khiển trình duyệt vào x.com, không API không chính thức.
- Không gửi gì khi chưa có người duyệt. Không có tin nhắc lại tự động.
- Tên mô hình giữ đúng `claude-fable-5-2` (mặc định, đổi qua `LLM_MODEL`). Không thay bằng tên mô hình cũ.
- Trước khi viết mã cho một lời gọi API, mở trang tài liệu hiện hành của lời gọi đó. Tài liệu khác tệp này
  thì làm theo tài liệu và ghi vào mục «Lệch so với kế hoạch».
- Môi trường: `python -m venv .venv` trong repo; cài bằng `pip install -r requirements.txt` bên trong venv.
- Mỗi nhiệm vụ một commit. Cuối giai đoạn gắn tag `gd-N`.

---

## 5. Trọng tâm rà soát

Năm tình huống đề bài không nói ra nhưng người dùng thật sẽ gặp. Mỗi tình huống đã có test ở giai đoạn ghi
trong ngoặc; Claude soi kỹ nhất các test này.

1. **Ứng dụng tắt giữa lúc đang gửi, hoặc bấm «Send» hai lần, hoặc mở hai tab.** Mong đợi: không ai nhận hai
   tin. (`test_claim_is_atomic`, `test_send_twice_sends_once`, `test_recover_stuck_sending` — GĐ5)
2. **X không trả lời kịp (timeout) sau khi đã nhận lệnh gửi.** Mong đợi: tin thành `unknown`, không tự gửi
   lại, hiện ở mục cần chú ý. (`test_ambiguous_failure_becomes_unknown_and_is_never_resent` — GĐ5)
3. **Người này đã được nhắn tay từ trước, ngoài công cụ.** Mong đợi: bị chặn với lý do «existing
   conversation». (`test_prior_conversation_blocks` — GĐ5)
4. **Token làm mới chỉ dùng được một lần; lưu hụt là mất kết nối.** Mong đợi: token mới được ghi xuống đĩa
   trước khi dùng. (`test_refresh_persists_rotated_token` — GĐ2)
5. **Bio hoặc bài đăng chứa câu lệnh cài cắm, emoji, chữ không phải Latin, hoặc người đó đổi username.** Mong
   đợi: mô hình coi đó là dữ liệu; kiểm bằng chứng vẫn đúng; không sinh hồ sơ trùng.
   (`test_untrusted_text_is_wrapped`, `test_verify_evidence_unicode` — GĐ4; `test_username_change_does_not_duplicate` — GĐ3)

---

## Giai đoạn 0 — Việc của người (Antigravity không làm được)

- [ ] **Trước Thứ Sáu 13/11/2026, 12:00 (GMT+7):** gửi thư xác nhận tham gia tới `hr@genaifund.ai`.
- [ ] Tạo tài khoản nhà phát triển X, tạo một App. Bật OAuth 2.0, loại ứng dụng có Client Secret (Web App),
      quyền đọc + ghi + Direct Messages, Callback URI `http://127.0.0.1:8765/callback`. Tên nút trong bảng
      điều khiển có thể khác đôi chút.
- [ ] Mua credit ở mức nhỏ nhất bảng điều khiển cho phép và đặt hạn mức chi. Ước tính của Claude cho cả quá
      trình phát triển: dưới 10 USD.
- [ ] Có hai tài khoản X của chính mình: **A** để gửi, **B** để nhận thử. B phải theo dõi A hoặc mở DM.
- [ ] Tạo khoá API của Anthropic.
- [ ] Mở trang `help.x.com/en/rules-and-policies/x-automation`, đọc phần về Direct Messages, chép câu liên
      quan vào `docs/bao_cao/gd-0.md` (bài viết cuối cần trích).
- [ ] Mở thư mục repo bằng Antigravity. Không dán khoá vào khung trò chuyện; tự điền vào `.env` ở GĐ1.

---

## Giai đoạn 1 — Khung dự án và cơ sở dữ liệu

**Tệp tạo:** `.gitignore` · `.env.example` · `requirements.txt` · `outreach/__init__.py` · `outreach/config.py`
· `outreach/db.py` · `tests/conftest.py` · `tests/test_db.py`

**Tạo ra cho giai đoạn sau:**

```python
# outreach/db.py
def now() -> str
def connect(path: str | None = None) -> sqlite3.Connection   # Row factory, foreign_keys=ON, WAL, gọi init_db
def init_db(conn) -> None
def kv_get(conn, key: str) -> dict | None
def kv_set(conn, key: str, value: dict) -> None
def record_usage(conn, kind: str, units: int) -> None        # kind: post_read|user_read|dm_read|dm_send|llm_in|llm_out
def spend_since(conn, iso_ts: str) -> float
# tests/conftest.py — fixture: conn (":memory:"), file_db (tmp_path, cho test hai kết nối), campaign_id
```

- [ ] **1.1** `git init`; viết `.gitignore` (`.env`, `data/`, `.venv/`, `__pycache__/`, `.pytest_cache/`),
      `.env.example` (mục 3), `requirements.txt` (5 thư viện, ghim phiên bản đang cài). Tạo venv, cài, commit.
- [ ] **1.2** Viết `tests/test_db.py`, chạy thấy hỏng:
  - `test_init_db_is_idempotent` — gọi `init_db` hai lần, dòng đã chèn vẫn còn.
  - `test_one_message_per_person` — chèn tin thứ hai cho cùng `x_user_id` → `sqlite3.IntegrityError`.
  - `test_status_check_constraint` — `status='bogus'` → `sqlite3.IntegrityError`.
  - `test_message_requires_existing_prospect` — `x_user_id` lạ → `sqlite3.IntegrityError`.
  - `test_kv_roundtrip` — `kv_set(conn,"k",{"a":1})` rồi `kv_get(conn,"k") == {"a":1}`; khoá lạ → `None`.
  - `test_record_usage_cost` — `record_usage(conn,"post_read",3)` rồi `spend_since(conn,"1970") == pytest.approx(0.015)`.
- [ ] **1.3** Viết `config.py` và `db.py` cho test qua. Chạy `pytest -q` → 6 passed. Commit.

**Xong khi:** `pytest -q` báo 6 passed; `git status` không liệt kê `.env` hay `data/`.

---

## Giai đoạn 2 — Kết nối X và lần thử thật

**Tệp tạo:** `outreach/xclient.py` · `outreach/fake_x.py` · `outreach/auth.py` · `outreach/doctor.py` ·
`tests/test_xclient.py`

**Dùng từ GĐ1:** `kv_get`, `kv_set`, `record_usage`. **Tạo ra cho giai đoạn sau:**

```python
# outreach/xclient.py
class XError(Exception): status: int; detail: str
class RateLimited(XError): reset_at: int     # giây epoch, đọc từ header x-rate-limit-reset
class AuthError(XError)                      # 401 — phải đăng nhập lại
class Forbidden(XError)                      # 403
class Ambiguous(XError)                      # timeout, lỗi mạng, 5xx — không biết lệnh đã chạy hay chưa

class XClient:
    def __init__(self, conn, transport: httpx.BaseTransport | None = None)
    def me(self) -> dict                                                   # {id, username}; lưu vào kv["me"]
    def search_recent(self, query: str, max_results: int) -> tuple[list[dict], list[dict]]   # (posts, users)
    def users_by_usernames(self, usernames: list[str]) -> list[dict]
    def following(self, user_id: str, max_results: int) -> list[dict]
    def user_posts(self, user_id: str, max_results: int = 5) -> list[dict]  # bỏ retweet và reply
    def send_dm(self, user_id: str, text: str) -> dict                      # {dm_event_id, dm_conversation_id}
    def dm_events_with(self, user_id: str, max_results: int) -> list[dict]
    def dm_events(self, stop_at_id: str | None = None) -> list[dict]        # mới nhất trước, dừng ở stop_at_id

def get_x(conn)   # FakeXClient khi X_MODE=fake, ngược lại XClient
```

Dạng dữ liệu đã chuẩn hoá — user: `{id, username, name, description, location, followers, protected,
receives_your_dm}` · post: `{id, author_id, text, created_at}` · sự kiện DM: `{id, sender_id, text,
created_at, dm_conversation_id}`. Mỗi lời gọi ghi `record_usage` theo số tài nguyên trả về.

```python
# outreach/auth.py
def build_authorize_url(state: str, code_challenge: str) -> str
def login(timeout_s: int = 120) -> dict     # mở trình duyệt, nghe ở 127.0.0.1:8765, lưu token vào kv, trả về me
# outreach/fake_x.py
class FakeXClient   # cùng 8 phương thức; thuộc tính: sent: list[tuple[str, str]], inbox: list[dict], fail_next: Exception | None
def fake_llm(system: str, user: str, schema: dict) -> dict
```

Dữ liệu mẫu của `FakeXClient`: 6 người — 2 người hợp và nhận được DM, 2 người hợp nhưng đóng DM, 1 tài khoản
khoá, 1 người không liên quan; mỗi người 2–3 bài đăng.

- [ ] **2.1** Viết `tests/test_xclient.py` bằng `httpx.MockTransport`, chạy thấy hỏng:
  - `test_authorize_url_has_pkce_and_scopes` — URL chứa `code_challenge_method=S256`, `dm.write`, `offline.access`.
  - `test_refresh_persists_rotated_token` — token hết hạn → gọi điểm đổi token; `kv["oauth"]` chứa cặp token
    mới **trước khi** lời gọi API đi ra; lời gọi API mang access token mới.
  - `test_send_dm_posts_to_participant_endpoint` — đường dẫn `/2/dm_conversations/with/42/messages`, thân
    `{"text": "hi"}`, trả về `{"dm_event_id": "e1", "dm_conversation_id": "c1"}`.
  - `test_search_recent_joins_authors` — trả về post và user đã chuẩn hoá, có `receives_your_dm`.
  - `test_429_raises_ratelimited_with_reset` — header `x-rate-limit-reset: 1700000000` → `reset_at == 1700000000`.
  - `test_401_raises_autherror` · `test_403_raises_forbidden` · `test_timeout_and_5xx_raise_ambiguous`.
  - `test_usage_recorded_per_resource` — tìm kiếm trả 3 bài và 2 người → sổ ghi `post_read` 3, `user_read` 2.
  - `test_dm_events_stops_at_known_id` — không xin trang tiếp sau khi gặp `stop_at_id`.
  - `test_fake_client_has_same_methods` — mọi phương thức công khai của `XClient` có ở `FakeXClient`.
- [ ] **2.2** Viết `xclient.py`, `auth.py`, `fake_x.py` cho test qua. `pytest -q` → 17 passed. Commit.
- [ ] **2.3** Viết `doctor.py`. Mỗi dòng in `PASS` / `WARN` / `FAIL` kèm cách sửa, không bao giờ in giá trị khoá:
  1. `.env` có đủ tên khoá. 2. Token còn dùng được, in «Connected as @…». 3. Token có `dm.read`, `dm.write`.
  4. `--spend`: một lần tìm kiếm 10 kết quả, in số bài, số người, số tiền ước tính.
  5. `--dm-test <username>` (phải nằm trong `SEND_ALLOWLIST`): in `receives_your_dm`, gửi một tin thử.
  6. `--check-reply <username>`: đọc `dm_events`, báo có thấy trả lời của người đó không.
- [ ] **2.4 Thử thật (người dùng cùng làm):** điền `.env`, `X_MODE=real`, `SEND_ALLOWLIST=<B>`. Chạy
      `python -m outreach.auth`, rồi `python -m outreach.doctor --spend --dm-test <B>`. Dùng tài khoản B trả
      lời tin thử. Chạy `python -m outreach.doctor --check-reply <B>`. Mở đường dẫn soạn tin ở mục 2 (c) trong
      trình duyệt. Xem bảng điều khiển X để trả lời mục 2 (b). Ghi cả bốn kết quả vào `docs/bao_cao/gd-2.md`.

**Xong khi:** 17 test qua, và báo cáo trả lời được bốn câu hỏi mở của mục 2.

**Cổng quyết định (Claude chốt sau khi đọc báo cáo):**

| Kết quả thử thật | Hướng đi |
|---|---|
| Gửi được, thấy trả lời qua API | Giữ nguyên kế hoạch |
| Gửi được, **không** thấy trả lời | Giữ nguyên; nút «Mark replied» thành đường chính, ghi rõ giới hạn trong README và bài viết |
| Không gửi được qua API | **Dừng, hỏi Claude.** Phương án lùi: mở sẵn khung soạn tin trên X + nút «I sent it»; chống trùng và theo dõi vẫn giữ |

---

## Giai đoạn 3 — Tìm người

**Tệp tạo:** `outreach/discover.py` · `tests/test_discover.py`

**Dùng từ GĐ2:** `search_recent`, `users_by_usernames`, `following`, `user_posts`, `me`. **Tạo ra:**

```python
def build_query(phrases: list[str]) -> str
def estimate_cost(mode: str, n: int) -> float      # mode: 'segment' | 'seed' | 'enrich'
def prefilter(user: dict, keywords: list[str] | None) -> str | None   # lý do loại (tiếng Anh) hoặc None
def discover_by_segment(conn, x, campaign_id: int, phrases: list[str], max_posts: int = 50) -> int
def discover_by_seed(conn, x, campaign_id: int, seed_username: str, max_users: int = 100) -> int
def enrich(conn, x, limit: int = 20) -> int        # tải 5 bài gần nhất cho hồ sơ chưa có bài nào
```

Luật: hai hàm `discover_*` trả về số hồ sơ **mới**; bỏ qua chính mình; hồ sơ đã có trong CSDL thì không ghi
đè dòng nào. `discover_by_segment` lưu luôn bài đăng khớp làm bằng chứng. `discover_by_seed` truyền
`keywords` của chiến dịch vào `prefilter`; `discover_by_segment` truyền `None`. `can_dm` lấy từ
`receives_your_dm`; người đóng DM vẫn được lưu.

- [ ] **3.1** Viết `tests/test_discover.py`, chạy thấy hỏng:
  - `test_build_query` — `build_query(["embodied AI","humanoid robot"]) == '("embodied AI" OR "humanoid robot") -is:retweet -is:reply lang:en'`.
  - `test_estimate_cost` — `('segment', 50) == 0.75` · `('seed', 100) == 1.00` · `('enrich', 20) == 0.50`
    (so bằng `pytest.approx`, vì đây là số thực).
  - `test_prefilter_reasons` — khoá → `"protected account"`; bio rỗng → `"no bio"`; có `keywords` mà bio
    không chứa từ nào → `"bio matches no keyword"`; hợp lệ → `None`.
  - `test_segment_creates_prospects_with_evidence_posts` — với dữ liệu mẫu: hồ sơ mới có `source` bắt đầu
    bằng `segment:` và ít nhất một dòng trong `posts`.
  - `test_known_user_not_overwritten` — hồ sơ có `do_not_contact=1` giữ nguyên sau khi tìm lại; hàm trả 0.
  - `test_username_change_does_not_duplicate` — cùng `id`, username khác → vẫn một dòng.
  - `test_self_is_skipped` — tác giả trùng `me()["id"]` không thành hồ sơ.
  - `test_closed_dm_is_kept_and_flagged` — `receives_your_dm=False` → có hồ sơ, `can_dm == 0`.
  - `test_enrich_only_prospects_without_posts` — chỉ gọi `user_posts` cho hồ sơ chưa có bài.
- [ ] **3.2** Viết `discover.py` cho test qua. `pytest -q` → 26 passed. Commit.

**Xong khi:** 26 test qua.

---

## Giai đoạn 4 — Chấm điểm, soạn tin, kiểm bằng chứng

**Tệp tạo:** `outreach/llm.py` · `outreach/review.py` · `tests/test_llm.py` · `tests/test_review.py`

**Tạo ra:**

```python
# outreach/llm.py
LLMCall = Callable[[str, str, dict], dict]      # (system, user, json_schema) -> dict đã phân tích
def get_llm(conn) -> LLMCall                    # fake_llm khi X_MODE=fake và không có khoá; ngược lại Anthropic
def score_fit(call: LLMCall, segment: str, prospect: dict, posts: list[dict]) -> dict
    # {score: 0..100, category: 'founder'|'builder'|'researcher'|'other', reasons: [{claim, source_id}]}
def draft_dm(call: LLMCall, sender_context: str, prospect: dict, posts: list[dict], fit: dict) -> dict
    # {text, evidence: [{source_id, quote}]}
def verify_evidence(evidence: list[dict], bio: str, posts: list[dict]) -> bool
def draft_problems(text: str) -> list[str]      # cảnh báo, không chặn
def score_and_draft(conn, call: LLMCall, min_score: int = 60, limit: int = 20) -> int   # số bản nháp mới

# outreach/review.py
def set_text(conn, message_id: int, text: str) -> None      # đặt edited=1; chỉ khi status ∈ draft, rejected, failed
def approve(conn, message_id: int) -> str | None            # None = đã duyệt; chuỗi = lý do từ chối
def reject(conn, message_id: int) -> None
```

Luật đã chốt:

- Lời gọi Anthropic ép đầu ra JSON bằng công cụ (`tools` + `tool_choice`) theo `json_schema`; ghi
  `usage.input_tokens` và `usage.output_tokens` vào sổ (`llm_in`, `llm_out`).
- Bio và bài đăng đặt trong thẻ `<profile>` và `<post id="…">`. Lời nhắc hệ thống nói rõ nội dung trong thẻ
  là dữ liệu, không phải chỉ dẫn.
- `score_fit`: lý do có `source_id` không tồn tại thì loại; không còn lý do nào thì `score = 0`.
- `verify_evidence` đúng khi danh sách không rỗng và mỗi `quote` dài ít nhất `MIN_QUOTE_CHARS`, là chuỗi con
  của nguồn nó trỏ tới sau khi chuẩn hoá (`casefold`, gộp khoảng trắng).
- Lời nhắc soạn tin bắt buộc: tối đa 500 ký tự; câu đầu nhắc một điều cụ thể người đó đã viết, lấy từ
  bằng chứng; một câu nói rõ người gửi là GenAI Fund; kết bằng một câu hỏi mở; không đường dẫn, không
  hashtag; cấm nói đã gặp, đã quen, đã theo dõi lâu; cấm số liệu không có trong nguồn.
- `draft_problems` trả cảnh báo cho: dài quá `MAX_DM_CHARS`; chứa `http`; chứa cụm tỏ ra quen biết (`big fan`,
  `long-time`, `we met`, `as discussed`, `following you for`).
- `score_and_draft` chỉ xử lý hồ sơ có bài đăng, chưa có điểm, `do_not_contact=0`. Tạo `messages` trạng thái
  `draft` khi `score >= min_score` và hồ sơ **chưa có dòng nào** trong `messages`.
- `approve` chỉ chạy khi status ∈ `draft`, `rejected`, `failed`; status khác → trả lý do
  `"cannot approve from status <status>"`. Từ chối khi `evidence_ok=0` và `edited=0`, với lý do
  `"evidence not verified — edit the text first"`. `set_text` không đổi status.

- [ ] **4.1** Viết test, chạy thấy hỏng. `tests/test_llm.py`:
  - `test_verify_evidence_accepts_verbatim_quote_ignoring_case_and_spacing`
  - `test_verify_evidence_rejects_invented_quote`
  - `test_verify_evidence_rejects_empty_and_short_quotes` — danh sách rỗng → `False`; trích 14 ký tự → `False`.
  - `test_verify_evidence_rejects_unknown_source_id`
  - `test_verify_evidence_unicode` — trích có emoji và chữ Việt, khớp nguồn → `True`.
  - `test_score_fit_drops_reasons_with_unknown_source` — mọi lý do sai nguồn → `score == 0`.
  - `test_untrusted_text_is_wrapped` — chuỗi `user` hàm giả nhận được chứa bio nằm giữa `<profile>` và `</profile>`.
  - `test_draft_problems` — tin 501 ký tự, tin chứa `https://`, tin chứa `big fan` → mỗi tin một cảnh báo; tin sạch → `[]`.
  - `test_score_and_draft_respects_min_score` — điểm 59 → không có bản nháp; điểm 60 → có.
  - `test_score_and_draft_never_touches_existing_message` — hồ sơ đã có tin `rejected` → không tạo, không sửa.
  - `test_llm_usage_recorded` — hàm bọc Anthropic với client giả ghi đúng số token vào sổ.

  `tests/test_review.py`:
  - `test_approve_requires_verified_evidence` — `evidence_ok=0`, `edited=0` → trả về lý do, status vẫn `draft`.
  - `test_edit_then_approve` — sau `set_text`, `approve` trả `None`, status `approved`.
  - `test_cannot_edit_after_sent` — `set_text` trên tin `sent` → `ValueError`.
  - `test_reject` — status `rejected`.
- [ ] **4.2** Viết `llm.py`, `review.py` cho test qua. `pytest -q` → 41 passed. Commit.
- [ ] **4.3** Kiểm bằng mắt với mô hình thật: `X_MODE=fake` kèm `ANTHROPIC_API_KEY`, chạy `score_and_draft`
      trên dữ liệu mẫu. Dán 3 bản nháp cùng bằng chứng vào báo cáo để Claude đọc chất lượng.

**Xong khi:** 41 test qua, báo cáo có 3 bản nháp thật.

---

## Giai đoạn 5 — Gửi và theo dõi

**Tệp tạo:** `outreach/sender.py` · `tests/test_sender.py`

**Dùng:** `send_dm`, `dm_events_with`, `dm_events`, `me` (GĐ2); các lỗi có kiểu (GĐ2). **Tạo ra:**

```python
class SendBlocked(Exception): reason: str
def sends_in_last_24h(conn) -> int              # đếm status ∈ sending, sent, unknown có claimed_at trong 24 giờ
def check_can_send(conn, message_id: int) -> str | None      # None = được gửi; chuỗi = lý do (tiếng Anh)
def claim(conn, message_id: int) -> bool
def send_one(conn, x, message_id: int) -> str                # trả về status mới; SendBlocked nếu bị chặn
def send_queue(conn, x, spacing_s: float = 20.0, sleep=time.sleep) -> dict[str, int]
def recover_stuck(conn, older_than_s: int = 300) -> int      # sending quá hạn → unknown
def reconcile(conn, x, message_id: int) -> str               # tìm thấy tin → sent; không thấy → vẫn unknown
def resolve_unknown(conn, message_id: int, was_sent: bool) -> str    # người quyết: sent hoặc failed
def mark_sent_manually(conn, message_id: int) -> None        # approved → sent, error='sent manually'
def sync_replies(conn, x) -> int                             # số trả lời mới
def mark_replied(conn, message_id: int, note: str) -> None
def mark_handled(conn, message_id: int) -> None
def needs_attention(conn) -> list[sqlite3.Row]
```

Luật đã chốt:

- `check_can_send` kiểm theo thứ tự, trả lý do đầu tiên vướng: status khác `approved` → `"not approved"` ·
  `do_not_contact=1` → `"marked do-not-contact"` · `can_dm=0` → `"recipient does not accept DMs from this account"` ·
  `SEND_MODE=allowlist` mà username ngoài danh sách → `"not on SEND_ALLOWLIST (safety mode)"` ·
  `sends_in_last_24h >= DAILY_SEND_CAP` → `"daily cap reached (N/N)"`.
- `send_one`: `check_can_send` → `claim` (commit) → `dm_events_with(user, 1)`; có sự kiện → `blocked`, lỗi
  `"existing conversation"`; bước kiểm này lỗi → trả về `approved` rồi ném lỗi → `send_dm` → xử lý theo sơ
  đồ vòng đời ở mục 3.
- `send_queue` gửi lần lượt các tin `approved`, nghỉ `spacing_s` giữa hai tin, dừng hẳn khi gặp
  `RateLimited`, `AuthError` hoặc chạm trần. Tin bị `check_can_send` chặn vì lý do khác thì bỏ qua và đếm
  vào `skipped`. Trả về bộ đếm theo status.
- `reconcile` đọc `dm_events_with(user, 10)`: có sự kiện do mình gửi với `text` trùng → `sent`. Không thấy thì
  **giữ `unknown`** (hội thoại mã hoá có thể vô hình với API) và chờ người chọn qua `resolve_unknown`.
- `sync_replies` đọc `dm_events(stop_at_id=kv["last_dm_event"])`; sự kiện có `sender_id` là người đã nhận tin
  `sent` và chưa có `replied_at` → ghi `reply_text`, `reply_event_id`, `replied_at`. Bỏ qua tin của chính
  mình và của người lạ.
- `needs_attention` gồm: có trả lời mà `handled_at` trống · `unknown` · `failed` · `blocked` chưa `handled`.

- [ ] **5.1** Viết `tests/test_sender.py` với `FakeXClient`, chạy thấy hỏng:
  - `test_send_happy_path` — `approved → sent`, có `dm_event_id`, `len(x.sent) == 1`.
  - `test_unapproved_is_never_sent` — tin `draft` và tin `rejected` → `SendBlocked`, `len(x.sent) == 0`.
  - `test_send_twice_sends_once` — gọi `send_one` hai lần → lần hai `SendBlocked`, `len(x.sent) == 1`.
  - `test_claim_is_atomic` — hai kết nối tới cùng `file_db`: đúng một `claim` trả `True`.
  - `test_ambiguous_failure_becomes_unknown_and_is_never_resent` — `x.fail_next = Ambiguous(...)` → `unknown`;
    chạy `send_queue` lần nữa → `len(x.sent) == 0`.
  - `test_403_marks_blocked` · `test_400_marks_failed`.
  - `test_429_returns_to_approved_and_stops_queue` — 3 tin, tin thứ hai gặp 429 → tin 2 và 3 vẫn `approved`.
  - `test_daily_cap_blocks` — trần 2, đã có 2 tin trong 24 giờ → lý do chứa `"daily cap"`.
  - `test_allowlist_blocks_strangers` — lý do chứa `"SEND_ALLOWLIST"`, `len(x.sent) == 0`.
  - `test_do_not_contact_blocks` · `test_closed_dm_blocks`.
  - `test_prior_conversation_blocks` — `x.inbox` có sẵn sự kiện với người đó → `blocked`, `len(x.sent) == 0`.
  - `test_recover_stuck_sending` — `sending` có `claimed_at` cách 10 phút → `unknown`; cách 1 phút → giữ nguyên.
  - `test_reconcile_found_marks_sent` · `test_reconcile_not_found_stays_unknown`.
  - `test_resolve_unknown` — `was_sent=True → sent`; `False → failed`.
  - `test_mark_sent_manually_counts_toward_cap` — sau đó `sends_in_last_24h == 1`, `send_one` → `SendBlocked`.
  - `test_sync_replies_marks_replied_and_ignores_own_and_strangers`.
  - `test_sync_replies_idempotent` — chạy hai lần: lần đầu trả 1, lần hai trả 0.
  - `test_needs_attention_contents` — đủ bốn loại; sau `mark_handled` thì mục đó biến mất.
- [ ] **5.2** Viết `sender.py` cho test qua. `pytest -q` → 62 passed. Commit.

**Xong khi:** 62 test qua.

---

## Giai đoạn 6 — Giao diện

**Tệp tạo:** `app.py` · `tests/test_app_smoke.py`. `app.py` không chứa luật nghiệp vụ; chỉ gọi hàm đã có.

- **Thanh bên:** nhãn `SAMPLE DATA` hoặc `LIVE` · «Connected as @…» hoặc nút `Connect X account` (gọi
  `auth.login`) · `Sent in last 24h: n / cap` · chế độ gửi (`ALLOWLIST: only @…` hoặc `LIVE`) · `Estimated
  spend today: $…` (từ `spend_since`).
- **Tab 1 Find:** biểu mẫu chiến dịch (name, segment, keywords, sender context) · ô cụm từ → hiện
  `estimate_cost` → nút `Search` · ô tài khoản hạt giống → hiện giá → nút `Import following` · nút
  `Fetch recent posts` · nút `Score & draft` · bảng hồ sơ: username có liên kết, điểm, loại, lý do, nhãn
  nhận được DM hay không.
- **Tab 2 Review:** mỗi bản nháp hiện tóm tắt hồ sơ, lý do phù hợp, từng câu trích kèm liên kết
  `https://x.com/<username>/status/<post_id>`, ô sửa nội dung, cảnh báo từ `draft_problems`, nút `Approve` /
  `Reject`. `Approve` bị từ chối thì hiện nguyên văn lý do.
- **Tab 3 Send:** danh sách `approved`; mỗi dòng hiện lý do từ `check_can_send` nếu bị chặn, liên kết
  `Open in X`, nút `I sent it manually`; nút `Send approved (n)` chạy `send_queue` kèm thanh tiến độ.
- **Tab 4 Track:** số đã gửi, số trả lời, tỉ lệ · nút `Sync replies` · danh sách **Needs attention** (mỗi
  mục có hành động phù hợp: `Reconcile`, `It was sent` / `It was not sent`, `Mark replied`, `Mark handled`) ·
  bảng nhật ký gửi · công tắc `Do not contact`.
- Khi khởi động: gọi `recover_stuck`.

- [ ] **6.1** Viết `tests/test_app_smoke.py`, chạy thấy hỏng:
  - `test_app_runs_in_fake_mode` — `AppTest.from_file("app.py").run(timeout=30)`; `not at.exception`; `len(at.tabs) == 4`.
- [ ] **6.2** Viết `app.py`. `pytest -q` → 63 passed. Commit.
- [ ] **6.3** Tự đi hết luồng ở `X_MODE=fake`: tìm → chấm điểm → duyệt → gửi → đồng bộ trả lời. Chụp một
      ảnh mỗi tab, đặt vào `docs/bao_cao/` và trỏ tới trong báo cáo.

**Xong khi:** 63 test qua; đi hết luồng ở chế độ giả lập không gặp lỗi.

---

## Giai đoạn 7 — Chạy thật, tài liệu, nộp bài

- [ ] **7.1 Chạy thật từ đầu đến cuối** (`X_MODE=real`, `SEND_MODE=allowlist`, danh sách chỉ có B). Ghi vào
      báo cáo từng dòng kèm bằng chứng (status, id, số liệu):
      tìm theo cụm từ → có hồ sơ, giá thật so với giá báo trước · đưa B vào bằng lối hạt giống → chấm điểm →
      có bản nháp với bằng chứng khớp · duyệt, gửi → B nhận được tin · gửi lại lần hai → bị chặn · thử gửi
      cho một người ngoài danh sách → bị chặn đúng lý do · B trả lời → `Sync replies` (hoặc `Mark replied`)
      → hiện ở Needs attention · tổng chi phí thật từ bảng `usage`.
- [ ] **7.2 `README.md`** (tiếng Anh): công cụ làm gì · yêu cầu (tài khoản X developer có credit, quyền của
      App, khoá Anthropic, chi phí dự kiến) · cài đặt đánh số từng bước · dùng thử không cần khoá
      (`X_MODE=fake`) · chuyển sang gửi thật (`SEND_MODE=live`) và ý nghĩa của việc đó · bảng «giới hạn và
      hành động bị chặn» (lý do hiện ra → cách gỡ) · xử lý sự cố · dữ liệu lưu ở đâu (nội dung DM chỉ nằm
      trong tệp SQLite trên máy).
- [ ] **7.3 Đo thời gian cài đặt:** clone sang thư mục trống, làm đúng theo README, bấm giờ. Phải dưới 15 phút.
- [ ] **7.4 `docs/writeup.md`** (tiếng Anh, không quá một trang): cách tiếp cận · đánh đổi (API chính thức và
      người duyệt từng tin, đổi lại tầm với nhỏ hơn) · luật của X và lập trường của công cụ · việc tiếp
      theo · chi phí (đơn giá X, số đo thật ở 7.1, công thức cho 100 hồ sơ) · đã dùng công cụ AI ra sao và
      kiểm kết quả bằng gì (Claude lập kế hoạch và rà soát, Antigravity viết mã, 63 test, bộ kiểm bằng
      chứng, người duyệt). Mọi con số lấy từ báo cáo, không ước lượng.
- [ ] **7.5 `docs/demo_script.md`:** kịch bản 3–5 phút — `doctor` → tìm theo cụm từ → lý do phù hợp và bằng
      chứng → sửa và duyệt, cho thấy một bản bị từ chối duyệt vì bằng chứng sai → gửi cho B, mở X thấy tin
      đến → gửi lại bị chặn → B trả lời, hiện ở Needs attention → nói thẳng phần chưa xong.
- [ ] **7.6 Quét trước khi nộp:** `git ls-files` không có `.env`, `data/`, `*.db`; `git grep -n "sk-ant-"`
      không ra dòng nào; `pytest -q` qua toàn bộ.
- [ ] **Người làm:** quay video, gửi thư nộp bài **trước 11:00 Thứ Ba 17/11/2026**.

**Xong khi:** mọi dòng ở 7.1 có bằng chứng; 7.3 dưới 15 phút; 7.6 sạch.

---

## Lịch đề xuất

| Ngày | Việc |
|---|---|
| Thứ Năm 12/11 | Giai đoạn 0 (người) · Giai đoạn 1 |
| Thứ Sáu 13/11 | **Trước 12:00: thư xác nhận** · Giai đoạn 2 và lần thử thật · Giai đoạn 3 |
| Thứ Bảy 14/11 | Giai đoạn 4 · Giai đoạn 5 |
| Chủ Nhật 15/11 | Giai đoạn 6 · bắt đầu 7.1 |
| Thứ Hai 16/11 | Giai đoạn 7 · Claude rà soát tổng · quay video |
| Thứ Ba 17/11 | Sáng: dự phòng · nộp trước 11:00 |

Nếu trễ: cắt lối vào hạt giống (R1 vẫn đạt nhờ lối cụm từ) trước, rồi tới `reconcile` tự động (giữ
`resolve_unknown` bằng tay). Không bao giờ cắt giai đoạn 5 và mục 7.1.
