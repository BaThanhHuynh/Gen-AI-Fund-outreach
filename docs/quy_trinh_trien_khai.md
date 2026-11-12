# Quy trình triển khai — Công cụ tìm người và nhắn tin trên X cho GenAI Fund

> **Dành cho Antigravity và người điều khiển nó.** Mỗi lần chỉ làm **một giai đoạn** theo vòng các bước ở
> mục 0, rồi **dừng** để Claude rà soát. Ô `- [ ]` dùng để đánh dấu tiến độ.
>
> **Bản 2 — 2026-11-12: chuyển sang hướng 0 USD**, người dùng đã duyệt. Lý do, nguồn, số đo:
> `docs/knowledge/nghien-cuu-0-usd.md`. Bản 1 (dựa hoàn toàn vào X API trả tiền) nằm trong git ở commit `f7e67ef`.

**Mục tiêu:** một công cụ GenAI Fund tự chạy được trên máy mình, có thể dùng mà **không tốn tiền**. Công cụ:
- Tìm người làm AI / robotics ở Đông Nam Á có tài khoản X, qua GitHub API chính thức (miễn phí).
- Giải thích vì sao từng người phù hợp, mỗi lý do trỏ về bằng chứng thật (phần giới thiệu, repo).
- Soạn tin riêng bằng mô hình chạy trên máy để người duyệt.
- Giúp người gửi tin đã duyệt: chép sẵn tin, mở hồ sơ X, rồi ghi nhận kết quả.
- Không bao giờ nhắn trùng.
- Cho thấy đã gửi gì, ai trả lời, việc gì cần xử lý.

Gửi qua X API chính thức là **tuỳ chọn** khi có credit X.

**Kiến trúc:**
- Một ứng dụng Streamlit chạy trên máy, một tệp SQLite là nguồn sự thật duy nhất.
- Giao diện chỉ gọi hàm trong gói `outreach/`.
- Mọi luật an toàn (chống trùng, trần gửi, danh sách cho phép) nằm ở ràng buộc của CSDL và ở `sender.py`,
  không nằm ở giao diện.
- Mỗi nguồn bên ngoài có một bản thật và một bản giả cùng phương thức: `GitHubClient` / `FakeGitHub`,
  `XClient` / `FakeXClient`. Nhờ vậy test và chế độ dùng thử không bao giờ ra mạng.

**Công nghệ:**
- Python ≥ 3.11 · Streamlit · `sqlite3` (thư viện chuẩn) · httpx · anthropic · python-dotenv · pytest.
- **Không thêm thư viện.** GitHub và Ollama đều gọi qua HTTP bằng httpx.
- Ollama là ứng dụng ngoài, người dùng tự cài.

**Đề bài:** `docs/assignment.md` (bản sao nguyên văn). **Hạn nộp: Thứ Ba 17/11/2026, 12:00 (GMT+7).**

---

## 0. Cách dùng tệp này

### Vòng các bước cho mỗi giai đoạn

| Bước | Ai | Làm gì | Xong khi |
|---|---|---|---|
| A. Kế hoạch | Antigravity | Đọc mục 0, 3, 4, 5 và đúng giai đoạn đang làm. Viết Implementation Plan cho riêng giai đoạn đó. Mở trang tài liệu GitHub / Ollama / X / Anthropic hiện hành của mọi lời gọi API sẽ viết; chỗ nào tệp này sai thì nêu ra. | Người dùng duyệt kế hoạch |
| B. Mã | Antigravity | Viết test trước, chạy cho thấy test hỏng, rồi mới viết mã cho test qua. Chỉ đụng các tệp giai đoạn liệt kê. | Mọi test của giai đoạn đã viết |
| C. Kiểm | Antigravity | Chạy `pytest -q` (toàn bộ) và lệnh kiểm riêng của giai đoạn. | Tất cả qua; hỏng 2 lần cùng một lỗi thì dừng và báo |
| D. Báo cáo | Antigravity | Ghi `docs/bao_cao/gd-N.md`, cập nhật `docs/knowledge/trang_thai.md`, commit, gắn tag `gd-N`. **Dừng.** | Tag tồn tại |
| E. Rà soát | Claude | Đọc báo cáo, đọc `git diff`, tự chạy lại test. Ghi kết luận vào `docs/bao_cao/gd-N-ra-soat.md`. | Không còn mục «phải sửa» → tag `gd-N-ok` |

`docs/bao_cao/gd-N.md` gồm đúng 5 mục:
1. **Đã làm**
2. **Kết quả kiểm** — dán nguyên văn output.
3. **Lệch so với kế hoạch** — và vì sao.
4. **Chưa kiểm được**
5. **Câu hỏi cho người dùng**

Ba luật báo cáo, vi phạm là mục «phải sửa»:
- **Chưa chạy thì ghi vào «Chưa kiểm được».** Không viết suy đoán thành câu trả lời.
- **Output ở `X_MODE=fake` phải ghi nhãn `X_MODE=fake`.**
- **Không ghi «người dùng chỉ đạo …» nếu người dùng chưa nói điều đó trong cuộc trò chuyện.** Lệch khỏi tệp
  này thì hỏi trước, không tự đổi rồi báo sau.

### Câu lệnh dán cho Antigravity

Bắt đầu một giai đoạn (thay `N`):

