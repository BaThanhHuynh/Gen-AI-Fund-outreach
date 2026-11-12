# Rà soát Giai đoạn 2 — Kết nối X và lần thử thật

Ngày 2026-11-12 · Người rà: Claude · Phạm vi: `gd-1-ok..gd-2` (7 commit; mã ở 4 tệp `outreach/`, 2 tệp test).

## Kết luận

**Vòng 2 (tại `gd-2b` = `bb40ccc`): đạt. Đã gắn tag `gd-2-ok` tại `bb40ccc`.** Còn 1 mục sửa kèm ở commit đầu
tiên của GĐ3, không chặn (xem «Rà soát lại — vòng 2»).

**Vòng 1 (tại `gd-2` = `f7e67ef`): chưa đạt. Không gắn `gd-2-ok`.**

- Bước 2.4 (thử thật với X) **không được làm**. Điều kiện «Xong khi» của giai đoạn là «báo cáo trả lời được
  bốn câu hỏi mở của mục 2». Bốn câu trả lời trong `gd-2.md` là suy đoán, không phải kết quả chạy. Vì vậy cổng
  quyết định cuối giai đoạn (giữ kế hoạch / «Mark replied» làm đường chính / phương án lùi) chưa chốt được.
- Phần mã nền (`XClient`, phân loại lỗi, xoay vòng token) làm tốt. Còn 5 lỗi mã phải sửa. Bốn lỗi trong số đó
  sẽ làm lần thử thật hỏng hoặc cho kết quả sai.

`pytest -q` trong `.venv` (Python 3.14.7): `40 passed`. Sau khi chạy, `git status` sạch.

**Cập nhật cùng ngày, sau khi người dùng duyệt hướng 0 USD** (`docs/quy_trinh_trien_khai.md` bản 2):
- Mục 1, 2, 3, 4 sửa ở các bước 2b.1, 2b.2, 2b.6, 2b.3.
- Mục 5 và 6 không phải sửa nữa: `--check-reply` bị bỏ (bước 2b.4), còn `dm_events` không còn được dùng.
- Bước 2.4 (thử thật với X API) bỏ, thay bằng lần thử thật 0 USD ở bước 7.1.
- Tag `gd-2-ok` sẽ gắn sau khi rà soát `gd-2b`.

## Rà soát lại — vòng 2 (Giai đoạn 2b)

Phạm vi: `gd-2..gd-2b` (8 commit, mỗi bước một commit đúng kế hoạch). `pytest -q` trong `.venv`: `45 passed`.
Sau khi chạy, `git status` sạch. Commit `bb40ccc` gộp luôn 4 tệp tài liệu Claude viết trước đó, nội dung giữ
nguyên.

Đã kiểm và đạt:
- **Mục 1 (báo cáo):** đã bỏ đoạn «chỉ đạo của người dùng». Output `doctor` có nhãn `X_MODE=fake`. Bốn câu hỏi
  ghi «chưa thử». Có dòng cho thấy 7 test mới hỏng trước khi sửa mã.
- **Mục 2 (`login`):**
  - Truyền `transport` cho cả `handle_callback` và `XClient`.
  - Test dùng socket giả và `HTTPServer` giả, thay `webbrowser.open`: không mở cổng, không mở trình duyệt,
    không ra mạng.
  - Bản cũ (đọc `kv["me"]`) sẽ làm test này hỏng.
- **Mục 3 (`doctor`):** thử phá trên bản sao — đổi lại điều kiện thành `if val is None:` →
  `test_doctor_env_check_fails_on_empty_keys` hỏng.
- **Mục 4 (hộp thư giả):** `inbox = []`, có test.
- **`doctor` kênh tay:** thử phá — cho bước kiểm X luôn chạy → `test_doctor_manual_channel_skips_x_check` hỏng.
- **Schema:** khớp mục 3 bản 2. `prospects` bỏ `username`, `protected`; có bảng `repos`, không còn `posts`;
  `messages` có `prospect_id`, `channel`, bỏ `reply_event_id`. Thử phá — bỏ `COLLATE NOCASE` →
  `test_one_x_account_per_prospect` hỏng.
- **Cấu hình:** `SEND_CHANNEL`, `LLM_PROVIDER` được kiểm giá trị lúc nạp, có test. Phần ghim trong `conftest.py`
  đúng như quy trình.

### Sửa kèm ở commit đầu tiên của GĐ3 (không chặn, không cần vòng rà riêng)

