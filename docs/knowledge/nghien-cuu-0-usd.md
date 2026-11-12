# Nghiên cứu: chạy trên dữ liệu thật, người thật, 0 USD

Ngày 2026-11-12 · Claude · Mọi sự thật dưới đây kiểm ngày 2026-11-12, trừ chỗ ghi khác.

## Kết luận ngắn

- **Gửi DM qua X API không thể miễn phí.** X không còn gói Free. DM tính tiền theo lượt.
- **Đường 0 USD hợp lệ:** tìm người trên GitHub (API miễn phí, hồ sơ có ô tên tài khoản X), soạn tin bằng mô
  hình chạy trên máy, rồi **người vận hành tự bấm gửi trong X**. Công cụ chỉ chép sẵn tin và mở hồ sơ. Không
  cào, không điều khiển trình duyệt, không tốn tiền.
- Cái giá phải trả: gửi và ghi nhận trả lời là thao tác tay (khoảng 3 cú bấm mỗi người). Chỉ tìm được những
  người có ghi tên tài khoản X trên GitHub (mẫu đo: 14/30, khoảng 47%).

## Sự thật đã kiểm

| Điều | Giá trị | Nguồn | Độ chắc |
|---|---|---|---|
| Gói miễn phí X API | Không có. Bảng giá chỉ có trả theo lượt dùng | `docs.x.com/x-api/getting-started/pricing` | Cao |
| Khuyến mãi X | 20 USD credit, chỉ sau khi lưu thẻ và **mua** credit lần đầu | 〃 | Vừa |
| Giá X | Đọc post 0,005 · đọc user 0,010 · đọc sự kiện DM 0,010 · gửi DM 0,015 USD | 〃 | Cao |
| Đường dẫn soạn DM | `x.com/messages/compose?recipient_id=<user id>&text=<mã hoá URL>`; `recipient_id` **bắt buộc**, không có tham số tên tài khoản | `docs.x.com/x-for-websites/direct-message-button` | Cao (tài liệu); chưa thử với XChat |
| XChat | Có API riêng `/2/chat/...`, cần thư viện mã hoá. `/2/dm_events` được báo là không đọc được hội thoại mã hoá | `docs.x.com/xchat/introduction`; diễn đàn bên thứ ba | Vừa / thấp |
| Luật tự động hoá X | «send them unsolicited messages» và «automated posts or Direct Messages that are spam» bị cấm | `help.x.com/en/rules-and-policies/x-automation` (trang chặn máy, chỉ đọc được qua đoạn trích) | Thấp, **người dùng tự đọc** |
| GitHub user | Có `twitter_username`, `location`, `bio`, `company`, `blog` | `docs.github.com/en/rest/users/users` | Cao |
| GitHub giới hạn | Miễn phí. Có token: 5.000 lời gọi/giờ, tìm kiếm 30/phút. Không token: 60/giờ, tìm kiếm 10/phút. Tối đa 1.000 kết quả mỗi truy vấn | `docs.github.com/en/search-github/searching-on-github/searching-users` | Cao |
| GitHub đo thật | `"machine learning" in:bio location:Vietnam` → 202 người · `robotics in:bio location:Singapore` → 289 · `topic:robotics stars:>20` → 3.241 repo · mẫu 30 người: 14 có tên X | Claude tự gọi API | Cao (số đếm, không lưu tên) |
| Anthropic API | Không có gói miễn phí | `claude.com/pricing` | Cao |
| Gemini miễn phí | Google dùng nội dung gửi lên, có người đọc. Điều khoản ghi «Do not submit … personal information to the Unpaid Services» → **không dùng** cho bio/tên người | `aistudio.google.com/docs/terms` | Cao |
| Ollama | Chạy trên máy, dữ liệu không rời máy. `qwen3:4b` tải 2,5 GB, `qwen3:8b` tải 5,2 GB | `ollama.com/library/qwen3` | Cao (kích thước); chất lượng chưa thử |
| Máy người dùng | RAM 7,9 GB · CPU i7-5500U · GPU 830M 2 GB · chưa cài Ollama | Claude đo | Cao. Chỉ hợp với mô hình cỡ 4B, chạy chậm |