```
Đọc docs/quy_trinh_trien_khai.md (mục 0, 3, 4, 5 và «Giai đoạn N»), docs/assignment.md và
docs/knowledge/trang_thai.md. Thực hiện ĐÚNG Giai đoạn N theo các bước ở mục 0, không làm sang giai
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
là: dùng được thật → không nhắn trùng → cá nhân hoá có bằng chứng → đẹp. Bản hẹp mà chắc tốt hơn bản rộng mà
dở dang.

| # | Đề bài yêu cầu | Công cụ phải làm | GĐ |
|---|---|---|---|
| R1 | «give it a target segment or seed accounts» | Lối 1: cụm từ khoá, tìm trong phần giới thiệu GitHub ở các nước Đông Nam Á. Lối 2: tài khoản GitHub hạt giống, tìm người được nhiều hạt giống cùng theo dõi. Lối 3: nhập đúng tên tài khoản GitHub | 3 |
| R2 | «finds people and explains why they fit» | Điểm chấm bằng luật, mỗi lý do trỏ về phần giới thiệu, vị trí hoặc một repo có thật | 3, 4 |
| R3 | «drafts personalised DMs for us to review and approve» | Bản nháp đặt cạnh bằng chứng; sửa, duyệt, từ chối. Chưa duyệt thì không gửi | 4, 6 |
| R4 | «real evidence, not invented familiarity» | Mỗi câu trích phải khớp nguyên văn nguồn; không khớp thì không cho duyệt | 4 |
| R5 | «sends approved messages from our connected account within X's rules and limits» | Kênh tay: người gửi từ tài khoản X của mình, công cụ ghi nhận. Kênh API: đăng nhập OAuth, gửi qua X API. Cả hai có trần 24 giờ | 5 |
| R6 | «never double-messages anyone» | Ràng buộc UNIQUE theo người (mã GitHub và tên X) + giữ chỗ nguyên tử + không tự gửi lại khi kết quả mơ hồ | 2b, 5 |
| R7 | «what was sent, who replied and what needs our attention» | Tab Track: đã gửi · đã trả lời · cần chú ý | 5, 6 |
| R8 | «use it without you beside us», cài dưới 15 phút | README; lệnh `doctor` tự kiểm cấu hình; chế độ giả lập không cần khoá; chạy không cần khoá X | 2b, 7 |
| R9 | «Make limitations and blocked actions clear» | Hành động nào bị chặn đều hiện lý do và cách gỡ | 5, 6 |
| R10 | «Test real sending only with accounts you control» | Danh sách cho phép gửi, bật mặc định, áp cho **cả hai kênh** | 5 |
| R11 | «Do not … include secrets in your submission» | Khoá chỉ nằm trong `.env` ngoài git; quét trước khi nộp | 7 |
| R12 | «Keep costs low and name any paid tools» | Mặc định 0 USD; ghi rõ chi phí của kênh API và Claude; sổ ghi chi phí thật | 7 |
| R13 | Video 3–5 phút, bài viết một trang | Kịch bản quay và bản nháp bài viết | 7 |

**Năm cái bẫy không ghi trong đề nhưng sẽ bị chấm** («good judgment about platform rules, failures and cost»):

1. **Tin chào mời là vùng xám ở cả X lẫn GitHub.** Công cụ không gửi tự động hàng loạt: người đọc và duyệt
   từng tin, trần gửi thấp, không có tin nhắc lại, có cờ «không liên hệ nữa», cảnh báo khi tin giống tin trước.
   Bài viết nói thẳng là vùng xám và trích luật của GitHub (xem tệp nghiên cứu).
2. **Không biết trước ai nhận được DM** khi không dùng X API. Kênh tay để người thấy ngay trên X. Kênh API đọc
   `receives_your_dm`.
3. **Người đã được nhắn từ trước, ngoài công cụ.** Kênh tay có nút «Already in contact». Kênh API kiểm lịch
   sử hội thoại trước khi gửi.
4. **Trả lời không tự hiện.** Đọc DM qua API tốn tiền và có thể không thấy hội thoại XChat mã hoá. Vì vậy nút
   «Mark replied» là đường chính.
5. **Chỉ tìm được người có ghi tên X trên GitHub** (mẫu đo khoảng một nửa). Bài viết ghi đây là giới hạn,
   kèm việc tiếp theo.

---

## 2. Sự thật về nền tảng (đã kiểm ngày 12/11/2026)

Chi tiết, nguồn và độ chắc: `docs/knowledge/nghien-cuu-0-usd.md`. Những điều mã phụ thuộc trực tiếp:

| Điều | Giá trị |
|---|---|
| X API | Không có gói miễn phí. Đọc user 0,010 · đọc sự kiện DM 0,010 · gửi DM 0,015 USD |
| Đường dẫn soạn DM của X | Cần `recipient_id` là **mã số**, không nhận tên. Vì vậy kênh tay mở `https://x.com/<tên>` |
| GitHub REST | Miễn phí. Token: 5.000 lời gọi/giờ, tìm kiếm 30/phút, tối đa 1.000 kết quả mỗi truy vấn. Hồ sơ có `twitter_username`; ngoài ra có `GET /users/{u}/social_accounts` |
| GitHub tìm kiếm | Qualifier `in:bio`, `location:` dùng được (đã đo: 202 người ghi «machine learning» ở Việt Nam) |
| Ollama | API HTTP tại `http://127.0.0.1:11434`; `POST /api/chat` nhận `format` là JSON schema; `GET /api/tags` liệt kê mô hình đã tải |
| Máy người dùng | RAM 8 GB, CPU đời 2015: chỉ mô hình cỡ 4B, chạy chậm. Tốc độ đo ở GĐ0 quyết định mặc định `ollama` hay `template` |
| Mô hình miễn phí trên mây | **Cấm dùng** (ví dụ Gemini bản miễn phí): điều khoản cho người đọc dữ liệu gửi lên, mà ta gửi hồ sơ người thật |

---

## 3. Thiết kế đã chốt

### Cấu trúc tệp

```
app.py                  Giao diện Streamlit, 4 tab
outreach/
  config.py             Đọc .env; hằng số
  db.py                 Schema, connect(), kv, sổ chi phí
  github.py             GitHubClient (httpx) + FakeGitHub + get_github()
  xclient.py            XClient (httpx): OAuth, lời gọi X API, lỗi có kiểu — chỉ dùng ở kênh API
  fake_x.py             FakeXClient
  auth.py               python -m outreach.auth — đăng nhập X (chỉ kênh API)
  doctor.py             python -m outreach.doctor — tự kiểm cấu hình, token, Ollama
  discover.py           Tìm người: theo cụm từ, theo hạt giống, nhập tên
  fit.py                Nguồn bằng chứng + chấm điểm bằng luật
  llm.py                Soạn tin (template / ollama / anthropic), kiểm bằng chứng, cảnh báo
  review.py             Sửa, duyệt, từ chối bản nháp
  sender.py             Giữ chỗ, kênh tay, kênh API, trạng thái, mục cần chú ý
tests/                  conftest.py + một tệp test cho mỗi mô-đun + test_app_smoke.py
docs/                   assignment.md · tệp này · knowledge/ · bao_cao/ · writeup.md · demo_script.md
.env.example · .gitignore · requirements.txt · README.md
```

### Cơ sở dữ liệu (SQLite, tạo trong `db.init_db`)

```sql
CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL);   -- token OAuth (kênh API), «me»

CREATE TABLE IF NOT EXISTS campaigns (
  id INTEGER PRIMARY KEY, name TEXT NOT NULL,
  segment TEXT NOT NULL,          -- mô tả người cần tìm, đưa cho mô hình
  keywords TEXT NOT NULL,         -- cụm từ, cách nhau bằng dấu phẩy: dùng để tìm VÀ để chấm điểm
  sender_context TEXT NOT NULL,   -- chúng tôi là ai và muốn gì ở cuộc trò chuyện
  created_at TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS prospects (
  id TEXT PRIMARY KEY,            -- 'gh:<mã số GitHub>' — không đổi khi người đó đổi tên
  github_login TEXT NOT NULL,
  x_username TEXT NOT NULL UNIQUE COLLATE NOCASE,   -- không có '@'; hai tài khoản GitHub cùng tên X = một người
  x_user_id TEXT,                 -- mã số X; chỉ điền ở kênh API
  name TEXT, bio TEXT, location TEXT, company TEXT, followers INTEGER,
  can_dm INTEGER,                 -- receives_your_dm: 1 / 0 / NULL (chưa biết; kênh tay luôn NULL)
  campaign_id INTEGER NOT NULL REFERENCES campaigns(id),
  source TEXT NOT NULL,           -- 'segment:<truy vấn>' | 'seed:<login,...>' | 'import'
  fit_score INTEGER, fit_category TEXT, fit_reasons TEXT,   -- JSON [{claim, source_id}]
  do_not_contact INTEGER NOT NULL DEFAULT 0,
  fetched_at TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS repos (
  source_id TEXT PRIMARY KEY,     -- 'repo:<owner>/<name>'
  prospect_id TEXT NOT NULL REFERENCES prospects(id),
  name TEXT NOT NULL, description TEXT,
  topics TEXT NOT NULL DEFAULT '[]',   -- JSON
  stars INTEGER NOT NULL DEFAULT 0, pushed_at TEXT, url TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY,
  prospect_id TEXT NOT NULL UNIQUE REFERENCES prospects(id),   -- mỗi người đúng một dòng, mãi mãi
  text TEXT NOT NULL,
  evidence TEXT NOT NULL,         -- JSON [{source_id, quote}]
  evidence_ok INTEGER NOT NULL, edited INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL CHECK (status IN
    ('draft','approved','rejected','sending','sent','failed','blocked','unknown')),
  channel TEXT CHECK (channel IN ('manual','api')),   -- ghi lúc giữ chỗ
  error TEXT, dm_event_id TEXT, dm_conversation_id TEXT,
  claimed_at TEXT, sent_at TEXT,
  reply_text TEXT, replied_at TEXT,   -- reply_text: ghi chú của người khi bấm «Mark replied»
  handled_at TEXT, created_at TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS usage (ts TEXT NOT NULL, kind TEXT NOT NULL, units INTEGER NOT NULL, cost_usd REAL NOT NULL);
```

`source_id` ở mọi nơi là `"bio"`, `"location"` hoặc `"repo:<owner>/<name>"`. Mốc thời gian là chuỗi UTC
ISO-8601, chỉ tạo ở `db.now()`. Bảng `posts` của bản 1 bị bỏ.

### Vòng đời một tin nhắn

```
draft ─duyệt→ approved ─giữ chỗ→ sending
  └─từ chối→ rejected

Kênh tay   sending ─«I sent it»─────────→ sent ─«Mark replied»→ sent + replied_at
           sending ─«Not sent»──────────→ approved   (bỏ giữ chỗ, không tính vào trần)
           sending ─«Already in contact»→ blocked    lỗi "existing conversation"

Kênh API   sending ─2xx──────────────→ sent
           sending ─403──────────────→ blocked   chắc chắn chưa gửi
           sending ─400 / 401────────→ failed    chắc chắn chưa gửi
           sending ─429──────────────→ approved  chắc chắn chưa gửi
           sending ─timeout / 5xx────→ unknown   KHÔNG tự gửi lại
```