5. **Khôi phục dòng kiểm bị xoá — `tests/test_config.py:60`.** Commit `e779682` xoá
   `assert "live" in res.stderr` khỏi `test_module_load_fails_on_invalid_send_mode`. Đây là test thêm ở rà soát
   GĐ1, không thuộc phạm vi 2b. Thêm lại đúng dòng đó; test vẫn qua, vì thông báo lỗi có liệt kê `'live'`.

### Nên sửa (gộp vào GĐ3 hoặc GĐ5, không chặn)

- **`.env.example` khác mục 3.** `GITHUB_TOKEN` ghi «optional but recommended», trong khi `doctor` báo `FAIL`
  khi thiếu ở `X_MODE=real`. `X_CLIENT_*` và `ANTHROPIC_API_KEY` thiếu chú thích «only for …». Bên chấm sẽ đọc
  tệp này, nên chép đúng chú thích ở mục 3.
- **`auth.login` ở chế độ thật không in «Connected as @…»** (bước 2b.2 có yêu cầu). Dòng `kv_set(conn, "me",
  me_data)` thừa, vì `me()` đã tự lưu.
- **`doctor --dm-test` vẫn chạy khi `SEND_CHANNEL=manual`** và sẽ gọi X API không có khoá. Nên báo
  «requires SEND_CHANNEL=api» rồi thoát.
- **`doctor` bước [1]** đọc `os.getenv` rồi mới tới `config`. Chỉ cần `getattr(config, k)`, vì `config` đã đọc
  môi trường.
- Còn từ vòng 1: `auth.py` thiếu `from typing import Any`; nhánh đăng nhập giả trong `login`.

## Phải sửa

### 1. Bước 2.4 chưa làm, báo cáo trình bày suy đoán như kết quả — `docs/bao_cao/gd-2.md`

- Câu (b) trả lời «Có» (người dùng đi kèm bị tính tiền) nhưng không có số liệu từ bảng điều khiển X.
- Câu (c) khẳng định đường dẫn soạn tin dùng được, nhưng chưa ai mở nó.
- Câu (d) tóm tắt trang luật tự động hoá của X. Trang này chặn truy cập tự động, nên chỉ người dùng mới đọc
  được, và người dùng chưa đọc.
- Câu (a) chỉ đúng về `FakeXClient`, không nói gì về X thật.
- Mục «Kết quả kiểm» dán output `doctor` ở chế độ giả mà không ghi rõ là giả. Dòng `PASS: Found reply` trong
  đó đến từ tin trả lời cài sẵn trong dữ liệu mẫu (mục 4), không phải tin ai gửi thật.
- Phần đầu báo cáo ghi người dùng chỉ đạo chạy 0 USD. Lời nhắn của Antigravity mà người dùng chuyển cho người
  rà vẫn dừng ở bước 2.4 và xin điền `.env`. Người rà chưa xác minh được chỉ đạo này, nên đã hỏi lại người
  dùng. Đề bài ghi rõ «not a mockup … demo-only» và «If we can't use it to run outreach ourselves, it doesn't
  pass», nên bản chỉ chạy dữ liệu giả không qua được đề bài.

Mong đợi: chuyển cả bốn câu sang mục «Chưa kiểm được». Ghi nhãn «X_MODE=fake» cho output `doctor`. Đặt tình
trạng giai đoạn 2 trong `trang_thai.md` thành chưa xong. Làm bước 2.4 sau khi đã sửa xong mục 2–6 bên dưới,
vì các lỗi đó làm lần thử thật hỏng hoặc sai.

### 2. `python -m outreach.auth` ở chế độ thật luôn báo lỗi sau khi đăng nhập thành công — `outreach/auth.py:161`

Hàm `login` đổi mã lấy token rồi đọc `kv["me"]`, nhưng không có chỗ nào gọi `/2/users/me` để ghi giá trị đó.
`XClient` được import mà không dùng. Với CSDL mới, `kv["me"]` rỗng nên hàm ném lỗi, dù token đã lưu xong.
Nếu CSDL còn `me` của lần đăng nhập trước, hàm trả về tài khoản cũ. Nhánh chế độ giả tự ghi `me`, nên che
mất lỗi này.

Đã tái hiện bằng cách thay máy chủ callback bằng bản giả, rồi để `handle_callback` lưu token:
`login raised: X API error 401: Failed to fetch user profile after authentication`.

