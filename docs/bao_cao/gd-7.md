# Giai đoạn 7 — Chạy thật, tài liệu, nộp bài

Ngày 2026-11-13/14 · Người làm: Claude (phiên chính). Ở 7.1, người dùng tự bấm gửi trong X từ tài khoản A và trả lời
bằng tài khoản B. Mọi output ở 7.1 chạy ở **`X_MODE=real`** (GitHub thật), `SEND_CHANNEL=manual`,
`SEND_MODE=allowlist`, `SEND_ALLOWLIST=Nolanhuynh` (tài khoản B), `LLM_PROVIDER=template`. CSDL: `data/outreach.db`.

## 1. Đã làm

- **7.1 Chạy thật, cả 7 dòng có bằng chứng.** Bấm trên giao diện thật (Streamlit ở `localhost:8502`, trình duyệt
  trong app Claude), trừ hai lần gọi thẳng `open_manual` để kiểm lớp dưới.

  | # | Việc | Kết quả | Bằng chứng |
  |---|---|---|---|
  | 1 | Tìm theo cụm từ `robotics, machine learning` | 30 hồ sơ người thật. Không nhắn ai | Thông báo trên app (mục 2) |
  | 2 | `Add` tài khoản GitHub `BaThanhHuynh` (ghi X là `Nolanhuynh`) → `Score` → `Draft` | 45 điểm; bản nháp trích nguyên văn bio, `evidence_ok = 1` | Dòng CSDL (mục 2) |
  | 3 | `Approve` → `Start` → người dùng gửi từ A → B nhận → `I sent it` | Tin `sent`, kênh `manual` | `gd-7-send-b.jpg`, `gd-7-x-b.png`, dòng CSDL |
  | 4 | `Start` lần hai cho B | Bị chặn: `not approved`; tab Send không còn nút nào cho B | Output (mục 2) |
  | 5 | `Start` với người thật ngoài danh sách (`@IliaLarchenko`) | Không có nút `Start`, hiện `Can't send: not on SEND_ALLOWLIST (safety mode)`. Gọi thẳng `open_manual` → `SendBlocked`, tin vẫn `approved`, không giữ chỗ, không trả đường dẫn X. Sau đó tin bị từ chối | Output (mục 2) |
  | 6 | B trả lời «sure thing» → `Mark replied` → hiện ở Needs attention → `Mark handled` | Có `replied_at`, `reply_text`, `handled_at`; Needs attention trống lại | `gd-7-track-b.png`, dòng CSDL |
  | 7 | Tổng chi phí từ bảng `usage` | 0 dòng, 0 USD | Output (mục 2) |

- **7.2** `README.md` (tiếng Anh), đủ các ý trong quy trình. Có thêm bẫy đường dẫn dài trên Windows, tìm ra ở 7.3.
- **7.3** Đo thời gian cài đặt theo README trong thư mục trống: 115 giây.
- **7.4** `docs/writeup.md` (592 từ, kể cả tiêu đề).
- **7.5** `docs/demo_script.md`: 8 cảnh, 0:00–4:50.
- **7.6** Quét trước khi nộp: sạch.
- Mặc định `LLM_PROVIDER` trong `outreach/config.py` và `.env.example` đổi thành `template` (người dùng chọn ngày 13/11).
  Commit: `6338577`, `1eb2ab5`.

## 2. Kết quả kiểm