Ba luật không được phá:
1. Chỉ `approved` mới được giữ chỗ.
2. Đổi `approved → sending` bằng một câu `UPDATE … WHERE id=? AND status='approved'`, kiểm `rowcount == 1`,
   và **commit trước khi** trả đường dẫn X cho người hoặc gọi X API.
3. `sending` ở kênh tay và `unknown` chỉ rời trạng thái khi người bấm chọn.

### Cấu hình (`.env.example`, chú thích trong tệp viết bằng tiếng Anh)

```
X_MODE=fake                 # fake: sample data, no network, no keys · real: live GitHub (+ X when SEND_CHANNEL=api)
GITHUB_TOKEN=               # fine-grained token, public repositories read-only; required when X_MODE=real
SEND_CHANNEL=manual         # manual: you press Send in X yourself ($0) · api: send via X API (paid credits)
X_CLIENT_ID=                # only for SEND_CHANNEL=api
X_CLIENT_SECRET=
X_REDIRECT_URI=http://127.0.0.1:8765/callback
LLM_PROVIDER=ollama         # ollama: local model ($0) · template: no model ($0) · anthropic: Claude API (paid)
OLLAMA_MODEL=qwen3:4b
ANTHROPIC_API_KEY=          # only for LLM_PROVIDER=anthropic
LLM_MODEL=claude-fable-5-2
LLM_PRICE_IN=0              # USD per million input tokens — copy from Anthropic's pricing page
LLM_PRICE_OUT=0
SEND_MODE=allowlist         # allowlist: only SEND_ALLOWLIST can be contacted · live: any approved prospect (manual channel only; the API channel is always limited to SEND_ALLOWLIST)
SEND_ALLOWLIST=             # comma-separated X usernames
DAILY_SEND_CAP=20
```

Hằng số trong `config.py`:
- `PRICES` — giữ như bản 1.
- `MAX_DM_CHARS = 500` · `MIN_QUOTE_CHARS = 15` · `SCOPES` — giữ như bản 1.
- `OLLAMA_URL = "http://127.0.0.1:11434"` · `MIN_SCORE = 40`.
- `SEA_LOCATIONS = ["Vietnam", "Viet Nam", "Ho Chi Minh", "Hanoi", "Singapore", "Thailand", "Bangkok",
  "Indonesia", "Jakarta", "Malaysia", "Kuala Lumpur", "Philippines", "Manila"]`.
- CSDL: `data/fake.db` khi `X_MODE=fake`, `data/outreach.db` khi `real`.

`X_MODE=fake` nghĩa là: `FakeGitHub` + `FakeXClient` + soạn tin bằng `template`, không ra mạng.

### Những thứ cố ý không làm

Mỗi mục ghi một dòng vào phần «what comes next» của bài viết:
- Tìm người qua X API (có sẵn `search_recent` ở `xclient.py`, chưa nối vào).
- Tìm qua arXiv / OpenAlex.
- Tự dò trả lời qua API, kể cả API XChat.
- Tin nhắc lại tự động.
- Nhiều người dùng · triển khai lên máy chủ · tiến trình chạy nền · ORM.
- Hàng đợi gửi hàng loạt ở kênh API (gửi từng tin một).
- Mô hình trên mây bản miễn phí.

---

## 4. Ràng buộc toàn cục (áp cho mọi giai đoạn)

- Mã, giao diện, README, bài viết: **tiếng Anh**. Báo cáo trong `docs/bao_cao/`: tiếng Việt.
- Khoá chỉ nằm trong `.env`. Không in giá trị khoá ra màn hình hay log. Không commit `.env`, `data/`, token.
- **Test không bao giờ ra mạng.** `GitHubClient`, `XClient` và lời gọi Ollama nhận `transport`
  (dùng `httpx.MockTransport`). Anthropic nhận client giả.
- **Chỉ dùng API chính thức.**
  - GitHub qua REST API có token.
  - X chỉ qua đường dẫn hồ sơ cho người bấm, hoặc X API chính thức ở kênh API.
  - Không cào trang, không điều khiển trình duyệt, không API không chính thức.
- **Không mở X, không gửi gì khi chưa có người duyệt.** Không có tin nhắc lại tự động.
- **Hồ sơ người thật chỉ gửi tới mô hình trên máy (Ollama) hoặc API có trả tiền (Anthropic).** Không gửi tới
  dịch vụ mô hình miễn phí trên mây.
- **Trong lúc phát triển:** `SEND_MODE` luôn là `allowlist`, danh sách chỉ chứa tài khoản B của chính mình.
- **Kênh API chỉ gửi cho người trong `SEND_ALLOWLIST`, kể cả khi `SEND_MODE=live`.** Luật tự động hoá của X (mục
  II.C) cấm gửi DM tự động cho người chưa chủ động xin liên lạc, dù có người duyệt từng tin. `SEND_MODE=live` chỉ
  mở kênh tay. Nguồn: `docs/bao_cao/gd-0.md`.
- Tên mô hình Anthropic giữ đúng `claude-fable-5-2` (đổi qua `LLM_MODEL`). Không thay bằng tên mô hình cũ.
- Trước khi viết mã cho một lời gọi API, mở trang tài liệu hiện hành của lời gọi đó. Tài liệu khác tệp này
  thì làm theo tài liệu và ghi vào mục «Lệch so với kế hoạch».
- Môi trường: `.venv` trong repo; cài bằng `pip install -r requirements.txt` bên trong venv. Không thêm thư
  viện khi chưa hỏi.
- Mỗi nhiệm vụ một commit. Cuối giai đoạn gắn tag `gd-N`.

---

## 5. Trọng tâm rà soát

Tình huống đề bài không nói ra nhưng người dùng thật sẽ gặp. Claude soi kỹ nhất các test ghi trong ngoặc.

1. **Bấm hai lần, mở hai tab, hoặc tắt ứng dụng giữa lúc gửi.** Mong đợi: không ai nhận hai tin. Tin kênh
   tay đang `sending` vẫn hiện ở mục cần chú ý sau khi mở lại.
   (`test_open_twice_second_is_blocked`, `test_claim_is_atomic`, `test_recover_stuck_only_touches_api_channel` — GĐ5)
2. **X không trả lời kịp sau khi đã nhận lệnh gửi (kênh API).** Mong đợi: thành `unknown`, không tự gửi lại.
   (`test_api_ambiguous_becomes_unknown_and_is_never_resent` — GĐ5)
3. **Người này đã được nhắn từ trước, ngoài công cụ.** Mong đợi: bị chặn với lý do «existing conversation».
   (`test_confirm_existing_conversation_blocks`, `test_api_prior_conversation_blocks` — GĐ5)
4. **Một người có hai tài khoản GitHub cùng ghi một tên X, hoặc đổi tên.** Mong đợi: vẫn một người, một tin.
   (`test_one_x_account_per_prospect` — GĐ2b; `test_same_x_handle_from_two_github_accounts_is_one_prospect` — GĐ3)
5. **Bio hoặc mô tả repo chứa câu lệnh cài cắm, emoji, chữ không phải Latin.** Mong đợi: mô hình coi đó là
   dữ liệu; kiểm bằng chứng vẫn đúng.
   (`test_untrusted_text_is_wrapped`, `test_verify_evidence_unicode` — GĐ4)
6. **Từ khoá ngắn khớp nhầm.** Ví dụ «ai» nằm trong «maintainer». Mong đợi: khớp theo ranh giới từ.
   (`test_keyword_match_is_word_boundary` — GĐ4)
7. **GitHub báo hết lượt gọi giữa chừng.** Mong đợi: người đã tìm được vẫn được lưu; báo rõ giờ được gọi
   lại. (`test_rate_limited_raises_with_reset` — GĐ3)

---