## Học từ mã nguồn mở

**Tuitbot** — `github.com/aramirez087/tuitbot` · commit `d5087495387fea93af8022586beaad429662f5dc` · MIT. Bot
Rust soạn trả lời trên X và xếp hàng chờ người duyệt. Có chế độ cào tuỳ chọn: **không học phần đó**.

Lấy ý tưởng (tự viết lại, không chép mã):
- Duyệt bằng một câu cập nhật có điều kiện: `UPDATE … WHERE id=? AND status='pending'`. Không có dòng nào đổi thì
  báo «đã duyệt rồi». Bấm hai lần, lần sau thua (`storage/approval_queue/queries.rs:279-305`). Thiết kế của ta
  đã có cùng kiểu cho bước `approved → sending`.
- Mọi lệnh gửi đi qua **một** cổng duy nhất: kiểm luật → kiểm trùng → ghi nhật ký (`mutation_gateway/mod.rs:104-176`).
  Họ làm vậy sau khi các bước kiểm bị chép lặp ở nhiều nơi. Ta giữ một hàm `send_one`.
- Chặn tin gần giống nhau: độ trùng từ Jaccard ≥ 0,8 so với các tin gần đây thì cảnh báo. Tin dưới 5 từ thì bỏ
  qua (`safety/dedup.rs:24-66`). **Đáng thêm**, vì giảm rủi ro bị coi là spam và buộc từng tin phải thật sự riêng.

Chỗ họ hở mà ta không được lặp lại:
- Họ chống gửi trùng bằng một cửa sổ 5 phút (`IDEMPOTENCY_WINDOW_SECS = 300`). Ta dùng ràng buộc UNIQUE vĩnh viễn
  trên người nhận.
- `has_replied_to` kiểm trước rồi mới làm, nên hai tiến trình chạy cùng lúc đều gửi được. Ta dùng UNIQUE kèm
  cập nhật có điều kiện.
- Họ không có trạng thái `sending`. Máy tắt giữa lúc gửi thì không biết tin đã đi chưa. Ta có
  `sending → unknown` và chỉ người mới được chốt.

Không tìm được repo nào làm trọn «duyệt + không bao giờ gửi trùng + theo dõi trả lời» cho DM X, hay «tìm người
qua `twitter_username` của GitHub». Phần này tự viết; nó nhỏ.

**WTF (Who to Follow, Twitter, WWW 2013)** — `web.stanford.edu/~rezab/papers/wtf_overview.pdf`. Cách gốc:
1. Lập «vòng tin cậy» bằng PageRank cá nhân hoá.
2. Dựng đồ thị hai phía: các hub ↔ những người hub theo dõi.
3. Chạy SALSA. Điểm authority cho ra người nên theo dõi.

Thông số gốc **chưa kiểm** (PDF không trích được chữ).

Bản tối thiểu cho ta, áp lên **đồ thị theo dõi của GitHub** (miễn phí, khác X):
- Hạt giống = vòng tin cậy, tức 10–20 tài khoản người dùng chọn.
- Ứng viên = người được ít nhất 2 hạt giống theo dõi.
- `điểm(c) = Σ 1/số_người_s_theo_dõi`, cộng trên mọi hạt giống `s` có theo dõi `c`. Đây là một bước SALSA đã
  chuẩn hoá theo bậc, nên tài khoản theo dõi hàng nghìn người không lấn át.
- Sau đó lọc theo vị trí và bio, rồi để mô hình chấm độ hợp.

Chi phí: mỗi hạt giống tốn `ceil(số_người_theo_dõi/100)` lời gọi, nằm gọn trong 5.000/giờ.

## Rủi ro tuân thủ — ghi vào bài viết

- **GitHub AUP**: cấm dùng thông tin lấy qua API «for spamming purposes, including … sending unsolicited emails»;
  «you will only use that personal information for the purpose for which that User has authorized it». Người tự
  ghi tên X công khai trên hồ sơ thì có thể coi là mời liên hệ, nhưng đây là **vùng xám**.