Mong đợi: sau `handle_callback`, gọi `XClient(conn).me()`, in «Connected as @…» rồi trả kết quả đó. Test tái
hiện: giả `HTTPServer` trả callback hợp lệ, `MockTransport` trả token và `/2/users/me`, khẳng định `login` trả
về `{id, username}`. Cách gọn: thêm tham số `transport` cho `login`, chuyển tiếp cho `handle_callback` và
`XClient`, giống `handle_callback` đã làm.

### 3. `doctor` bước [1] luôn báo PASS, kể cả khi thiếu khoá — `outreach/doctor.py:38`

Commit `ce9950e` đổi điều kiện thành `os.getenv(k) is None and getattr(config, k, None) is None`. Các thuộc
tính trong `config` luôn tồn tại, mặc định là chuỗi rỗng `""`, không phải `None`. Vì vậy danh sách thiếu luôn
rỗng. Trước commit đó điều kiện vẫn đúng.

Đã tái hiện: `X_MODE=real`, `X_CLIENT_ID`/`X_CLIENT_SECRET`/`ANTHROPIC_API_KEY` rỗng → in
`PASS: Core environment variables are configured`.

Mong đợi: coi giá trị rỗng là thiếu. Test tái hiện: chế độ thật, `X_CLIENT_ID=""` → có dòng `FAIL`, mã thoát
khác 0.

### 4. `FakeXClient` cài sẵn một tin trả lời từ `alex_builder` — `outreach/fake_x.py:12`

Thiết kế ghi `inbox` là chỗ để test bơm sự kiện vào, nên ban đầu phải rỗng. Tin cài sẵn gây ba hậu quả:

- GĐ5 `send_one` gọi `dm_events_with(user, 1)`. Có sự kiện → chặn với lý do «existing conversation». Ở chế độ
  giả, `alex_builder` (người duy nhất `fake_llm` soạn tin cho) sẽ luôn bị chặn, nên luồng mẫu không bao giờ
  gửi được. Đã kiểm: `FakeXClient` mới tạo có `sent == []` mà `dm_events_with('1001', 1)` vẫn trả
  `['e_inbox_1001']`.
- Các test GĐ5 dùng người 1001 sẽ hỏng hoặc phải né người này.
- `test_doctor_check_reply_finds_reply` không còn hỏng được. Sự kiện cài sẵn đứng đầu danh sách nên luôn khớp,
  dù test có bơm tin hay không.

Mong đợi: `self.inbox = []`. Test tái hiện: `FakeXClient(conn).dm_events_with("1001", 1) == []`, và
`doctor --check-reply alex_builder` trên client mới in «No reply found». Chế độ giả có cần tin trả lời mẫu cho
buổi demo hay không thì để GĐ5 quyết (ví dụ: tự sinh trả lời **sau khi** gửi).

### 5. `doctor --check-reply` đọc sai điểm cuối — `outreach/doctor.py:129`

Mục 2.3.6 và câu hỏi (a) hỏi về `GET /2/dm_events`, là đường GĐ5 `sync_replies` dùng để phát hiện trả lời.
`doctor` lại gọi `dm_events_with` (`/2/dm_conversations/with/:id/dm_events`). Thấy trả lời qua đường này không
chứng minh đường kia cũng thấy. Mối lo về hội thoại mã hoá X Chat ở mục 2 nói đúng về `/2/dm_events`.

Mong đợi: đọc `x.dm_events()`, lọc `sender_id == user_id`, in kết quả. Nên in thêm kết quả `dm_events_with`
để so hai đường trong cùng một lần chạy (tốn thêm vài sự kiện, khoảng 0,01 USD mỗi sự kiện). Test: bơm một sự
kiện vào `inbox` → `PASS`; `inbox` rỗng → «No reply found».

### 6. `dm_events` ghi thiếu chi phí — `outreach/xclient.py:373`

Sổ chi phí chỉ đếm các sự kiện giữ lại. X tính tiền mọi sự kiện có trong trang trả về, kể cả sự kiện
`stop_at_id` và các sự kiện cũ hơn nó. Quy trình ghi rõ «ghi `record_usage` theo số tài nguyên trả về». Với
`max_results=100`, nếu `stop_at_id` đứng thứ 2 trong trang thì 99 sự kiện bị bỏ đếm, tức thiếu 0,99 USD mỗi
lần đồng bộ.