**7.1** (`X_MODE=real`). `python -m outreach.doctor`:
```
[1] Checking environment configuration...
  PASS: Core environment variables are configured (secrets kept hidden)
[2] Checking X connection...
  PASS: Manual send channel (no X API credentials required)
[GitHub] Checking GITHUB_TOKEN...
  PASS: GitHub token accepted (5000/5000 requests left)
```
Thông báo trên app sau `Search GitHub`, rồi sau `Add` (lần cuối), `Score`, `Draft next 14`:
```
30 new, 0 already known, 480 people had no X handle (510 GitHub accounts checked).
1 new, 0 already known, 0 people had no X handle (1 GitHub accounts checked).
Scored 31 people.
14 new drafts.
```
Hồ sơ và bản nháp của B:
```
fit_score 45 · [Bio mentions machine learning (bio), Repo Machine-Learning-From-Scratch is about machine learning
  (repo:BaThanhHuynh/Machine-Learning-From-Scratch), Pushed code to IT-Law-Chatbot in the last 90 days (repo:…)]
{'id': 7, 'status': 'draft', 'evidence_ok': 1, 'evidence': '[{"source_id": "bio", "quote": "Machine learning and AI chatbots"}]', …}
```
Bước 5 (người ngoài danh sách, tin số 1):
```
SendBlocked: not on SEND_ALLOWLIST (safety mode)
{'id': 1, 'status': 'approved', 'channel': None, 'claimed_at': None}
```
Sau `Start` cho B: `(7, 'sending', 'manual', '2026-11-13T19:01:37.439416+00:00')`; tin số 1: `(1, 'rejected')`.
Bước 3–4, sau `I sent it`:
```
{'id': 7, 'status': 'sent', 'channel': 'manual', 'sent_at': '2026-11-13T19:12:07.650906+00:00'}
check_can_send: not approved
second Start -> SendBlocked: not approved
status after: sent
```
Bước 6–7:
```
{'id': 7, 'status': 'sent', 'channel': 'manual', 'claimed_at': '2026-11-13T19:01:37.439416+00:00', 'sent_at': '2026-11-13T19:12:07.650906+00:00', 'replied_at': '2026-11-13T19:12:20.734476+00:00', 'reply_text': 'sure thing', 'handled_at': '2026-11-13T19:12:29.196696+00:00'}
usage rows: (0, 0)
messages by status: [('draft', 12), ('rejected', 1), ('sent', 1)]
prospects: 31
```
Ảnh: `gd-7-send-b.jpg` (sau `Start`: tin chờ gửi, nút chép, `Open @Nolanhuynh on X`, ba nút xác nhận, `1 / 20`).
`gd-7-x-b.png`: ảnh người dùng chụp trong X từ A. Tin gửi lúc 2:07 AM, B trả lời «sure thing» lúc 2:09 AM. X ghi «This
conversation is now end-to-end encrypted». `gd-7-track-b.png`: Sent 1, Replied 1, 100%, Needs attention có
@Nolanhuynh kèm «Reply: sure thing», `Spend today: $0.00`.

**7.3** Script làm đúng các bước README, chạy trong `data/t73` (thư mục trống mới tạo):
```
[0s] 1 clone
[1s] 2 venv
Python 3.14.7
[11s] 3 pip
pip exit=0
[105s] 4 env
X_MODE=fake                 # fake: samp
LLM_PROVIDER=template       # template:
[106s] 5 doctor
  PASS: Core environment variables are configured (secrets kept hidden)
  PASS: Manual send channel (no X API credentials required)
doctor exit=0
[111s] 6 app
[115s] app health: ok
[115s] done
```
Lần đo đầu, trong thư mục nháp (đường dẫn gốc 105 ký tự), `pip` hỏng:
```
ERROR: Could not install packages due to an OSError: [Errno 2] No such file or directory: 'C:\\Users\\dell\\AppData\\Local\\Temp\\claude\\…\\setup73\\genaifund-outreach\\.venv\\Lib\\site-packages\\anthropic\\types\\beta\\beta_managed_agents_self_hosted_resources_unsupported_deployment_paused_reason_error.py'
HINT: This error might have occurred since this system does not have Windows Long Path support enabled.
```
Tệp dài nhất tính từ `site-packages`: `streamlit` 142 ký tự, `anthropic` 139. Máy có `LongPathsEnabled = 0x0`.

**7.6**
```
git ls-files | grep -E '(^|/)\.env$|^data/|\.db$'   → (không có dòng nào)
git grep -nE "sk-ant-|ghp_|github_pat_"
docs/quy_trinh_trien_khai.md:848:  - `git grep -nE "sk-ant-|ghp_|github_pat_"` không ra dòng nào.
pytest -q → 140 passed in 19.03s
```
Dòng duy nhất khớp là chính dòng quy trình chứa mẫu tìm. Mẫu chặt hơn (`sk-ant-[A-Za-z0-9_-]{10,}|ghp_[A-Za-z0-9]{20,}|
github_pat_[A-Za-z0-9_]{20,}`): `HEAD: 0 files`, `all history: 0 hits`, `revs scanned: 59`.

