# Rà soát Giai đoạn 5 — Gửi và theo dõi

Ngày 2026-11-13 · Người rà: một subagent mới của Claude (không viết mã GĐ5). Nó đọc `git diff gd-4-ok..gd-5`, các mục 3
(«Vòng đời một tin nhắn»), 4, 5 và mục GĐ5 trong `docs/quy_trinh_trien_khai.md`, cùng `docs/bao_cao/gd-5.md`. Claude
phiên chính đối chiếu từng mục với mã rồi sửa.

## Kết luận

**Đạt sau khi sửa. Đã gắn `gd-5-ok`.**

- Tại `gd-5`: `pytest -q` trong `.venv` → `124 passed`. Chạy với plugin chặn mạng (`httpx.HTTPTransport.handle_request`
  và `socket.socket.connect` đều ném lỗi) → `124 passed`, `blocked network attempts: 0`.
- Không có mục phải sửa. Có 5 mục nên sửa (3 ở mã, 2 thiếu test), đã sửa hết trong commit `65526ae`.
- Sau khi sửa: `pytest -q` → `131 passed`. Chạy chặn mạng → `131 passed`, `blocked network attempts: 0`.
- Mọi output trên chạy ở `X_MODE=fake` (conftest ép), X chỉ là `FakeXClient`.

## Phải sửa

Không có. Subagent không tìm thấy kịch bản nào phá ba luật cứng, gửi trùng tin, hay lệch thứ tự và câu chữ lý do của
`check_can_send`.

## Nên sửa — đã sửa luôn (rẻ, chạm đúng chỗ dễ hỏng)

Thấy hỏng trước khi sửa: `pytest -q tests/test_sender.py` → `5 failed, 24 passed` (4 test mới, cộng
`test_needs_attention_contents` đã đổi theo mục 3). Ba test canh giữ (mục 4, 5) qua ngay, vì mã đã đúng.

| # | Lỗi | Tình huống hỏng (subagent đã chạy) | Sửa | Test |
|---|---|---|---|---|
| 1 | Trần gửi trong ngày bị vượt khi hai tab bấm cùng lúc | `DAILY_SEND_CAP=1`, hai tin `approved`. Tab A và B cùng qua `check_can_send`, rồi cả hai `claim` đều `True` → 2 tin trong 24 giờ | Đếm trần ngay trong câu `UPDATE` của `claim`, nên kiểm và giữ chỗ là một bước. `claim` thua thì báo lý do thật (ví dụ `daily cap reached (1/1)`) | `test_daily_cap_holds_when_two_tabs_claim_different_messages` |
| 2 | Lỗi lạ sau khi gửi làm tin «biến mất» | `send_dm` đã gửi xong rồi ném `ValueError` (thân 2xx hỏng). Tin kẹt ở `sending` kênh API, không có trong Needs attention. `recover_stuck` chỉ bắt được sau 5 phút, mà GĐ6 chỉ gọi nó lúc khởi động | Lỗi không phải `XError` ở bước gửi → `unknown`: không biết tin đã đi chưa, nên không bao giờ tự gửi lại | `test_api_unexpected_error_after_send_becomes_unknown` |
| 3 | Trả lời mới bị ẩn nếu tin đã «handled» | Gửi → trả lời → `mark_handled` → người kia trả lời lần hai → `mark_replied` → tin không hiện lại. Tin `unknown` bị `mark_handled` không báo gì, rồi sau đó bị ẩn sẵn | `mark_replied` xoá `handled_at`. `mark_handled` từ chối tin `unknown` và tin đang `sending`, vì hai loại này chỉ rời đi khi người chọn kết quả | `test_new_reply_after_handled_shows_again`, `test_mark_handled_refuses_unknown_and_manual_sending` |
| 4 | Thiếu test: bước kiểm trước khi gửi lỗi → trả về `approved` rồi ném lỗi | Mã đúng (subagent chạy tay), chỉ thiếu test giữ cho đúng về sau | Thêm test, cho cả lỗi tra người dùng và lỗi kiểm hội thoại cũ | `test_api_prior_check_error_returns_to_approved_and_raises` (2 trường hợp) |
| 5 | Thiếu test cho luật cứng 2 ở kênh API: «commit trước khi gọi X» | `test_claim_is_atomic` chỉ kiểm riêng `claim`. Ai đó bọc `claim` và lời gọi X chung một giao dịch thì không test nào bắt | Thêm test: một kết nối thứ hai đọc trạng thái ngay lúc mỗi lời gọi X diễn ra | `test_api_claim_is_committed_before_any_x_call` |

Một test cũ phải đổi: `test_needs_attention_contents` gọi `mark_handled` lên tin `unknown` và tin kênh tay đang chờ, rồi
kiểm hai tin đó vẫn nằm trong danh sách. Giờ lời gọi đó ném `ValueError`; test kiểm việc bị từ chối. Kết luận của test
giữ nguyên: hai tin đó vẫn hiện.

