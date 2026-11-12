# GĐ0 — Việc của người: kết quả kiểm trên X

Ngày kiểm: 2026-11-12. Người kiểm: Claude, qua tiện ích Claude in Chrome, trong phiên đã đăng nhập tài khoản A.
Chỉ xem trang, không bấm, không gõ, không gửi.

## 1. Luật tự động hoá của X

Nguồn: `https://help.x.com/en/rules-and-policies/x-automation` (trang ghi «Updated April 2026»; công cụ tải tự động
bị chặn 403, phải đọc qua trình duyệt). Tóm tắt phần liên quan đến dự án:

| Luật (diễn đạt lại) | Mục trên trang | Hệ quả cho dự án |
|---|---|---|
| «You may not send unsolicited Direct Messages in a bulk or automated manner.» Chỉ được gửi DM tự động khi người nhận đã chủ động xin liên lạc trước, và phải cho họ cách từ chối. | II.C | **Kênh `api` chỉ được gửi cho người trong `SEND_ALLOWLIST`** (tài khoản thử của chính mình). Không dùng kênh `api` cho người được tìm ra. |
| Việc người dùng *có thể* nhận DM (mở DM cho mọi người, đang theo dõi mình) không có nghĩa là họ muốn nhận DM tự động. | II.C | `can_dm` chỉ để hiển thị, không phải giấy phép gửi. |
| Cấm tự động hoá không qua API, ví dụ viết script điều khiển trang web X; có thể bị khoá tài khoản vĩnh viễn. | I. Don't | Kênh `manual` chỉ **mở** trang hồ sơ; người gửi tự bấm, tự dán, tự gửi. Không tự điền, không tự bấm trên x.com. |
| Không gửi tin trùng lặp hoặc gần giống nhau hàng loạt (spam). | I.A | Tin `template` dễ giống nhau → cảnh báo Jaccard ≥ 0.8 phải giữ; mỗi tin phải có bằng chứng riêng của người đó. |
| Sau khi cuộc trao đổi kết thúc, không gửi tin nhắc lại khi chưa được phép. | II.C | Khớp luật «không nhắn hai lần»: không có tin nhắc tự động. |
| Trả lời tự động bằng AI cần X duyệt trước bằng văn bản. | II.B.3 | Dự án không tự trả lời; trả lời là việc của người. |

Kết luận: luồng gửi tay — người duyệt từng tin, tự gửi trong X, có trần mỗi ngày, không nhắn hai lần — nằm trong
luật. Kênh `api` gửi cho người lạ thì **không** nằm trong luật, dù có người duyệt.

## 2. Nút «Message» với người không theo dõi A

- Mở hồ sơ tài khoản B khi đăng nhập bằng A. B không theo dõi A (không có nhãn «Follows you»; nút hiện «Follow»).
- Nút **«Message»** có hiện trên hồ sơ B.
- **Chưa kiểm:** bấm «Message» có mở ô soạn tin không, và X có đòi cài mã khoá (passcode) cho XChat không.
  Việc này cần một cú bấm. Người dùng tự làm, hoặc cho phép Claude bấm.
- Ghi chú: hồ sơ B hiện «Joined July 2022», tức đây là tài khoản cũ được đặt tên mới, không phải tài khoản mới tạo.
  Trước bước 7.1 cần xác nhận A và B chưa từng nhắn cho nhau.
