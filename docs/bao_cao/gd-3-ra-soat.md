# Rà soát Giai đoạn 3 — Tìm người qua GitHub

Ngày 2026-11-13 · Người rà: một subagent mới của Claude (không viết mã GĐ3), đọc `git diff gd-2-ok..gd-3` và mục
GĐ3 trong `docs/quy_trinh_trien_khai.md`. Claude phiên chính đối chiếu từng mục với mã rồi sửa.

## Kết luận

**Đạt sau khi sửa. Đã gắn `gd-3-ok`.**

- Tại `gd-3`: `pytest -q` trong `.venv` → `67 passed`, cây git sạch. Mã nền làm đúng spec ở hầu hết các điểm
  (xem «Đã kiểm, thấy đúng»).
- Có 5 mục phải sửa. Mục nặng nhất: một test cũ gọi mạng thật (vi phạm «test không bao giờ ra mạng»).
- Sau khi sửa: `pytest -q` → `72 passed`. Chạy lại với một plugin chặn mọi kết nối HTTP thật
  (`httpx.HTTPTransport.handle_request` ném lỗi) → vẫn `72 passed`, tức không test nào ra mạng.

## Phải sửa — đã sửa

| # | Lỗi | Tình huống hỏng | Sửa | Commit |
|---|---|---|---|---|
| 1 | `doctor` gọi GitHub thật khi `X_MODE=real` mà token rỗng | `test_doctor_env_check_fails_on_empty_keys` gửi `GET https://api.github.com/rate_limit` | Chỉ kiểm token khi token khác rỗng (rỗng thì bước [1] đã FAIL); test truyền `gh` giả ném lỗi nếu bị gọi | `b283bb8` |
| 2 | `test_doctor_fails_on_bad_github_token` không kiểm gì | Biến môi trường rỗng làm bước [1] luôn FAIL; thay nhánh `except GitHubAuthError` bằng `print("PASS")` test vẫn qua | Đặt biến môi trường `GITHUB_TOKEN`, kiểm chữ `FAIL: GitHub rejected GITHUB_TOKEN` và lời khuyên | `b283bb8` |
| 3 | Chỉ có `retry-after` thì `reset_at = 0` hoặc giờ reset của cửa sổ chính | Giới hạn phụ của API tìm kiếm: báo chờ ~1 giờ thay vì 60 giây | `reset_at = now + retry-after` khi có; test mới `test_secondary_limit_uses_retry_after` | `f8d7611` |
| 4 | Thông điệp lỗi tiếng Việt trong mã | Trái luật «mã bằng tiếng Anh»; `python -m outreach.doctor > log.txt` có thể vỡ vì bảng mã cp1252 | Đổi sang tiếng Anh; test kiểm thông điệp chỉ gồm ASCII | `f8d7611` |
| 5 | `FakeGitHub` không có repo, không có `following` | Chế độ fake lưu 0 repo; `discover_by_seeds` luôn ra 0; GĐ4 không có bằng chứng repo để demo | Thêm repo (2 người hợp có mô tả, 1 người hợp `description=None`, 1 người không liên quan) và `following` chung cho 2 hạt giống | `f8d7611` |

## Nên sửa — đã sửa luôn (rẻ, chạm đúng lỗi đã gặp)

- **6.** Lỗi mạng chỉ in `lỗi mạng: ` (rỗng với `ReadTimeout`). Giờ in loại lỗi và đường dẫn:
  `network error ReadTimeout on GET /users/bob: …`. Lần chạy thật 3.3 đầu tiên không biết lỗi ở đâu vì thiếu đúng thông tin này.
- **7.** Mỗi lời gọi mở một `httpx.Client` mới (bắt tay TCP + TLS lại). Giờ mỗi `GitHubClient` giữ một client.
  Chưa đo lại thời gian chạy thật.
- **8.** Trùng `repos.source_id` (login đổi tên, hoặc hai lượt chạy cùng lúc) làm `IntegrityError` dừng cả lượt.
  Giờ đếm là `existing` và chạy tiếp; test `test_repo_already_saved_for_someone_else_counts_existing`.
- **9.** Thiếu test cho «gặp hết lượt gọi giữa chừng thì người đã tìm được vẫn được lưu». Đã thêm
  `test_rate_limit_mid_run_keeps_saved_people` (mã vốn đúng; test chống lùi).
- **10.** `gd-3.md` mục 2 chưa dán nguyên văn output. Đã dán output sau sửa vào cuối `gd-3.md`.

## Ghi nhận — chưa sửa

- `gd-3.md` câu «kết quả thật, không phải lỗi đếm» chưa có bằng chứng; `no_x_handle` gộp cả login 404. Đã sửa câu
  thành «số đo được, chưa lấy mẫu kiểm». Câu lỗi thời «chưa gắn tag gd-3» đã sửa.
- Dò tên X từ `social_accounts`: so host chính xác (đúng), nhưng bỏ sót `mobile.twitter.com`, URL không có scheme;
  `twitter.com/intent/…` cho ra tên `intent`. Hiếm.
- `import_logins` không bỏ `@`, khoảng trắng hay URL khỏi login; login 404 bị đếm là `no_x_handle`. Cần xử lý ở
  giao diện GĐ6 (ô nhập tay ở bước 7.1).
- Chạy thật với token rỗng gửi `Bearer ` rỗng; `doctor` bắt được, `discover` thì không.
- `minh_ml`, `linh_front` của `FakeGitHub` không có trong `FakeXClient` → kênh API ở chế độ fake sẽ báo «not found»
  cho hai người này (GĐ5).
- Khi có lỗi giữa chừng, bộ đếm bị mất (spec cho phép).
- Truy vấn không có `type:user`; tổ chức có thể lọt vào. Chưa kiểm.
- `.env.example` thiếu đoạn «(manual channel only; the API channel is always limited to SEND_ALLOWLIST)» như spec §3.
  Không thuộc GĐ3.

## Đã kiểm, thấy đúng

- Ánh xạ lỗi 401 / 403·429 / 500 / lỗi mạng; không tự thử lại; có timeout 30 giây.
- Header `Accept`, `X-GitHub-Api-Version`, `Authorization: Bearer`; token không nằm trong URL hay thông điệp lỗi.
- `search_users` phân trang `per_page=100`, trần `min(limit, 1000)`; `following` phân trang, trần 500.
- `user()`: 404 → `None`; chuẩn hoá tên X; dự phòng qua `social_accounts`. `repos()`: `type=owner`, `sort=pushed`,
  bỏ fork, tối đa 5.
- Hồ sơ đã có (theo `id` hoặc `x_username`, không phân biệt hoa thường) → `existing`, không ghi đè. Hồ sơ và repo
  trong một giao dịch; rollback đúng. Login trùng giữa các truy vấn chỉ gọi `user()` một lần.
- `seed_scores` đúng công thức, lọc, thứ tự; 1 hạt giống → `min_seeds=1`; `import_logins` ghi `source='import'`.
- `test_same_x_handle_from_two_github_accounts_is_one_prospect` và `test_rate_limited_raises_with_reset` hỏng khi
  bỏ đoạn mã tương ứng (đã thử trên bản chép).
- Ba commit GĐ3 chỉ đụng đúng các tệp spec liệt kê cộng báo cáo.