- **X**: tin gửi tay qua ứng dụng không phải «automated», nhưng luật chống spam vẫn áp dụng.
- Giảm rủi ro: trần 20 tin/ngày, chỉ người thật sự liên quan, mỗi tin dựa trên bằng chứng riêng, chặn tin gần
  giống nhau, tôn trọng yêu cầu ngừng liên hệ (`do_not_contact`). Trong lúc phát triển chỉ gửi cho tài khoản
  của chính mình (đề bài yêu cầu).

## Hướng đi v2 (2026-11-12) — NGƯỜI DÙNG ĐÃ DUYỆT; chi tiết thi công ở `docs/quy_trinh_trien_khai.md` bản 2

Nguyên tắc:
- Bạn làm và thử trên người thật với 0 USD.
- Bên chấm dùng được ngay mà không cần khoá X.
- Ai có khoá X hoặc khoá Claude thì bật thêm. Không bắt buộc.

| Phần | Cách làm | Chi phí |
|---|---|---|
| Tìm người | GitHub: tìm cụm từ trong bio, lọc theo 6 nước Đông Nam Á (`in:bio location:`). Hạt giống là tài khoản GitHub, chấm theo «được k hạt giống cùng theo dõi» (WTF rút gọn). Chỉ giữ người có `twitter_username` | 0 (token GitHub miễn phí) |
| Vì sao hợp | Chấm bằng luật, không dùng mô hình: từ khoá trong bio, chủ đề và mô tả repo, số sao, hoạt động gần đây, vị trí. Mỗi lý do kèm `source_id` thật | 0, cho kết quả ngay, không bịa được |
| Soạn tin | Mặc định dùng Ollama trên máy. Có `ANTHROPIC_API_KEY` thì dùng Claude. Kiểm bằng chứng như cũ, thêm cảnh báo khi tin giống một tin trước đó từ 80% trở lên (Jaccard, học từ Tuitbot) | 0 / tuỳ chọn |
| Gửi | Mặc định gửi tay: công cụ chép tin và mở `x.com/<tên>`. Người tự bấm gửi, rồi bấm «I sent it», «Not sent» hoặc «Already in contact». Có khoá X thì dùng chế độ API (`send_dm` của GĐ2), ghi rõ «chưa thử với X thật» | 0 / khoảng 0,025 USD mỗi tin (tra mã số người nhận + gửi) |
| Không nhắn trùng | Mỗi người một dòng, mãi mãi: mã số GitHub và tên X viết thường đều UNIQUE. Bước `approved → sending` vẫn là một câu cập nhật có điều kiện như cũ | — |
| Trả lời, mục cần chú ý | Cả hai chế độ đều bấm tay «Mark replied». Mục cần chú ý: tin treo ở `sending`, tin `unknown`, tin đã có trả lời mà chưa xử lý | 0 |

Đổi so với kế hoạch hiện tại:
- GĐ1: đổi khoá hồ sơ trong schema.
- GĐ2: sửa mục 1–4. Mục 5–6 hạ xuống không chặn, vì đường đọc DM qua API ra khỏi phạm vi.
- Bước 2.4: thay bằng lần thử thật 0 USD với tài khoản B ở bước 7.1.
- GĐ3: viết `github.py` thay cho tìm trên X.
- GĐ5: bỏ `reconcile` và `sync_replies` tự động.

Khi trễ, cắt theo thứ tự: hạt giống → chế độ API → Claude. Không cắt: chống nhắn trùng, thử thật với B.

Việc người dùng làm trước (GĐ0 mới), chưa ai kiểm:
1. Tạo token GitHub loại fine-grained, chỉ đọc dữ liệu công khai.
2. Cài Ollama, chạy `ollama pull qwen3:4b`, rồi đo tốc độ soạn một tin.
3. Ghi tên X của tài khoản B vào một hồ sơ GitHub do bạn kiểm soát.
4. Thử mở `x.com/<tên>` → «Message» với một người chưa theo dõi mình.
5. Đọc trang luật tự động hoá của X.
