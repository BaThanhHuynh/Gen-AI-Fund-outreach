# Trạng thái dự án — bài tập GenAI Fund

Cập nhật: 2026-11-13 (bàn giao: GĐ3 đạt `gd-3-ok`; GĐ4 xong `gd-4`, chưa rà soát độc lập).

- Đề bài: `docs/assignment.md` · Quy trình: `docs/quy_trinh_trien_khai.md` · Báo cáo: `docs/bao_cao/gd-N.md`
- Vai trò: **từ GĐ3 Claude tự làm hết GĐ3 → GĐ7** (người dùng quyết ngày 13/11/2026). Việc chỉ người làm được
  (bấm gửi tin thật ở 7.1, quay video, gửi thư nộp bài) giao lại người dùng.
- Nhật ký: `docs/knowledge/nhat_ky/` (chỉ mục `CHI_MUC.md`)
- Hạn nộp: Thứ Ba 17/11/2026, 12:00 (GMT+7)

## Tiến độ

| Giai đoạn | Tình trạng | Tag |
|---|---|---|
| 0 | đạt: token GitHub OK · tài khoản B trong allowlist · `.env` đã `LLM_PROVIDER=template` | — |
| 1, 2, 2b | đạt | gd-1-ok, gd-2-ok |
| 3 — Tìm người qua GitHub | **đạt** (rà soát subagent: 5 phải sửa + 4 nên sửa đã sửa; 72 test) | gd-3, gd-3-ok |
| 4 — Chấm điểm, soạn tin | **mã + kiểm thật xong** (98 test; 4.3: 10 hồ sơ, 5 bản nháp `template`, 5/5 bằng chứng đúng). **Còn**: rà soát subagent độc lập → `gd-4-ok` | gd-4 |
| 5, 6, 7 | chưa bắt đầu | — |

## Việc tiếp theo (phiên sau)
1. Rà soát độc lập GĐ4: subagent mới đọc `git diff gd-3-ok..gd-4` + mục GĐ4 quy trình; sửa; gắn `gd-4-ok`; ghi `docs/bao_cao/gd-4-ra-soat.md`.
2. Làm GĐ5 theo quy trình.

## Câu hỏi còn mở
- Tỉ lệ `no_x_handle` cao (254/264). Có nới cụm từ tìm kiếm ở GĐ4 không?
- Đề xuất GĐ4: đổi mặc định soạn tin thành `template` trong `config.py` và `.env.example`.
- Ba câu hỏi mới ở `docs/bao_cao/gd-4.md` mục 5 (cắt câu trích, ngưỡng điểm, mặc định `LLM_PROVIDER`).
