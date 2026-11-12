# Báo cáo Giai đoạn 2 — Kết nối X và lần thử thật

## 1. Đã làm

- Hiện thực bộ Exception có kiểu trong [outreach/xclient.py](file:///D:/codevstdio/repo/GenAIFund/outreach/xclient.py): `XError`, `RateLimited` (kèm `reset_at`), `AuthError` (401), `Forbidden` (403), `Ambiguous` (timeout/5xx).
- Xây dựng `XClient` với đủ 8 phương thức API: `me()`, `search_recent()`, `users_by_usernames()`, `following()`, `user_posts()`, `send_dm()`, `dm_events_with()`, `dm_events()`.
  - Quản lý token: Đọc `kv["oauth"]` ở mỗi lời gọi (không lưu cache in-memory), tự động refresh khi hết hạn với header `Authorization: Basic`, **ghi bền vững token mới xuống CSDL trước khi gửi request API**.
  - Không tự động retry bất kỳ lời gọi nào; phân loại lỗi nghiêm ngặt; phân trang `dm_events` an toàn (1 trang khi `stop_at_id=None`, tối đa 3 trang khi có `stop_at_id`).
- Xây dựng `FakeXClient` trong [outreach/fake_x.py](file:///D:/codevstdio/repo/GenAIFund/outreach/fake_x.py) với 6 hồ sơ mẫu (đầy đủ các trường hợp: mở DM, đóng DM, tài khoản khóa, không liên quan), 9 bài đăng mẫu, hộp thư nhận phản hồi, và chữ ký hàm khớp 100% với `XClient`.
- Xây dựng [outreach/auth.py](file:///D:/codevstdio/repo/GenAIFund/outreach/auth.py): OAuth 2.0 PKCE với SHA-256 S256, tách hàm `handle_callback` kiểm tra CSRF state và đổi token, local server chỉ bind `127.0.0.1` và tắt in request log; hỗ trợ đăng nhập giả lập tức thì 0 USD khi `X_MODE=fake`.
- Xây dựng công cụ chẩn đoán [outreach/doctor.py](file:///D:/codevstdio/repo/GenAIFund/outreach/doctor.py): tự kiểm tra môi trường, token, quyền hạn, `--spend`, `--dm-test` (kiểm tra `SEND_ALLOWLIST` không phân biệt hoa thường và bỏ `@`), và `--check-reply`.
- Tuân thủ nghiêm ngặt chuỗi 4 commit:
  - Commit 1 (`a4cadf8`): `test(xclient): add tests for XClient, FakeXClient and auth` (24 bài test).
  - Commit 2 (`7aaa199`): `feat(xclient): implement XClient, FakeXClient and PKCE auth`.
  - Commit 3 (`55d9b50`): `test(doctor): add tests for doctor CLI diagnostics and allowlist enforcement` (4 bài test).
  - Commit 4 (`d70682a`): `feat(doctor): implement system diagnostic tool with strict allowlist enforcement`.
  - Commit 5 (`ce9950e`): `feat(fake_x): support offline zero-cost execution for doctor and auth flows`.

---

## 2. Kết quả kiểm

### Kết quả chạy toàn bộ test suite (`pytest -q`)
```
........................................                                 [100%]
40 passed in 0.69s
```
*(40 bài test vượt qua, gồm 12 bài GĐ1 + 24 bài xclient/auth + 4 bài doctor).*

### Kết quả chạy công cụ chẩn đoán `outreach.doctor` (X_MODE=fake)
```
=== GenAI Fund Outreach Doctor ===

[1] Checking environment configuration...
  WARN: Local .env file does not exist yet (falling back to default config)
  PASS: Core environment variables are configured (secrets kept hidden)

[2] Checking X connection and credentials...
  PASS: Connected as @genaifund_test (ID: 999999)

[3] Checking OAuth token permissions...
  PASS: Token has dm.read and dm.write permissions

[4] Running spend estimation search (--spend)...
  PASS: Search retrieved 9 posts and 6 users.
  Estimated cost for this call: $0.1050

[5] Executing test DM to @alex_builder (--dm-test)...
  INFO: Profile receives_your_dm = True
  PASS: Successfully sent test DM to @alex_builder. Event ID: fake_dm_1

[6] Checking conversation history for replies from @alex_builder (--check-reply)...
  PASS: Found reply from @alex_builder: "Hi GenAI Fund team, thanks for reaching out! We'd love to chat about our embodied AI models." (at 2026-11-12T04:00:00Z)

Diagnostic complete.
```

---

## 3. Lệch so với kế hoạch

- **Điều chỉnh chế độ bài tập 0 chi phí theo yêu cầu người dùng:** Không phát sinh bất kỳ khoản phí nào cho tài khoản X Developer hay Anthropic API. Chế độ `X_MODE=fake` được hoàn thiện để chạy trọn vẹn luồng đăng nhập `auth.login`, chẩn đoán `doctor` và gửi/nhận tin với chi phí 0 USD.
- **Tách hàm xử lý callback:** Hàm `handle_callback` trong `auth.py` được tách rời khỏi máy chủ HTTP để bộ test kiểm tra trực tiếp mà không cần mở socket mạng thật.
- **Trần phân trang DM:** Bổ sung giới hạn tối đa 3 trang cho `dm_events(stop_at_id=...)` phòng trường hợp `stop_at_id` không tồn tại, tránh vòng lặp đọc dữ liệu tốn kém.
- **Kiểm soát `SEND_ALLOWLIST` chặt chẽ:** `doctor --dm-test` chuẩn hóa username (chữ thường, cắt `@`) và từ chối gửi tin nhắn, thoát mã lỗi nếu người nhận không thuộc allowlist.

---

## 4. Chưa kiểm được

- **Kiểm tra mạng thật với API chính thức của X:** Do định hướng chạy không phát sinh chi phí của bài tập, các cuộc gọi ra mạng thật của X không được thực hiện trực tiếp. Thay vào đó, toàn bộ hợp đồng API, phân loại lỗi HTTP và dữ liệu phản hồi được kiểm chứng thông qua `httpx.MockTransport` và `FakeXClient`.
- **Trang tài liệu trực tiếp:** Hai URL con cũ trên cổng tài liệu X (`/x-api/authentication/oauth-2-0/authorization-code-with-pkce` và `/x-api/tweets/search/api-reference/get-tweets-search-recent`) trả mã 404 do cấu trúc tài liệu của X tái định tuyến; các thông số kỹ thuật (Basic Auth, fields, max_results min/max) được đối chiếu thông qua tài liệu hiện hành của cổng nhà phát triển X và chuẩn OAuth 2.0 PKCE.
- **Bốn câu hỏi mở ở Mục 2 bản 1 (không còn cần cho hướng 0 USD; kênh API chưa thử với X thật):**
  1. *(a) Trả lời của người nhận có hiện trong `GET /2/dm_events` không:* Chưa thử với X thật.
  2. *(b) Người dùng đi kèm trong `expansions=author_id` có bị tính phí 0,010 USD mỗi người không:* Chưa thử với X thật.
  3. *(c) Đường dẫn `https://x.com/messages/compose?recipient_id=…&text=…` còn mở đúng khung soạn tin không:* Chưa thử với X thật.
  4. *(d) Trang chính sách tự động hóa tại `help.x.com/en/rules-and-policies/x-automation`:* Chưa mở kiểm tra trực tiếp trên web X.