## Giai đoạn 0 — Việc của người (Antigravity không làm được)

- [x] Gửi thư xác nhận tham gia tới `hr@genaifund.ai` (người dùng báo đã gửi ngày 12/11).
- [ ] **Token GitHub:** GitHub → Settings → Developer settings → Fine-grained tokens → Generate. Chọn quyền
      chỉ đọc repo công khai («Public repositories (read-only)»). Điền vào `.env` (`GITHUB_TOKEN=`), không dán
      vào khung trò chuyện.
- [ ] **Ollama:** cài từ `ollama.com`. Chạy `ollama pull qwen3:4b`, rồi chạy:
      `ollama run qwen3:4b --verbose "Write a friendly 3-sentence message to a robotics engineer. /no_think"`.
      Báo cho Claude dòng `eval rate`. Dưới khoảng 3 token/giây thì đặt mặc định `LLM_PROVIDER=template`.
- [ ] **Tài khoản X:** A để gửi (đăng nhập sẵn trên trình duyệt), B để nhận thử. B theo dõi A hoặc mở DM.
- [ ] **Hồ sơ GitHub cho lần thử thật:** trên một tài khoản GitHub do bạn kiểm soát, thêm tài khoản X **B**
      vào hồ sơ (ô X/Twitter hoặc «Social accounts»). Kiểm bằng cách mở
      `https://api.github.com/users/<login>`: trường `twitter_username` phải là tên B. Không thấy thì mở
      `https://api.github.com/users/<login>/social_accounts`. Cả hai đều không có thì báo Claude.
- [ ] **Thử tay:** mở `https://x.com/<tên một người chưa theo dõi A>`. Nút «Message» có hiện và mở được khung
      soạn tin không?
- [ ] **Đọc luật:** mở `help.x.com/en/rules-and-policies/x-automation`, chép các câu về Direct Messages vào
      `docs/bao_cao/gd-0.md`. Bài viết cuối cần trích.
- [ ] **Xoá `data/fake.db`.** Đây là dữ liệu mẫu, schema đổi ở GĐ2b, tệp sẽ tự tạo lại.
- [ ] Không cần: tài khoản X Developer, credit X, khoá Anthropic. Chỉ cần khi muốn bật kênh API hoặc Claude.

---

## Giai đoạn 1 — Khung dự án và cơ sở dữ liệu — ĐÃ ĐẠT (`gd-1-ok`)

Xem `docs/bao_cao/gd-1.md` và `gd-1-ra-soat.md`. Schema đổi ở GĐ2b.

---

## Giai đoạn 2 — Kết nối X — mã ĐÃ VIẾT (`gd-2`), chưa đạt; sửa ở GĐ2b

Đã có:
- `xclient.py`: `XClient` với lỗi có kiểu `XError`, `RateLimited`, `AuthError`, `Forbidden`, `Ambiguous`,
  xoay vòng token ghi xuống CSDL trước khi gọi, 8 phương thức, `get_x`.
- `fake_x.py`: `FakeXClient` (`sent`, `inbox`, `fail_next`).
- `auth.py`: đăng nhập PKCE.
- `doctor.py`.

Kênh API ở GĐ5 dùng: `me`, `users_by_usernames`, `send_dm`, `dm_events_with`. Các phương thức còn lại giữ
nguyên, không dùng.

Bước 2.4 (thử thật với X API) **bỏ**: không có credit. Thay bằng lần thử thật 0 USD ở bước 7.1. Kênh API
được ghi rõ là «tested with mocks only» trong README và bài viết.

## Giai đoạn 2b — Sửa sau rà soát, đổi khoá hồ sơ, cấu hình mới

**Tệp sửa:** `docs/bao_cao/gd-2.md` · `outreach/auth.py` · `outreach/doctor.py` · `outreach/fake_x.py` ·
`outreach/db.py` · `outreach/config.py` · `.env.example` · `tests/conftest.py` · `tests/test_db.py` ·
`tests/test_config.py` · `tests/test_doctor.py` · `tests/test_xclient.py`

Đọc `docs/bao_cao/gd-2-ra-soat.md` trước. Mỗi mục dưới đây một commit, có test thì viết test trước.

- [ ] **2b.1 Báo cáo** (rà soát mục 1). Sửa `gd-2.md`:
  - Bỏ đoạn «Lưu ý đặc biệt … chỉ đạo của người dùng».
  - Ghi nhãn `X_MODE=fake` cho output `doctor`.
  - Chuyển bốn câu hỏi mở sang «Chưa kiểm được», ghi: «không còn cần cho hướng 0 USD; kênh API chưa thử
    với X thật».
- [ ] **2b.2 `login` lấy `me`** (rà soát mục 2). Sau `handle_callback`, gọi `XClient(conn, transport).me()`,
      in «Connected as @…», trả kết quả. Thêm tham số `transport` cho `login`.
      Test `test_login_fetches_and_returns_me`: giả `HTTPServer` trả callback hợp lệ; `MockTransport` trả
      token và `/2/users/me`.
- [ ] **2b.3 Hộp thư giả rỗng** (rà soát mục 4). `self.inbox = []`. Test `test_fake_inbox_starts_empty`.
- [ ] **2b.4 Bỏ `--spend` và `--check-reply` khỏi `doctor`**, cùng hai test của chúng. Hai lệnh này đọc X API
      trả tiền và không còn trong phạm vi. Mục 5 và 6 của bản rà soát nhờ vậy không còn phải sửa.
      Giữ `--dm-test` cho kênh API.
- [ ] **2b.5 Cấu hình mới.**
  - Thêm `GITHUB_TOKEN`, `SEND_CHANNEL` (`manual`/`api`, kiểm bằng `validate_choice`), `LLM_PROVIDER`
    (`ollama`/`template`/`anthropic`, kiểm bằng `validate_choice`), `OLLAMA_MODEL`, và các hằng số
    `OLLAMA_URL`, `MIN_SCORE`, `SEA_LOCATIONS` (mục 3).
  - Cập nhật `.env.example` và phần ghim giá trị trong `conftest.py`. Ghim: `SEND_CHANNEL=manual`,
    `LLM_PROVIDER=template`, `GITHUB_TOKEN=""`.
  - Test: `test_module_load_fails_on_invalid_send_channel`, `test_module_load_fails_on_invalid_llm_provider`,
    cùng kiểu với test `X_MODE` đang có.
- [ ] **2b.6 `doctor` theo chế độ** (rà soát mục 3).
  - Bước kiểm `.env` coi giá trị rỗng là thiếu.
  - Danh sách bắt buộc:
    - `X_MODE=real` → `GITHUB_TOKEN`.
    - `SEND_CHANNEL=api` → `X_CLIENT_ID`, `X_CLIENT_SECRET`.
    - `LLM_PROVIDER=anthropic` → `ANTHROPIC_API_KEY`.
  - Bước kiểm kết nối X chỉ chạy khi `SEND_CHANNEL=api`.
  - Test: `test_doctor_env_check_fails_on_empty_keys` (`X_MODE=real`, `GITHUB_TOKEN=""` → `FAIL`, mã thoát
    khác 0) và `test_doctor_manual_channel_skips_x_check` (kênh tay không gọi `x.me()`).
- [ ] **2b.7 Đổi schema** theo mục 3: `prospects` khoá `id`, bảng `repos` thay `posts`, `messages.prospect_id`,
      cột `channel`.
  - Sửa các test `test_db.py` đang dùng `x_user_id`.
  - Thêm `test_one_x_account_per_prospect`: hai hồ sơ khác `id`, cùng `x_username` khác hoa thường →
    `sqlite3.IntegrityError`.
- [ ] **2b.8** `pytest -q` → **45 passed** (40 − 2 bỏ ở 2b.4 + 7 mới). Dán output vào cuối `gd-2.md`, cập
      nhật `trang_thai.md`, commit, gắn tag `gd-2b`, DỪNG.

**Xong khi:** 45 test qua; `gd-2.md` không còn câu trả lời suy đoán.

---

## Giai đoạn 3 — Tìm người qua GitHub