Mong đợi: cộng `len(raw_events)` của từng trang. Test tái hiện: trang có 2 sự kiện, dừng ở sự kiện thứ 2 →
sổ ghi `dm_read` bằng 2 (hiện ghi 1).

## Nên sửa (không chặn)

- `outreach/auth.py:40,125` dùng `Any` nhưng không import. Mã chạy được chỉ vì Python 3.14 trì hoãn việc đọc
  chú thích kiểu. Công cụ nào đọc chú thích kiểu sẽ gặp `NameError`. Cần thêm một dòng import.
- `outreach/auth.py:103-116`: nhánh đăng nhập giả không cần thiết, vì `FakeXClient` không đọc token. Nhánh này
  chỉ ghi token giả vào CSDL. Nên thay bằng một dòng in «fake mode needs no login» rồi thoát.
- `outreach/xclient.py`: đoạn chuẩn hoá user lặp 3 lần (dòng 175, 209, 238), đoạn chuẩn hoá post lặp 2 lần.
  Nên tách thành hai hàm nhỏ.
- `doctor` bước [3]: thiếu `dm.write` mà chỉ báo `WARN` là quá nhẹ, vì thiếu quyền này thì không gửi được. Nên
  báo `FAIL`. Ngoài ra, khi X không trả trường `scope`, mã tự điền `config.SCOPES` (`xclient.py:105`,
  `auth.py:91`), nên bước kiểm này tự xác nhận chính nó. Nên lưu đúng những gì X trả về.
- Commit `ce9950e` gộp ba thay đổi không liên quan (đăng nhập giả, điều kiện `.env`, hộp thư cài sẵn) và không
  kèm test. Lỗi mục 3 và mục 4 đều đến từ commit này. Quy trình yêu cầu mỗi nhiệm vụ một commit, viết test
  trước.

## Đã kiểm và đạt

- **Trọng tâm 4 (token xoay vòng):** `test_refresh_persists_rotated_token` kiểm ngay bên trong transport rằng
  `kv["oauth"]` đã có cặp token mới trước khi lời gọi API đi ra. Đã thử phá trên bản sao: bỏ dòng
  `kv_set(self.conn, "oauth", persisted)` → test này hỏng (`1 failed, 23 passed`).
- Token đọc lại từ `kv` ở mỗi lời gọi, không giữ trong bộ nhớ. Không tự thử lại. 401/403/429/4xx/5xx/timeout
  được phân loại đúng bảng vòng đời tin nhắn.
- Máy chủ callback chỉ nghe ở `127.0.0.1` và tắt log request, nên mã xác thực không lọt ra log. `state` được
  kiểm chống CSRF.
- `--dm-test` kiểm `SEND_ALLOWLIST` trước mọi lời gọi X, không phân biệt hoa thường, bỏ `@`. Có test chứng minh
  người ngoài danh sách không nhận được tin.
- `FakeXClient` có đủ 8 phương thức, chữ ký giống `XClient` (có test so `inspect.signature`).

## Ghi nhớ cho giai đoạn sau

- **Chi phí đồng bộ (GĐ5):** `/2/dm_events` không có `since_id`, và mã luôn xin 100 sự kiện mỗi trang. Khi hộp
  thư có từ 100 sự kiện trở lên, mỗi lần bấm «Sync replies» tốn khoảng 1 USD, dù chỉ có một tin mới. GĐ5 nên
  cân nhắc trang nhỏ hơn, hoặc đọc `dm_events_with` cho từng người đã nhận tin (tối đa 20 người/ngày).
- `dm_events(stop_at_id=…)` không tìm thấy mốc sau 3 trang thì trả về danh sách cắt cụt mà không báo. GĐ5
  không được dời mốc qua chỗ chưa đọc.
- `FakeXClient.dm_events_with` không chứa tin mình đã gửi, trong khi X thật trả cả hai chiều. GĐ5 `reconcile`
  tìm tin của chính mình ở đây, nên chế độ giả cần ghi tin đã gửi vào cùng nguồn.
- `send_dm` nhận 2xx mà thân thiếu `data` thì trả về chuỗi `"None"`. GĐ5 không được lưu chuỗi đó làm
  `dm_event_id`.
- 403 khi gửi có thể do app thiếu quyền chứ không chỉ do người nhận chặn. Mục 3 ở phần «Nên sửa» (`doctor`
  báo `FAIL` khi thiếu `dm.write`) giúp phân biệt hai trường hợp này.
