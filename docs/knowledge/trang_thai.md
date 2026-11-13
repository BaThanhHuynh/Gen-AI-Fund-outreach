# Trạng thái dự án — bài tập GenAI Fund

Cập nhật: 2026-11-13 (bàn giao: GĐ4 đạt `gd-4-ok`; GĐ5 xong `gd-5`, chưa rà soát độc lập).

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
| 3 — Tìm người qua GitHub | **đạt** (72 test) | gd-3, gd-3-ok |
| 4 — Chấm điểm, soạn tin | **đạt** (rà soát subagent: 2 phải sửa + 4 nên sửa đã sửa; 102 test; 4.3 chạy lại sau sửa) | gd-4, gd-4-ok |
| 5 — Gửi và theo dõi | **mã xong** (124 test, chỉ kiểm bằng `FakeXClient`). **Còn**: rà soát subagent độc lập → `gd-5-ok` | gd-5 |
| 6, 7 | chưa bắt đầu | — |

## Việc tiếp theo (phiên sau)
1. Rà soát độc lập GĐ5: subagent mới đọc `git diff gd-4-ok..gd-5` + mục GĐ5 quy trình + mục 5 «Trọng tâm rà soát»;
   sửa; gắn `gd-5-ok`; ghi `docs/bao_cao/gd-5-ra-soat.md`.
2. Làm GĐ6 (giao diện) theo quy trình.

## Câu hỏi còn mở
- `gd-5.md` mục 5: `failed` có được ẩn bằng «handled» không.
- `gd-4.md` mục 5: cắt câu trích ở 120 ký tự, ngưỡng `MIN_SCORE=40`, mặc định `LLM_PROVIDER` (`config.py` /
  `.env.example` vẫn là `ollama`), ưu tiên câu bio có từ khoá.
- Tỉ lệ `no_x_handle` cao (254/264).