**Tệp tạo:** `outreach/github.py` · `outreach/discover.py` · `tests/test_github.py` · `tests/test_discover.py`.
**Tệp sửa:** `outreach/doctor.py` · `tests/test_doctor.py`.

**Tạo ra:**

```python
# outreach/github.py — gốc https://api.github.com; header Authorization: Bearer <token>,
# Accept: application/vnd.github+json, X-GitHub-Api-Version: 2022-11-28
class GitHubError(Exception): status: int; detail: str
class GitHubRateLimited(GitHubError): reset_at: int     # từ x-ratelimit-reset
class GitHubAuthError(GitHubError)                      # 401: token sai hoặc hết hạn

class GitHubClient:
    def __init__(self, transport: httpx.BaseTransport | None = None)
    def search_users(self, query: str, limit: int = 100) -> list[str]       # login; per_page=100, phân trang đến limit (≤ 1000)
    def user(self, login: str) -> dict | None                               # None khi 404
        # {gh_id, login, name, bio, location, company, followers, x_username}
        # x_username: twitter_username; rỗng thì tìm ở /users/{login}/social_accounts
        # (provider "twitter" hoặc url thuộc x.com / twitter.com); bỏ '@' và khoảng trắng; không có → None
    def repos(self, login: str, limit: int = 5) -> list[dict]               # type=owner, sort=pushed, bỏ fork
        # {source_id: 'repo:<owner>/<name>', name, description, topics, stars, pushed_at, url}
    def following(self, login: str, limit: int = 500) -> list[str]          # login

class FakeGitHub      # cùng 4 phương thức; 6 người mẫu: 4 có tên X (2 hợp, 1 hợp nhưng repo không mô tả, 1 không liên quan), 2 không có tên X
def get_github()      # FakeGitHub khi X_MODE=fake, ngược lại GitHubClient

# outreach/discover.py
def search_queries(phrases: list[str], locations: list[str] = config.SEA_LOCATIONS) -> list[str]
def discover_by_segment(conn, gh, campaign_id: int, phrases: list[str], max_people: int = 30) -> dict
def import_logins(conn, gh, campaign_id: int, logins: list[str]) -> dict
def seed_scores(following: dict[str, list[str]], min_seeds: int) -> list[tuple[str, float]]
def discover_by_seeds(conn, gh, campaign_id: int, seed_logins: list[str], min_seeds: int = 2, max_people: int = 30) -> dict
# ba hàm discover / import trả {"new": n, "existing": n, "no_x_handle": n, "checked": n}
```

Luật:
- **Lỗi GitHub:**
  - 401 → `GitHubAuthError`.
  - 403 hoặc 429 có `x-ratelimit-remaining: 0` hoặc `retry-after` → `GitHubRateLimited`.
  - 4xx khác, 5xx, mất mạng → `GitHubError`. Đọc dữ liệu nên an toàn để người bấm lại; không tự thử lại.
- **`search_queries`:** mỗi cặp cụm từ × địa điểm thành `"<cụm từ>" in:bio location:<địa điểm>`. Địa điểm có
  khoảng trắng thì đặt trong ngoặc kép. Ví dụ `"machine learning" in:bio location:"Ho Chi Minh"`.
- **Lưu một người:** `user()` → không có `x_username` thì đếm `no_x_handle`. Đã có `id` hoặc `x_username`
  trong CSDL thì đếm `existing` và **không ghi đè gì**. Còn lại: chèn hồ sơ và tối đa 5 repo trong một giao
  dịch, đếm `new`.
- **Dừng sớm:** `discover_*` dừng khi đủ `max_people` hồ sơ `new`. Gặp `GitHubRateLimited` thì giữ những gì
  đã lưu và ném lỗi tiếp lên trên.
- **`seed_scores`** (WTF rút gọn, xem tệp nghiên cứu):
  - `điểm(c) = Σ 1/len(following[s])`, cộng trên mọi hạt giống `s` có theo dõi `c`.
  - Chỉ giữ ứng viên được ít nhất `min_seeds` hạt giống theo dõi; bỏ chính các hạt giống.
  - Sắp giảm dần; bằng điểm thì xếp theo `login`.
  - Chỉ có 1 hạt giống thì `discover_by_seeds` dùng `min_seeds=1`.
- **`import_logins`** thêm đúng những tài khoản được nhập, `source='import'`. Đây là lối đưa tài khoản B vào ở
  bước 7.1.
- **`doctor`** thêm bước: `X_MODE=real` thì gọi `GET /rate_limit` (không tính vào hạn mức). In `PASS` kèm số
  lượt còn lại, hoặc `FAIL` kèm cách sửa token.

- [ ] **3.1** Viết test, chạy thấy hỏng.

  `tests/test_github.py` (`MockTransport`):
  - `test_search_users_paginates_and_caps` — 2 trang, `limit=150` → 150 login; tham số `per_page=100`, `page=1,2`.
  - `test_user_normalizes_x_handle` — `" @Alice_X "` → `"Alice_X"`.
  - `test_user_falls_back_to_social_accounts` — `twitter_username` rỗng, `social_accounts` có
    `https://x.com/bob` → `"bob"`.
  - `test_user_without_any_x_handle` — cả hai rỗng → `x_username is None`.
  - `test_repos_skips_forks_and_builds_source_ids`.
  - `test_rate_limited_raises_with_reset` — 403 + `x-ratelimit-remaining: 0` + `x-ratelimit-reset:
    1700000000` → `reset_at == 1700000000`; 429 cũng vậy.
  - `test_bad_token_raises_autherror`.
  - `test_token_sent_as_bearer_header` — token nằm ở header, không nằm trong URL.
  - `test_fake_github_has_same_methods` — so `inspect.signature`.

  `tests/test_discover.py` (`FakeGitHub`):
  - `test_search_queries_quote_multiword`.
  - `test_people_without_x_handle_are_skipped_and_counted`.
  - `test_segment_saves_prospect_with_repos`.
  - `test_known_prospect_not_overwritten` — `do_not_contact=1` giữ nguyên sau khi tìm lại; `new == 0`.
  - `test_same_x_handle_from_two_github_accounts_is_one_prospect`.
  - `test_import_logins_adds_exact_accounts`.
  - `test_seed_scores_degree_normalized` — `s1` theo dõi `{a, b}`, `s2` theo dõi `{a, c, d, e}`,
    `min_seeds=2` → đúng `[("a", 0.75)]`.
  - `test_discovery_stops_at_max_people`.

  `tests/test_doctor.py`:
  - `test_doctor_fails_on_bad_github_token`.
- [ ] **3.2** Viết `github.py`, `discover.py`, sửa `doctor.py` cho test qua. `pytest -q` → **63 passed**. Commit.
- [ ] **3.3 Kiểm thật, 0 USD.** `X_MODE=real`, có `GITHUB_TOKEN`. Chạy `discover_by_segment` với cụm từ
      `["robotics", "machine learning"]`, `max_people=10`. Dán vào báo cáo: bộ đếm trả về, số repo đã lưu,
      thời gian chạy. **Không dán tên hay bio của người thật** vào báo cáo; dán số đếm thôi.

**Xong khi:** 63 test qua; báo cáo có số đếm của lần chạy thật.

---

## Giai đoạn 4 — Chấm điểm, soạn tin, kiểm bằng chứng

**Tệp tạo:** `outreach/fit.py` · `outreach/llm.py` · `outreach/review.py` · `tests/test_fit.py` ·
`tests/test_llm.py` · `tests/test_review.py`. **Tệp sửa:** `outreach/doctor.py` · `tests/test_doctor.py` ·
`outreach/fake_x.py` (xoá `fake_llm`, vì `template` thay thế nó).

**Tạo ra:**

