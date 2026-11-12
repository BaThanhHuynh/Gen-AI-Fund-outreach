# Trạng thái dự án — bài tập GenAI Fund

Cập nhật: 2026-11-13 (bàn giao cuối phiên: GĐ3 làm xong, chưa rà soát độc lập).

- Đề bài: `docs/assignment.md` · Quy trình: `docs/quy_trinh_trien_khai.md` · Báo cáo: `docs/bao_cao/gd-N.md`
- Vai trò: **từ GĐ3 Claude tự làm hết GĐ3 → GĐ7** (người dùng quyết ngày 13/11/2026). Việc chỉ người làm được
  (bấm gửi tin thật ở 7.1, quay video, gửi thư nộp bài) giao lại người dùng.
- Nhật ký: `docs/knowledge/nhat_ky/` (chỉ mục `CHI_MUC.md`)
- Hạn nộp: Thứ Ba 17/11/2026, 12:00 (GMT+7)

## Tiến độ

| Giai đoạn | Tình trạng | Tag |
|---|---|---|
| 0 | một phần: token GitHub OK · tài khoản B trong allowlist · **còn**: `.env` đang `LLM_PROVIDER=ollama` (phải là `template`, người dùng tự đổi) | — |
| 1, 2, 2b | đạt | gd-1-ok, gd-2-ok |
| 3 — Tìm người qua GitHub | **mã và kiểm thật xong** (67 test; chạy thật: 10 hồ sơ mới, 264 người kiểm, 254 không có tên X). **Còn**: rà soát subagent độc lập, rồi gắn `gd-3-ok` | gd-3 |
| 4 — Chấm điểm, soạn tin | chưa bắt đầu | — |
| 5, 6, 7 | chưa bắt đầu | — |

## Việc tiếp theo (phiên sau)
1. Rà soát độc lập GĐ3: subagent mới đọc `git diff gd-2-ok..gd-3` và mục GĐ3 trong quy trình; sửa lỗi phải sửa; gắn `gd-3-ok` và ghi `docs/bao_cao/gd-3-ra-soat.md`.
2. Làm GĐ4 theo quy trình (test trước, `pytest -q`, báo cáo, tag `gd-4`, rà soát).
3. Lưu ý đã biết: lần chạy thật đầu của 3.3 lỗi mạng (`GitHubError` mã 0) sau 303 giây; lần hai trơn. Nguyên nhân chưa rõ.

## Câu hỏi còn mở
- Tỉ lệ `no_x_handle` cao (254/264). Có nới cụm từ tìm kiếm ở GĐ4 không?
- Đề xuất GĐ4: đổi mặc định soạn tin thành `template` trong `config.py` và `.env.example`.