## 3. Lệch so với kế hoạch

- **B dưới ngưỡng ở lần đầu.** Hồ sơ GitHub của B không có bio và vị trí → 25/40 điểm, không có bản nháp. Người dùng
  chọn tự thêm bio trên GitHub. `discover` không làm mới hồ sơ đã lưu («already known»), nên Claude xoá đúng dòng
  `prospects` + 5 dòng `repos` của B, hai lần, cả hai lần chưa có tin nào. Lần đầu GitHub chưa lưu thay đổi, API vẫn
  trả bio rỗng. Lần hai bio là «Machine learning and AI chatbots», vị trí vẫn trống → 45 điểm.
- **Soạn tin cho 14 người, không chỉ B.** Bản nháp được soạn theo thứ tự điểm, nên muốn có tin của B phải soạn cả 14 người
  đủ ngưỡng (`template`, trên máy, 0 USD). 12 bản nháp cho người thật vẫn nằm trong `data/outreach.db` ở `draft`.
  Danh sách cho phép chặn gửi.
- **Bước 5 duyệt một tin cho người thật để thử chặn**, rồi từ chối ngay. Giao diện không có nút `Start` cho dòng bị chặn,
  nên «thử Start» được làm bằng cách gọi thẳng `sender.open_manual`.
- **`I sent it` do Claude bấm**, sau khi người dùng báo đã gửi và gửi ảnh. Giữa lúc `Start` và `I sent it`, phiên Claude
  khởi động lại làm app tắt. Chạy lại thì tin vẫn ở «Waiting for you to send», đúng trọng tâm rà soát 1.
- **7.3 do máy làm theo README, không phải người.** Script bỏ qua thời gian đọc README. Ở chế độ `X_MODE=fake` không
  cần token GitHub. `pip` chạy với `--no-cache-dir` để tải như máy mới. Lần đầu hỏng vì đường dẫn quá dài (mục 2), nên
  đo lại ở `data/t73`, rồi thêm giới hạn này vào README (`1eb2ab5`). Không đo thời gian tải mô hình Ollama vì dùng
  `template`.
- **7.4 ghi đúng thực tế, không theo kế hoạch «Antigravity viết mã».** `git log`: các commit GĐ1–2b không có dòng
  `Co-Authored-By` của Claude, còn từ `2c72325` (GĐ3) trở đi đều có. Các báo cáo rà soát GĐ1–2 do Claude ghi.
- **Ảnh `gd-7-track-b.png` được cắt** để bỏ phần dưới có tên X của một người thật (ô «Do not contact»).
- **Cổng 8501 đang có một app Streamlit khác chạy** (có thể của người dùng), nên Claude dùng cổng 8502 và không tắt app kia.

## 4. Chưa kiểm được

- Chưa có người thật làm theo README từ đầu (7.3 do script đo). Chưa thử trên macOS / Linux.
- Kênh X API, Ollama, Anthropic chưa chạy thật lần nào; chỉ kiểm bằng mock.
- Cảnh 4 của kịch bản quay («bản bị từ chối duyệt vì bằng chứng sai») không tự xảy ra với `template`. Kịch bản đã ghi cách
  thay thế.
- Quay video và gửi thư nộp bài: việc của người dùng, chưa làm.

## 5. Câu hỏi cho người dùng

- 12 bản nháp cho người thật trong `data/outreach.db`: giữ, từ chối, hay xoá cả CSDL? Tệp này nằm ngoài git.
- Bản clone thử `data/t73` (439 MB, ngoài git): xoá được không?
- Bảng hồ sơ ở tab Find vẫn có liên kết X, theo kế hoạch (`gd-6-ra-soat.md`). Giữ hay bỏ?