```python
# outreach/fit.py
def sources_for(prospect: dict, repos: list[dict]) -> dict[str, str]
    # {"bio": bio, "location": location, "repo:o/n": "<name>: <description>"}; bỏ nguồn rỗng
def keyword_hits(text: str, keywords: list[str]) -> list[str]     # casefold, khớp theo ranh giới từ (\b)
def score_fit(prospect: dict, repos: list[dict], keywords: list[str], today: str) -> dict
    # {score: 0..100, category: 'founder'|'researcher'|'builder', reasons: [{claim, source_id}]}
def score_campaign(conn, campaign_id: int, today: str | None = None) -> int   # số hồ sơ vừa chấm

# outreach/llm.py
class LLMUnavailable(Exception)
Drafter = Callable[[str, dict, dict[str, str], dict], dict]   # (sender_context, prospect, sources, fit) -> {text, evidence}
def get_drafter(conn) -> Drafter          # template khi X_MODE=fake hoặc LLM_PROVIDER=template; ollama; anthropic
def template_draft(sender_context, prospect, sources, fit) -> dict
def ollama_call(system: str, user: str, schema: dict, transport=None) -> dict
def anthropic_call(conn, client=None) -> Callable[[str, str, dict], dict]
def build_prompt(sender_context, prospect, sources, fit) -> tuple[str, str]   # (system, user)
def verify_evidence(evidence: list[dict], sources: dict[str, str]) -> bool
def draft_problems(text: str, other_texts: list[str]) -> list[str]   # cảnh báo, không chặn
def draft_for_campaign(conn, drafter: Drafter, campaign_id: int, min_score: int = config.MIN_SCORE, limit: int = 20) -> int

# outreach/review.py
def set_text(conn, message_id: int, text: str) -> None      # edited=1; chỉ khi status ∈ draft, rejected, failed
def approve(conn, message_id: int) -> str | None            # None = đã duyệt; chuỗi = lý do từ chối
def reject(conn, message_id: int) -> None
```

### Luật chấm điểm (không dùng mô hình)

Hằng số đặt đầu `fit.py`.

| Bằng chứng | Điểm | Lý do ghi lại |
|---|---|---|
| Mỗi từ khoá chiến dịch khớp trong bio | +20, tối đa 40 | `source_id` `"bio"` |
| Mỗi repo có tên / mô tả / chủ đề khớp từ khoá | +15, tối đa 45 | `source_id` là repo đó |
| Có repo được đẩy mã trong 90 ngày tính đến `today` | +10 | một lý do |
| Repo nhiều sao nhất có ≥ 50 sao | +5 | một lý do |
| `location` chứa một mục của `SEA_LOCATIONS` | +10 | `source_id` `"location"` |

- Tổng tối đa 100.
- **Không có từ khoá nào khớp (ở bio lẫn repo) thì điểm là 0.** Phải có bằng chứng liên quan, hoạt động và
  sao không đủ.
- Phân loại theo bio + company, ưu tiên theo thứ tự:
  - `founder|co-?founder|ceo|cto` → `founder`
  - `phd|researcher|professor|postdoc|research scientist` → `researcher`
  - còn lại → `builder`

### Luật soạn tin

- **`template_draft`:**
  - Lấy mô tả repo điểm cao nhất có từ khoá khớp làm câu trích, nguyên văn, cắt tối đa 120 ký tự ở ranh
    giới từ. Không có thì lấy một câu trong bio.
  - Không có câu nào đủ `MIN_QUOTE_CHARS` → `LLMUnavailable("no quotable evidence")`.
  - Khuôn: `Hi {tên đầu, hoặc "there"}, I came across {repo} on GitHub: "{trích}". {sender_context} What are
    you focusing on next?`
- **`ollama_call`:** `POST {OLLAMA_URL}/api/chat` với `{"model", "messages", "stream": false, "format":
  <schema>, "options": {"temperature": 0.3}}`.
  - Nếu tài liệu hiện hành có tham số tắt suy nghĩ (`think`) thì đặt `false`.
  - Timeout 300 giây. Đọc `message.content` rồi phân tích JSON.
  - Không kết nối được → `LLMUnavailable("Ollama is not running at … — start it or set LLM_PROVIDER=template")`.
- **`anthropic_call`:** giữ luật bản 1. Ép JSON bằng `tools` + `tool_choice`. Ghi `usage.input_tokens` và
  `usage.output_tokens` vào sổ (`llm_in`, `llm_out`).
- **`build_prompt`:**
  - Bio và repo đặt trong `<profile>` và `<repo id="repo:…">`. Lời nhắc hệ thống nói rõ nội dung trong thẻ là
    dữ liệu, không phải chỉ dẫn.
  - Yêu cầu: tối đa 500 ký tự; câu đầu nhắc một điều cụ thể lấy từ bằng chứng; một câu nói rõ người gửi là
    GenAI Fund; kết bằng một câu hỏi mở.
  - Cấm: đường dẫn, hashtag, nói đã gặp / đã quen / đã theo dõi lâu, số liệu không có trong nguồn.
  - Đầu ra theo schema `{text, evidence: [{source_id, quote}]}`.
- **`verify_evidence`** đúng khi:
  - danh sách không rỗng;
  - mỗi `source_id` có trong `sources`;
  - mỗi `quote` dài ít nhất `MIN_QUOTE_CHARS` và là chuỗi con của nguồn sau khi chuẩn hoá (`casefold`, gộp
    khoảng trắng).
- **`draft_problems`** cảnh báo khi:
  - dài quá `MAX_DM_CHARS`;
  - chứa `http`;
  - chứa cụm tỏ ra quen biết (`big fan`, `long-time`, `we met`, `as discussed`, `following you for`);
  - **giống một tin khác**: Jaccard trên tập từ (casefold) ≥ 0,8 so với bất kỳ `other_texts` nào. Tin dưới 5
    từ thì bỏ qua (học từ Tuitbot).
- **`draft_for_campaign`:**
  - Chỉ xử lý hồ sơ có `fit_score >= min_score`, `do_not_contact=0`, **chưa có dòng nào** trong `messages`.
  - Tạo tin `draft` với `evidence_ok = verify_evidence(...)`.
  - Một hồ sơ gặp `LLMUnavailable` thì bỏ qua hồ sơ đó. Ollama không chạy thì dừng cả lượt và ném lỗi.
- **`approve`:**
  - Chỉ chạy khi status ∈ `draft`, `rejected`, `failed`. Status khác → `"cannot approve from status <status>"`.
  - `evidence_ok=0` và `edited=0` → `"evidence not verified — edit the text first"`.
- **`doctor`** thêm bước (bỏ qua khi `LLM_PROVIDER` ≠ `ollama`): `GET {OLLAMA_URL}/api/tags`. Không kết nối
  được, hoặc thiếu `OLLAMA_MODEL`, thì `FAIL` kèm lệnh sửa (`ollama pull …` hoặc `LLM_PROVIDER=template`).

- [ ] **4.1** Viết test, chạy thấy hỏng.

  `tests/test_fit.py`:
  - `test_bio_keyword_scores_and_cites_bio`
  - `test_repo_keyword_cites_repo_source`
  - `test_score_capped_at_100`
  - `test_no_keyword_scores_zero` — repo mới, nhiều sao, ở Việt Nam, nhưng không khớp từ khoá nào → 0.
  - `test_category_founder_researcher_builder`
  - `test_keyword_match_is_word_boundary` — `"ai"` không khớp `"maintainer"`, `"said"`; khớp `"AI tools"`.

  `tests/test_llm.py`:
  - `test_verify_evidence_accepts_verbatim_quote_ignoring_case_and_spacing`
  - `test_verify_evidence_rejects_invented_quote`
  - `test_verify_evidence_rejects_empty_short_and_unknown_source`
  - `test_verify_evidence_unicode` — trích có emoji và chữ Việt, khớp nguồn → `True`.
  - `test_untrusted_text_is_wrapped` — chuỗi `user` của `build_prompt` chứa bio nằm giữa `<profile>` và
    `</profile>`.
  - `test_draft_problems` — 501 ký tự, `https://`, `big fan` → mỗi tin một cảnh báo; tin sạch → `[]`.
  - `test_near_duplicate_warning` — chỉ khác một từ so với tin trước → có cảnh báo; tin 4 từ → không.
  - `test_template_draft_passes_verification`
  - `test_template_draft_without_quotable_source_raises`
  - `test_ollama_call_sends_schema_and_parses_json` — `MockTransport` kiểm thân request có `format` và
    `stream: false`.
  - `test_ollama_unreachable_gives_clear_error`
  - `test_anthropic_usage_recorded` — client giả, sổ ghi đúng số token.
  - `test_draft_for_campaign_respects_min_score_and_existing_messages`

  `tests/test_review.py`:
  - `test_approve_requires_verified_evidence`
  - `test_edit_then_approve`
  - `test_cannot_edit_after_sent` — `ValueError`.
  - `test_reject`

  `tests/test_doctor.py`:
  - `test_doctor_fails_when_ollama_model_missing`
