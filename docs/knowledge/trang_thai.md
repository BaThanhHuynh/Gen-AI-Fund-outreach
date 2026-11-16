# Trạng thái dự án — bài tập GenAI Fund

Cập nhật: 2026-11-16 (người dùng thêm chế độ kép GitHub / X Native; Claude rà và sửa 3 lỗi mã + tài liệu; 149 test;
chưa commit).

- Đề bài: `docs/assignment.md` · Quy trình: `docs/quy_trinh_trien_khai.md` · Báo cáo: `docs/bao_cao/gd-N.md`
- Vai trò: **từ GĐ3 Claude tự làm hết GĐ3 → GĐ7** (người dùng quyết ngày 13/11/2026). Việc chỉ người làm được
  (bấm gửi tin thật ở 7.1, quay video, gửi thư nộp bài) giao lại người dùng.
- Nhật ký: `docs/knowledge/nhat_ky/` (chỉ mục `CHI_MUC.md`)
- Hạn nộp: Thứ Ba 17/11/2026, 12:00 (GMT+7); quy trình đặt mốc nộp trước 11:00.

## Tiến độ

| Giai đoạn | Tình trạng | Tag |
|---|---|---|
| 0 | đạt: token GitHub OK · tài khoản B trong allowlist · `.env` đã `LLM_PROVIDER=template` | — |
| 1, 2, 2b | đạt | gd-1-ok, gd-2-ok |
| 3 — Tìm người qua GitHub | **đạt** (72 test) | gd-3, gd-3-ok |
| 4 — Chấm điểm, soạn tin | **đạt** (102 test) | gd-4, gd-4-ok |
| 5 — Gửi và theo dõi | **đạt** (131 test) | gd-5, gd-5-ok |
| 6 — Giao diện | **đạt** (rà soát subagent: 3 phải sửa + 5 nên sửa đã sửa; 140 test, cả khi chặn mạng) | gd-6, gd-6-ok |
| 7 — Chạy thật, tài liệu | **đạt** phần của Claude (rà soát subagent: 5 phải sửa + 6 nên sửa đã sửa; 140 test, cả khi chặn mạng; `gd-7.md`, `gd-7-ra-soat.md`) | gd-7, gd-7-ok |

## Việc tiếp theo
1. **Người dùng:** quay video 3–5 phút theo `docs/demo_script.md` (làm phần «Start clean» trước: đổi tên
   `data/outreach.db`, xoá hội thoại A–B của lần chạy thử); gửi thư nộp bài trước 11:00 Thứ Ba 17/11/2026.
2. Tuỳ chọn: một lần rà soát tổng (Claude) trước khi nộp, theo lịch Thứ Hai 16/11.

## Đã chốt
- 13/11/2026: `failed` được ẩn khỏi Needs attention bằng «Mark handled» (người dùng: «Giữ: cho ẩn»).
- 13/11/2026 (người dùng): mặc định `LLM_PROVIDER=template`; giữ `MIN_SCORE=40` và câu trích tối đa 120 ký tự.
- 14/11/2026 (người dùng: «Giữ, nói rõ trong video»): không vá 3 chỗ hụt so với đề bài trước hạn nộp: tìm người và seed
  qua GitHub chứ không qua X; người lạ thì người bấm gửi, kênh API chỉ gửi cho allowlist; trả lời đánh dấu tay. Cảnh 8
  của `docs/demo_script.md` nói rõ cả ba.
- 16/11/2026: người dùng thêm X Native Mode (commit `7efe7a9`, `0e201cf`). Claude sửa: Sync lỗi `NameError`;
  `user_posts` xin dưới 5 bị X trả 400; ô tìm X nối từ khoá bằng OR. README lấy lại các mục «Try it without any
  keys», «Contacting real people», «Costs and paid features», «Limits and blocked actions»; cảnh 8 và writeup nói
  X Native chỉ thử bằng dữ liệu mẫu và mock. Giữ mặc định `X_MODE=real` (lựa chọn của người dùng). Để lại, không
  bắt buộc: Sync có thể đếm tin mình gửi là trả lời khi `me()` lỗi; không so giờ với `sent_at`; bảng Find lẫn
  người của chế độ kia; X Native bỏ qua `SEND_CHANNEL`; từ khoá rỗng cho truy vấn X rỗng.

## Câu hỏi còn mở
- `gd-6-ra-soat.md`: bảng hồ sơ ở tab Find vẫn có liên kết X (Claude tự quyết theo kế hoạch). Người dùng muốn bỏ thì
  sửa một dòng ở `app.py`.
- Tên X của một người thật (dùng thử chặn ở 7.1) còn trong lịch sử git (`21d2362`); bản hiện tại đã ẩn. Repo chưa có
  remote. Viết lại lịch sử là việc người dùng quyết.
- `data/outreach.db` còn 12 bản nháp cho người thật từ 7.1. Giữ, từ chối hay xoá CSDL là việc người dùng quyết.
