# Trạng thái dự án — bài tập GenAI Fund

Cập nhật: 2026-11-12 (Claude rà soát Giai đoạn 2b: đạt, gắn gd-2-ok; việc tiếp theo: GĐ3. Người dùng không cài Ollama).

- Đề bài: `docs/assignment.md`
- Quy trình và thiết kế: `docs/quy_trinh_trien_khai.md`
- Báo cáo từng giai đoạn: `docs/bao_cao/gd-N.md` · kết luận rà soát: `docs/bao_cao/gd-N-ra-soat.md`
- Vai trò: Antigravity viết mã và test; Claude rà soát sau mỗi giai đoạn.
- Nghiên cứu đường 0 USD (dữ liệu thật, người thật) và hướng đi đã duyệt: `docs/knowledge/nghien-cuu-0-usd.md`
- Nhật ký phiên: `docs/knowledge/nhat_ky/` (chỉ mục: `CHI_MUC.md`)

## Mốc thời gian

- Thư xác nhận tham gia: trước Thứ Sáu 13/11/2026, 12:00 (GMT+7) — **đã gửi** (người dùng báo ngày 12/11/2026)
- Nộp bài: trước Thứ Ba 17/11/2026, 12:00 (GMT+7)

## Tiến độ

| Giai đoạn | Tình trạng | Tag |
|---|---|---|
| 0 — Việc của người (token GitHub, tài khoản B, đọc luật X) | một phần (12/11): token GitHub chạy được (5.000 lượt/giờ) · tài khoản B đã tạo, nằm trong `SEND_ALLOWLIST` · hồ sơ GitHub của người dùng có tên X của B, đọc được qua API · `data/fake.db` đã không còn · **không cài Ollama** → dùng `template` · đã đọc luật X và thấy nút «Message» trên hồ sơ B (xem `docs/bao_cao/gd-0.md`). Còn: đổi `.env` sang `LLM_PROVIDER=template`; bấm «Message» xem có mở ô soạn tin / đòi passcode XChat không | — |
| 1 — Khung dự án và cơ sở dữ liệu | **đạt** sau rà soát vòng 3 — xem `docs/bao_cao/gd-1-ra-soat.md` | gd-1, gd-1-ok |
| 2 — Kết nối X (kênh API tuỳ chọn) | **đạt** sau 2b (bước 2.4 bỏ) — xem `docs/bao_cao/gd-2-ra-soat.md` | gd-2, gd-2-ok |
| 2b — Sửa sau rà soát, đổi khoá hồ sơ, cấu hình mới | **đạt** (rà soát vòng 2); 1 mục sửa kèm ở đầu GĐ3 | gd-2b, gd-2-ok |
| 3 — Tìm người qua GitHub | **việc tiếp theo** của Antigravity | — |
| 4 — Chấm điểm, soạn tin, kiểm bằng chứng | chưa bắt đầu | — |
| 5 — Gửi và theo dõi | chưa bắt đầu | — |
| 6 — Giao diện | chưa bắt đầu | — |
| 7 — Chạy thật, tài liệu, nộp bài | chưa bắt đầu | — |

## Câu hỏi còn mở

Hướng 0 USD đã được người dùng duyệt ngày 12/11/2026: tìm qua GitHub, chấm bằng luật, soạn bằng khuôn,
gửi tay trong X; kênh X API, Ollama và Claude là tuỳ chọn. Bốn câu hỏi mở về X API của bản 1 không còn chặn.

Đã chốt (12/11): người dùng không cài Ollama → mặc định soạn tin là `template`. Đề xuất cho GĐ4: đổi mặc định
trong `config.py` và `.env.example` thành `template`; giữ `ollama_call` nhưng ghi «chưa thử thật».

Đã đọc luật X (12/11, `docs/bao_cao/gd-0.md`): gửi tay từng tin là hợp lệ; **kênh `api` chỉ được gửi cho người
trong `SEND_ALLOWLIST`** — GĐ5 phải giữ chốt này. Còn chờ: bấm thử «Message» (ô soạn tin, passcode XChat).

Bước 7.1: nên dùng tài khoản B chưa từng nhắn với A, để luồng thử thật không phải bấm «Already in contact».