- [ ] **4.2** Viết mã cho test qua. `pytest -q` → **87 passed**. Commit.
- [ ] **4.3 Kiểm bằng mắt, 0 USD.** Với hồ sơ thật lấy ở 3.3, chạy `score_campaign` và `draft_for_campaign`
      bằng `LLM_PROVIDER` đã chọn ở GĐ0.
      - Dán 3 bản nháp kèm bằng chứng và cảnh báo vào báo cáo; được thay tên người bằng `<name>`.
      - Ghi thời gian soạn mỗi tin.

**Xong khi:** 87 test qua; báo cáo có 3 bản nháp thật và thời gian soạn.

---

## Giai đoạn 5 — Gửi và theo dõi

**Tệp tạo:** `outreach/sender.py` · `tests/test_sender.py`

**Dùng:** `me`, `users_by_usernames`, `send_dm`, `dm_events_with` và các lỗi có kiểu của GĐ2. **Tạo ra:**

```python
class SendBlocked(Exception): reason: str
def sends_in_last_24h(conn) -> int              # status ∈ sending, sent, unknown có claimed_at trong 24 giờ
def check_can_send(conn, message_id: int) -> str | None      # None = được gửi; chuỗi = lý do (tiếng Anh)
def claim(conn, message_id: int, channel: str) -> bool
# kênh tay
def open_manual(conn, message_id: int) -> dict               # {url: "https://x.com/<x_username>", text}
def confirm_manual(conn, message_id: int, outcome: str) -> str   # 'sent' | 'not_sent' | 'existing' → status mới
# kênh API
def send_api(conn, x, message_id: int) -> str                # status mới
def recover_stuck(conn, older_than_s: int = 300) -> int      # chỉ kênh API: sending quá hạn → unknown
def resolve_unknown(conn, message_id: int, was_sent: bool) -> str    # người quyết: sent hoặc failed
# theo dõi
def mark_replied(conn, message_id: int, note: str) -> None
def mark_handled(conn, message_id: int) -> None
def set_do_not_contact(conn, prospect_id: str, value: bool) -> None
def needs_attention(conn) -> list[sqlite3.Row]
```

Luật:
- **`check_can_send`** kiểm theo thứ tự, trả lý do đầu tiên vướng:
  1. status khác `approved` → `"not approved"`
  2. `do_not_contact=1` → `"marked do-not-contact"`
  3. `can_dm=0` → `"recipient does not accept DMs from this account"`
  4. `SEND_MODE=allowlist` mà `x_username` (casefold) ngoài danh sách → `"not on SEND_ALLOWLIST (safety mode)"`
  5. `sends_in_last_24h >= DAILY_SEND_CAP` → `"daily cap reached (N/N)"`
- **`open_manual`:** `check_can_send` → `claim(…, 'manual')` (commit) → trả đường dẫn và nội dung. Bị chặn →
  `SendBlocked(lý do)`. Không ghi gì khác.
- **`confirm_manual`** chỉ chạy khi status là `sending` và `channel='manual'`, ngược lại `ValueError`:
  - `'sent'` → `sent`, ghi `sent_at`.
  - `'not_sent'` → `approved`, xoá `claimed_at` và `channel`.
  - `'existing'` → `blocked`, lỗi `"existing conversation"`.
- **`send_api`:**
  1. `x_username` (casefold) ngoài `SEND_ALLOWLIST` → `SendBlocked("api channel is limited to SEND_ALLOWLIST
     (X automation rules)")`, **ở mọi `SEND_MODE`**, trước khi claim. Rồi `check_can_send` → `claim(…, 'api')` (commit).
  2. Chưa có `x_user_id` thì gọi `users_by_usernames` và lưu `x_user_id`, `can_dm`. Không tìm thấy, hoặc
     `can_dm=0`, thì `blocked`.
  3. `dm_events_with(id, 1)`: có sự kiện → `blocked` `"existing conversation"`. Bước kiểm này lỗi → trả về
     `approved` rồi ném lỗi.
  4. `send_dm` → xử lý theo sơ đồ kênh API ở mục 3.
- **`needs_attention`** gồm:
  - kênh tay đang `sending` (chờ người xác nhận, mọi tuổi);
  - `unknown`, `failed`;
  - `blocked` chưa `handled`;
  - có `replied_at` mà `handled_at` trống.

- [ ] **5.1** Viết `tests/test_sender.py`, chạy thấy hỏng:
  - `test_unapproved_is_never_opened_or_sent` — `draft`, `rejected` → `SendBlocked`; kênh API `len(x.sent) == 0`.
  - `test_open_manual_claims_and_returns_profile_url_and_text`
  - `test_open_twice_second_is_blocked`
  - `test_claim_is_atomic` — hai kết nối tới cùng `file_db`: đúng một `claim` trả `True`.
  - `test_confirm_sent_counts_toward_cap`
  - `test_confirm_not_sent_returns_to_approved_and_frees_cap`
  - `test_confirm_existing_conversation_blocks`
  - `test_confirm_requires_manual_sending_state`
  - `test_daily_cap_blocks` — trần 2, đã có 2 tin trong 24 giờ → lý do chứa `"daily cap"`.
  - `test_allowlist_blocks_strangers_case_insensitive` — áp cho cả `open_manual` và `send_api`.
  - `test_api_channel_requires_allowlist_even_when_live` — `SEND_MODE=live`, người ngoài danh sách: `send_api` →
    `SendBlocked` chứa `"api channel"`, `len(x.sent) == 0`, status vẫn `approved`; `open_manual` cùng người → được mở.
  - `test_do_not_contact_blocks`
  - `test_api_send_happy_path` — tra `x_user_id`, `approved → sent`, có `dm_event_id`, `len(x.sent) == 1`.
  - `test_api_prior_conversation_blocks` — `x.inbox` có sự kiện với người đó → `blocked`, `len(x.sent) == 0`.
  - `test_api_ambiguous_becomes_unknown_and_is_never_resent` — `x.fail_next = Ambiguous(...)` → `unknown`;
    gọi `send_api` lần nữa → `SendBlocked`, `len(x.sent) == 0`.
  - `test_api_403_blocked_400_failed_429_back_to_approved`
  - `test_api_closed_dm_blocks`
  - `test_recover_stuck_only_touches_api_channel` — API cách 10 phút → `unknown`; API cách 1 phút → giữ;
    kênh tay cách 10 phút → giữ `sending`.
  - `test_resolve_unknown` — `was_sent=True → sent`; `False → failed`.
  - `test_mark_replied_and_handled`
  - `test_needs_attention_contents` — đủ các loại; sau `mark_handled` thì mục đó biến mất.
- [ ] **5.2** Viết `sender.py` cho test qua; sửa chú thích `SEND_MODE` trong `.env.example` cho khớp mục 3. `pytest -q` → **108 passed**. Commit.

**Xong khi:** 108 test qua.

---

## Giai đoạn 6 — Giao diện

**Tệp tạo:** `app.py` · `tests/test_app_smoke.py`. `app.py` không chứa luật nghiệp vụ; chỉ gọi hàm đã có.

- **Thanh bên:**
  - nhãn `SAMPLE DATA` hoặc `LIVE`;
  - kênh gửi (`Manual — you send in X` hoặc `X API`; kênh API có «Connected as @…» hoặc nút
    `Connect X account`);
  - cách soạn tin (`template` / `ollama: <model>` / `anthropic`);
  - `Sent in last 24h: n / cap`;
  - chế độ gửi (`ALLOWLIST: only @…` hoặc `LIVE`);
  - `Spend today: $…` (`spend_since`; ở mặc định là `$0.00`).