`sends_in_last_24h` giờ đếm bằng một câu SQL (so chuỗi thời gian). `claim` dùng chung câu đó, nên trần chỉ có một định
nghĩa. So chuỗi đúng vì mọi mốc thời gian đều do `db.now()` tạo, cùng một dạng.

## Quyết định của người dùng

- **`failed` có được ẩn khỏi Needs attention bằng `mark_handled` không** (`gd-5.md` mục 5). Người dùng trả lời «Giữ:
  cho ẩn», ngày 13/11/2026. Mã hiện tại đã làm đúng như vậy, không phải sửa. Subagent cũng nghiêng về cho ẩn: `failed`
  là «chắc chắn chưa gửi», giống `blocked`; `claim` xoá `handled_at` nên lần thử mới vẫn hiện lại; `review.py` vẫn cho
  sửa và duyệt lại tin `failed`. Điều kiện kèm theo: GĐ6 phải hiện tin `failed` ở tab Review.

## Ghi nhận — chưa sửa

- `_finish` / `_release` bỏ qua `rowcount`. Nếu `recover_stuck` chạy đúng lúc một lần gửi đang chờ X, `send_api` trả
  `"sent"` trong khi CSDL ghi `unknown`. Gần như không xảy ra: mỗi lời gọi X hết giờ sau 30 giây, còn mốc là 300 giây.
- 429 ở bước gửi trả `"approved"` và mất `reset_at`. 429 ở bước tra người dùng / kiểm hội thoại thì ném `RateLimited`.
  Giao diện phải xử lý cả hai cách.
- Đánh dấu do-not-contact khi tin kênh API đang `sending`: giữa lúc giữ chỗ và lúc gửi không kiểm lại (khe vài giây).
- `set_do_not_contact` với mã hồ sơ sai thì lặng lẽ không làm gì.
- `mark_replied` lần hai ghi đè ghi chú lần một.
- `test_api_ambiguous…` thay `x.send_dm` thay vì dùng `x.fail_next` như kế hoạch viết. Thay là đúng, vì `fail_next` sẽ
  trúng `users_by_usernames` trước. `gd-5.md` không nêu chỗ lệch này.
- `test_claim_is_atomic` nhận fixture `campaign_id` mà không dùng. `test_api_closed_dm_blocks` không kiểm câu lỗi và
  không kiểm `can_dm=0` đã được lưu.
- Nhãn `X_MODE=fake` trong `gd-5.md` chỉ có một câu sau các khối output, không gắn từng khối. Chấp nhận được.

## Đã kiểm, thấy đúng

- **Luật 1:** `claim` dùng `WHERE id=? AND status='approved'`; `draft`, `rejected` bị chặn ở cả hai kênh.
- **Luật 2:** một câu `UPDATE`, kiểm `rowcount == 1`, commit bằng `with conn:`. Kết nối thứ hai thấy `sending` trước
  khi trả đường dẫn và trước mọi lời gọi X. Chạy 300 vòng, hai luồng thật cùng gọi `open_manual` một tin: mỗi vòng đúng
  một bên thắng, 0 lỗi.
- **Luật 3:** tin kênh tay đang `sending` chỉ rời đi qua `confirm_manual`, tin `unknown` chỉ qua `resolve_unknown`;
  `recover_stuck` chỉ chạm kênh API; `review.approve` / `reject` không nhận `sending` hay `unknown`.
- `check_can_send`: thứ tự và cả năm câu lý do khớp nguyên văn kế hoạch.
- Kênh API: kiểm danh sách cho phép trước khi giữ chỗ ở mọi `SEND_MODE`; lưu `x_user_id`, `can_dm`; không tìm thấy hoặc
  DM đóng → `blocked`; 403 → `blocked`, 400/401 → `failed`, 429 → `approved`, timeout/5xx → `unknown`; thứ tự các nhánh
  `except` đúng theo cây lớp lỗi; tin `unknown` không bao giờ bị gửi lại.
- Danh sách cho phép không phân biệt hoa thường. CSDL có `x_username UNIQUE COLLATE NOCASE` và `messages.prospect_id
  UNIQUE`: mỗi người một tin.
- «Not sent» trả tin về `approved` và không tính vào trần. Trần đếm `sending`, `sent`, `unknown` trong 24 giờ.
- Đủ 21 test đúng tên kế hoạch, cộng 1 test chống lùi; không test nào tự đúng hiển nhiên. 124 thay vì 108: 102 test cũ +
  22 test mới, báo cáo giải thích đúng.
- `gd-5.md` có đúng 5 mục; output dán khớp lần chạy lại (cả commit đỏ `e24537b`: `Interrupted: 1 error during
  collection`; thêm `--continue-on-collection-errors` → `102 passed, 1 error`). Không có câu «người dùng chỉ đạo». Phần
  chưa chạy X thật nằm ở «Chưa kiểm được».
- Chú thích `SEND_MODE` trong `.env.example` trùng từng chữ với mục 3. Diff chỉ đụng tệp kế hoạch liệt kê, cộng tài liệu.
