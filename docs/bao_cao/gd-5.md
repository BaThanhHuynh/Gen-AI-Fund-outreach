# Báo cáo Giai đoạn 5 — Gửi và theo dõi

Người làm: Claude. Phiên chính viết yêu cầu chi tiết, một subagent (model sonnet) viết test và mã theo đúng mục GĐ5
của quy trình. Phiên chính đọc toàn bộ diff, sửa 3 điểm (mục 3), chạy lại test rồi commit.

## 1. Đã làm
- 5.1: `tests/test_sender.py` gồm 21 test đúng tên trong kế hoạch, cộng 1 test chống lùi (mục 3). Chạy thấy hỏng
  (thiếu `outreach.sender`). Commit `e24537b`.
- 5.2: `outreach/sender.py` có đủ các hàm kế hoạch liệt kê:
  - `SendBlocked`, `sends_in_last_24h`, `check_can_send`, `claim`;
  - kênh tay: `open_manual`, `confirm_manual`;
  - kênh API: `send_api`, `recover_stuck`, `resolve_unknown`;
  - theo dõi: `mark_replied`, `mark_handled`, `set_do_not_contact`, `needs_attention`.

  Chú thích `SEND_MODE` trong `.env.example` giờ khớp đúng mục 3 của kế hoạch. Commit `b20f3a0`.
- Mọi lần đổi trạng thái là một câu `UPDATE … WHERE id=? AND <trạng thái mong đợi>`, kiểm `rowcount`, commit ngay.
  Giữ chỗ (`approved → sending`) commit trước khi trả đường dẫn X hay gọi X API.
- Kênh API kiểm `SEND_ALLOWLIST` trước khi giữ chỗ, ở mọi `SEND_MODE`.
- Không viết lời gọi API mới. GĐ5 chỉ dùng `users_by_usernames`, `dm_events_with`, `send_dm` đã viết và kiểm ở GĐ2,
  nên không mở lại tài liệu X.

## 2. Kết quả kiểm

Test hỏng trước khi viết mã (5.1), chạy trên bản xuất của commit `e24537b`.

`pytest -q`:
```
ERROR tests/test_sender.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 1.38s
```

`pytest -q --continue-on-collection-errors`:
```
ERROR tests/test_sender.py
102 passed, 1 error in 2.55s
```

Sau 5.2, `pytest -q`, rồi `pytest -q -p nonet` (plugin chặn `httpx.HTTPTransport.handle_request` và
`socket.socket.connect`):
```
124 passed in 2.11s
```
```
[nonet] blocked network attempts: 0 []
124 passed in 1.92s
```

Test chống lùi `test_new_attempt_after_handled_failure_shows_again`: tạm bỏ phần xoá `handled_at` trong `claim` thì
test hỏng; khôi phục thì qua.
```
1 failed, 21 deselected in 0.51s
22 passed in 0.37s
```

Các test của mục «Trọng tâm rà soát» đều qua:
- `test_open_twice_second_is_blocked`, `test_claim_is_atomic`, `test_recover_stuck_only_touches_api_channel`;
- `test_api_ambiguous_becomes_unknown_and_is_never_resent`;
- `test_confirm_existing_conversation_blocks`, `test_api_prior_conversation_blocks`.

Mọi test chạy với `FakeXClient` (`X_MODE=fake` theo `tests/conftest.py`).

## 3. Lệch so với kế hoạch
- **Số test: 124, kế hoạch ghi 108.** Kế hoạch tính từ 87 test sau GĐ4. Thực tế sau GĐ4 và rà soát có 102. GĐ5 thêm
  21 test của kế hoạch và 1 test chống lùi.
- **Ánh xạ lỗi của `send_dm`** theo các lớp lỗi có sẵn trong `xclient.py`:
  - `Forbidden` (403) → `blocked`;
  - `RateLimited` (429) → `approved`, bỏ giữ chỗ;
  - `Ambiguous` (timeout, 5xx) → `unknown`;
  - `AuthError` (401) và mọi `XError` khác (400, 4xx khác) → `failed`.

  Lỗi ngoài các lớp này để tin ở `sending`; `recover_stuck` chuyển nó thành `unknown` sau 5 phút. Không bao giờ tự gửi lại.
- **`users_by_usernames` lỗi cũng trả tin về `approved` rồi ném lỗi.** Kế hoạch chỉ nói vậy cho `dm_events_with`.
  Lúc đó chưa gửi gì, nên thử lại là an toàn.
- **`needs_attention`:**
  - kênh tay đang `sending` và `unknown` luôn hiện; chỉ rời đi khi người chọn (`confirm_manual`, `resolve_unknown`);
    `mark_handled` không ẩn chúng;
  - `failed`, `blocked`, và tin có `replied_at` hiện cho tới khi `mark_handled`.

  Kế hoạch ghi `failed` không kèm điều kiện «chưa handled». Chọn cho ẩn được, vì nếu không thì một tin `failed` mà
  người không muốn gửi lại sẽ nằm đó mãi.
- **Phiên chính sửa 3 điểm khi rà diff** (trước commit `b20f3a0`):
  - `claim` xoá `handled_at`. Nếu không, tin `failed` đã handled, được duyệt lại rồi hỏng lần nữa sẽ bị ẩn. Có test
    chống lùi.
  - `send_api` đọc lại tin sau khi giữ chỗ, để gửi đúng văn bản đã giữ.
  - Xoá hằng `COUNTED` không dùng tới.
- **24 giờ và 300 giây được so bằng `datetime.fromisoformat`**, không so chuỗi. Cách này không phụ thuộc định dạng
  chuỗi (`db.now()` bỏ phần micro giây khi bằng 0).
- **Thêm vài lỗi rõ ràng:**
  - `confirm_manual` với kết quả lạ → `ValueError`;
  - `mark_handled` với mã tin không có → `ValueError`;
  - `open_manual` / `send_api` thua cuộc giữ chỗ (hai tab) → `SendBlocked("not approved")`.
- `mark_replied` chỉ chạy với tin `sent`; trạng thái khác → `ValueError`.

## 4. Chưa kiểm được
- **Chưa gọi X thật.** Kênh tay cần người bấm gửi (bước 7.1). Kênh API tốn tiền, trái ràng buộc 0 USD. Mọi đường gửi
  mới chỉ kiểm bằng `FakeXClient` và lỗi giả.
- **`test_claim_is_atomic` gọi hai kết nối lần lượt, không chạy song song thật.** Nó chứng minh câu `UPDATE` có điều
  kiện chỉ thắng một lần. Chưa thử hai luồng cùng lúc.
- **Mã HTTP nào thành lớp lỗi nào** (`XClient`) đã kiểm ở GĐ2, lần này không kiểm lại.
- **Chưa kiểm ở chế độ fake** với hai người `minh_ml`, `linh_front` của `FakeGitHub`. Họ không có trong
  `FakeXClient`, nên kênh API sẽ báo `blocked` «X account not found» (ghi nhận từ rà soát GĐ3).

## 5. Câu hỏi cho người dùng
- **`failed` có được ẩn bằng «handled» không** (mục 3), hay phải hiện tới khi duyệt lại / từ chối?
- **Còn mở từ GĐ4** (`gd-4.md` mục 5):
  - cách cắt câu trích;
  - ngưỡng `MIN_SCORE`;
  - mặc định `LLM_PROVIDER`;
  - ưu tiên câu bio có từ khoá.