- **Tab 1 Find:**
  - Biểu mẫu chiến dịch (name, segment, keywords, sender context).
  - Nút `Search GitHub`: hiện số truy vấn sẽ chạy, chạy `discover_by_segment`, hiện bộ đếm, bao gồm «n
    people had no X handle».
  - Ô `Seed GitHub accounts` → nút `Find people they follow`.
  - Ô `Add GitHub accounts` → nút `Add`.
  - Nút `Score`.
  - Bảng hồ sơ: liên kết GitHub, liên kết X, điểm, loại, lý do.
  - Gặp `GitHubRateLimited` thì hiện giờ được gọi lại, theo giờ địa phương.
- **Tab 2 Review:**
  - Nút `Draft next N`, kèm thanh tiến độ, vì Ollama chậm.
  - Mỗi bản nháp hiện:
    - tóm tắt hồ sơ;
    - lý do phù hợp;
    - từng câu trích kèm liên kết repo hoặc hồ sơ GitHub;
    - ô sửa nội dung;
    - cảnh báo từ `draft_problems`;
    - nút `Approve` / `Reject`.
  - `Approve` bị từ chối thì hiện nguyên văn lý do.
- **Tab 3 Send:** danh sách `approved`; mỗi dòng hiện lý do từ `check_can_send` nếu bị chặn.
  - Kênh tay, nút `Start`:
    1. Gọi `open_manual`.
    2. Hiện nội dung trong `st.code` (có nút chép sẵn) và `st.link_button("Open @… on X", url)`.
    3. Hướng dẫn một dòng: «Click Message on their profile, paste, send — then confirm below».
    4. Ba nút `I sent it` / `Not sent` / `Already in contact`.
  - Kênh API: nút `Send via X API`.
- **Tab 4 Track:**
  - Số đã gửi, số trả lời, tỉ lệ.
  - Danh sách **Needs attention**, mỗi mục có hành động phù hợp: ba nút xác nhận kênh tay,
    `It was sent` / `It was not sent`, `Mark replied` (kèm ô ghi chú), `Mark handled`.
  - Bảng nhật ký gửi.
  - Công tắc `Do not contact`.
- **Khi khởi động:** gọi `recover_stuck`.

- [ ] **6.1** Viết `tests/test_app_smoke.py`, chạy thấy hỏng:
  - `test_app_runs_in_fake_mode` — `AppTest.from_file("app.py").run(timeout=30)`; `not at.exception`;
    `len(at.tabs) == 4`.
- [ ] **6.2** Viết `app.py`. `pytest -q` → **109 passed**. Commit.
- [ ] **6.3** Tự đi hết luồng ở `X_MODE=fake`: tìm → chấm → soạn → duyệt → Start → I sent it → Mark replied →
      Mark handled. Chụp một ảnh mỗi tab, đặt vào `docs/bao_cao/` và trỏ tới trong báo cáo.

**Xong khi:** 109 test qua; đi hết luồng ở chế độ giả lập không gặp lỗi.

---

## Giai đoạn 7 — Chạy thật, tài liệu, nộp bài

- [ ] **7.1 Chạy thật từ đầu đến cuối, 0 USD.** Cấu hình: `X_MODE=real`, `SEND_CHANNEL=manual`,
      `SEND_MODE=allowlist`, danh sách chỉ có B. Ghi vào báo cáo từng dòng kèm bằng chứng (status, số đếm,
      ảnh chụp):
  1. Tìm theo cụm từ → có hồ sơ người thật. Không nhắn ai trong số họ.
  2. `Add GitHub accounts` với tài khoản GitHub mang tên B → chấm điểm → có bản nháp với bằng chứng khớp.
  3. Duyệt → `Start` → gửi tay cho B → B nhận được tin → `I sent it`.
  4. `Start` lần hai cho cùng người → bị chặn.
  5. Thử `Start` với một người thật ngoài danh sách → bị chặn đúng lý do. Tin không được mở.
  6. B trả lời → `Mark replied` → hiện ở Needs attention → `Mark handled`.
  7. Tổng chi phí từ bảng `usage`: 0 USD.
- [ ] **7.2 `README.md`** (tiếng Anh):
  - công cụ làm gì;
  - yêu cầu: Python, token GitHub (miễn phí), Ollama + mô hình (miễn phí) hoặc `template`;
  - tuỳ chọn có trả tiền: kênh X API (credit X, quyền App, «tested with mocks only») và Claude;
  - cài đặt đánh số từng bước;
  - dùng thử không cần khoá (`X_MODE=fake`);
  - chuyển sang liên hệ thật (`SEND_MODE=live`) và ý nghĩa của việc đó — chỉ áp cho kênh tay; kênh API luôn chỉ
    gửi trong `SEND_ALLOWLIST` theo luật X;
  - bảng «giới hạn và hành động bị chặn» (lý do hiện ra → cách gỡ);
  - xử lý sự cố;
  - dữ liệu lưu ở đâu: chỉ trong tệp SQLite trên máy.
- [ ] **7.3 Đo thời gian cài đặt:** clone sang thư mục trống, làm đúng theo README, bấm giờ. Phải dưới 15
      phút với `LLM_PROVIDER=template`. Ghi riêng thời gian tải mô hình Ollama.
- [ ] **7.4 `docs/writeup.md`** (tiếng Anh, không quá một trang):
  - cách tiếp cận: vì sao dùng GitHub, gửi tay và mô hình trên máy;
  - đánh đổi: 0 USD và tuân thủ, đổi lại thao tác tay và chỉ tới được người có ghi tên X;
  - luật X và GitHub, lập trường của công cụ;
  - việc tiếp theo (mục 3 «cố ý không làm»);
  - chi phí: 0 USD mặc định; kênh API khoảng 0,035 USD mỗi tin (tra người 0,010 + kiểm hội thoại 0,010 +
    gửi 0,015); Claude theo số token đo được;
  - đã dùng công cụ AI ra sao và kiểm kết quả bằng gì: Claude lập kế hoạch và rà soát, Antigravity viết
    mã, số test, bộ kiểm bằng chứng, người duyệt.

  Mọi con số lấy từ báo cáo, không ước lượng.
- [ ] **7.5 `docs/demo_script.md`:** kịch bản 3–5 phút:
  1. `doctor`
  2. Tìm trên GitHub.
  3. Lý do phù hợp và bằng chứng.
  4. Sửa và duyệt; cho thấy một bản bị từ chối duyệt vì bằng chứng sai.
  5. `Start` → gửi tay cho B → B thấy tin.
  6. Gửi lại bị chặn.
  7. B trả lời → `Mark replied` → Needs attention.
  8. Nói thẳng phần chưa xong (kênh API chưa thử thật).
- [ ] **7.6 Quét trước khi nộp:**
  - `git ls-files` không có `.env`, `data/`, `*.db`.
  - `git grep -nE "sk-ant-|ghp_|github_pat_"` không ra dòng nào.
  - `pytest -q` qua toàn bộ.
- [ ] **Người làm:** quay video, gửi thư nộp bài **trước 11:00 Thứ Ba 17/11/2026**.

**Xong khi:** mọi dòng ở 7.1 có bằng chứng; 7.3 dưới 15 phút; 7.6 sạch.

---

## Lịch

| Ngày | Việc |
|---|---|
| Thứ Năm 12/11 | GĐ1 xong · GĐ2 mã xong · rà soát GĐ2 · đổi hướng 0 USD |
| Thứ Sáu 13/11 | Sáng: GĐ0 (người) · GĐ2b. Chiều: GĐ3 |
| Thứ Bảy 14/11 | GĐ4 · GĐ5 |
| Chủ Nhật 15/11 | GĐ6 · 7.1 |
| Thứ Hai 16/11 | 7.2–7.6 · Claude rà soát tổng · quay video |
| Thứ Ba 17/11 | Sáng: dự phòng · nộp trước 11:00 |

Nếu trễ, cắt theo thứ tự:
1. Lối hạt giống (`discover_by_seeds`). R1 vẫn đạt nhờ lối cụm từ.
2. Kênh API ở GĐ5 và GĐ6.
3. `anthropic_call`.

Không bao giờ cắt: chống nhắn trùng ở GĐ5, kiểm bằng chứng, bước 7.1.
