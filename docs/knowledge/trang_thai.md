# Trạng thái dự án — bài tập GenAI Fund

Cập nhật: 2026-11-13 (bàn giao: GĐ5 đạt `gd-5-ok`; GĐ6 xong `gd-6`, chưa rà soát độc lập).

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
| 5 — Gửi và theo dõi | **đạt** (rà soát subagent: 0 phải sửa, 5 nên sửa đã sửa; 131 test; chỉ kiểm bằng `FakeXClient`) | gd-5, gd-5-ok |
| 6 — Giao diện | **mã xong** (133 test; luồng đi bằng `AppTest`, 4 ảnh tab; chưa người bấm, chưa chạy kênh API / `X_MODE=real` qua giao diện). **Còn**: rà soát subagent độc lập → `gd-6-ok` | gd-6 |
| 7 | chưa bắt đầu | — |

## Việc tiếp theo (phiên sau)
1. Rà soát độc lập GĐ6: subagent mới đọc `git diff gd-5-ok..gd-6` + mục GĐ6 quy trình + `gd-6.md`; chạy chặn mạng bằng
   plugin cho qua `socket.socketpair` nội bộ (`gd-6.md` mục 3); sửa; gắn `gd-6-ok`; ghi `gd-6-ra-soat.md`.
2. Làm GĐ7 theo quy trình. Việc chỉ người làm được (bấm gửi thật ở 7.1, quay video, gửi thư nộp bài) giao lại người dùng.

## Đã chốt
- 13/11/2026: `failed` được ẩn khỏi Needs attention bằng «Mark handled» (người dùng: «Giữ: cho ẩn»; `gd-5-ra-soat.md`).

## Câu hỏi còn mở
- `gd-4.md` mục 5: cắt câu trích ở 120 ký tự, ngưỡng `MIN_SCORE=40`, mặc định `LLM_PROVIDER` (`config.py` /
  `.env.example` vẫn là `ollama`), ưu tiên câu bio có từ khoá.
- Tỉ lệ `no_x_handle` cao (254/264).
