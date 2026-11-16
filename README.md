# GenAI Fund Outreach

Công cụ chạy trên máy của bạn, giúp: tìm những người đang làm AI và robot ở Đông Nam Á, soạn tin nhắn làm quen
riêng cho từng người (có trích nguyên văn bằng chứng), và nhắn tin trên X một cách an toàn, đúng luật của nền tảng.

Làm cho **bài tập về nhà vị trí Forward Deployed Engineer (FDE) của GenAI Fund**.

---

## Điểm chính

- **Hai chế độ làm việc:** chọn ở thanh bên trái (sidebar) của app Streamlit:
  1. **🛡️ Chế độ GitHub (0 USD, an toàn — nên dùng):** tìm người thật qua GitHub API (kho mã, lần commit, nơi ở
     tại Đông Nam Á). Bản nháp trích mô tả kho mã hoặc mã thật của họ. Bạn tự tay bấm Gửi trên X, nên tốn 0 USD và
     không có tin nhắn riêng (DM) nào gửi tự động.
  2. **⚡ Chế độ X gốc (đúng đề bài):** tìm người ngay trên X (theo từ khoá trong bài đăng và theo mạng lưới của các
     tài khoản X gốc), trích nguyên văn bài đăng gần đây của họ. App gửi DM qua X API đã kết nối, nhưng chỉ tới các
     tài khoản có trong `SEND_ALLOWLIST` (người khác thì bạn tự tay gửi), rồi đọc hộp thư DM để biết ai đã trả lời.
     Cần một X developer App trả phí (xem [Chi phí](#chi-phí-và-tính-năng-trả-phí)). **Mới chỉ thử bằng dữ liệu mẫu
     và X giả lập (mock), chưa chạy với X API thật.**
- **Cá nhân hoá có bằng chứng:** mỗi bản nháp trích một thông tin kiểm được từ tiểu sử (bio), kho mã hoặc bài đăng
  gần đây của người đó. Câu trích phải khớp từng chữ với nguồn; không khớp thì không duyệt được.
- **Không bao giờ nhắn một người hai lần:** cơ sở dữ liệu SQLite bảo đảm điều này bằng ràng buộc `UNIQUE(prospect_id)`
  (mỗi người chỉ có một tin) và bằng cách «giữ chỗ» tin nhắn trong một lệnh duy nhất
  (`UPDATE ... WHERE status='approved'`). Bấm hai lần liền hay mở nhiều tab trình duyệt cũng không gửi trùng.
- **Có sẵn giới hạn an toàn:** trần số tin mỗi ngày (mặc định 20/ngày), danh sách cho phép (`SEND_MODE=allowlist`),
  và công tắc «Không liên hệ» có tác dụng ngay.
- **Mặc định 0 USD (chế độ GitHub):** lưu dữ liệu bằng SQLite trên máy, dùng token GitHub miễn phí, soạn nháp bằng mẫu
  có sẵn (hoặc mô hình Ollama chạy trên máy). Có thể bật API trả phí (Claude, X API v2) nếu bạn cấu hình.
- **Kiểm thử kỹ:** 149 test tự động, tất cả chạy được khi không có mạng (mọi lệnh gọi mạng đều bị chặn).

---

## Cần có gì

- **Python:** 3.11 trở lên.
- **Token GitHub (miễn phí):** loại *Fine-grained personal access token*, quyền *Public repositories (read-only)* —
  chỉ đọc kho công khai.
- **Hệ điều hành:** Windows, macOS hoặc Linux.
- **Cách soạn nháp (chọn một trong `.env`):**
  - `template` (mặc định, **0 USD**): một mẫu tin cố định, điền câu trích nguyên văn vào. Không cần mô hình AI.
  - `ollama` (**0 USD**, chạy trên máy): dùng [Ollama](https://ollama.com) (`ollama pull qwen3:4b`).
  - `anthropic` (API trên mây, trả phí): dùng Claude qua Anthropic API.

---

## Bắt đầu nhanh (dưới 5 phút)

### 1. Tải mã về và vào thư mục
```bash
git clone <repository-url> genaifund-outreach
cd genaifund-outreach
```
*(Trên Windows, nên để thư mục ở đường dẫn ngắn như `C:\projects\genaifund-outreach` để tránh lỗi đường dẫn quá dài.)*

### 2. Tạo và bật môi trường ảo (virtual environment)
```bash
python -m venv .venv
```
- **Windows (PowerShell):** `.\.venv\Scripts\Activate.ps1`
- **macOS / Linux:** `source .venv/bin/activate`

### 3. Cài thư viện
```bash
pip install -r requirements.txt
```

### 4. Cấu hình
Tạo tệp `.env` từ tệp mẫu:
- **Windows:** `copy .env.example .env`
- **macOS / Linux:** `cp .env.example .env`

Mở `.env` và điền token GitHub miễn phí của bạn:
```env
X_MODE=real
GITHUB_TOKEN=github_pat_...
SEND_CHANNEL=manual
SEND_MODE=allowlist
SEND_ALLOWLIST=your_x_handle
DAILY_SEND_CAP=20
```

### 5. Chạy công cụ kiểm tra cấu hình
Kiểm tra trong 2 giây:
```bash
python -m outreach.doctor
```
Mọi dòng phải hiện `PASS`.

### 6. Mở app Streamlit
```bash
streamlit run app.py
```
Mở **`http://localhost:8501`** trong trình duyệt.

---

## Cách dùng từng bước

Chọn chế độ ở mục **CHẾ ĐỘ LÀM VIỆC** trên cùng của thanh bên trái.

### Chế độ 1: 🛡️ GitHub (0 USD, an toàn)
1. **Tìm người** (tab *Tìm người*):
   - Tạo hoặc chọn một chiến dịch (ví dụ từ khoá: `robotics, machine learning`).
   - Bấm **Tìm trên GitHub** (tìm từng từ khoá ở từng địa điểm Đông Nam Á), **Tìm người họ theo dõi** (đi từ vài
     tài khoản GitHub gốc sang mạng lưới của họ), hoặc **Thêm** (nhập sẵn tài khoản GitHub).
   - Bấm **Chấm điểm** để tính điểm phù hợp theo luật cố định, dựa trên bằng chứng thật (tiểu sử, kho mã, mức hoạt
     động, số sao).
2. **Duyệt tin** (tab *Duyệt tin*):
   - Chọn số bản nháp rồi bấm **Soạn N bản nháp tiếp theo**.
   - Xem từng bản nháp cạnh nguồn bằng chứng và đường dẫn tới nguồn.
   - Sửa chữ nếu cần, rồi bấm **Duyệt** hoặc **Từ chối**. Câu trích không khớp nguồn thì không duyệt được.
3. **Gửi tin** (tab *Gửi tin*):
   - Tin đã duyệt hiện ra, sẵn sàng để gửi.
   - Bấm **Bắt đầu gửi**: công cụ «giữ chỗ» tin này trong SQLite (để không ai gửi trùng), hiện nội dung tin kèm nút
     sao chép, và nút mở trang X của người nhận.
   - Dán và gửi tin trên X, rồi quay lại xác nhận: **Tôi đã gửi**, **Chưa gửi**, hoặc **Đã liên hệ từ trước**.
4. **Theo dõi** (tab *Theo dõi*):
   - Số liệu cập nhật ngay: Đã gửi, Đã trả lời, Tỉ lệ trả lời.
   - Có người trả lời: chọn người đó ở **Đánh dấu đã trả lời**, ghi chú họ nói gì; tin sẽ vào mục **Cần xử lý**.
   - Xong việc thì bấm **Đã xử lý xong**, hoặc bật **Không liên hệ người này**.

### Chế độ 2: ⚡ X gốc (đúng đề bài)
Trước khi bắt đầu (chạy thật): tạo một X developer App có quyền đọc/ghi DM và có credit API, đăng ký
`http://127.0.0.1:8765/callback` làm callback URL (địa chỉ X gọi lại sau khi đăng nhập), điền `X_CLIENT_ID` /
`X_CLIENT_SECRET` vào `.env`, rồi bấm **Kết nối tài khoản X** ở thanh bên trái. Mỗi lệnh gọi X dưới đây đều tốn
credit: xem [Chi phí](#chi-phí-và-tính-năng-trả-phí).

1. **Tìm người trên X:**
   - Ô tìm kiếm được điền sẵn từ từ khoá của chiến dịch, viết theo cú pháp của X, ví dụ
     `("robotics" OR "embodied AI") -is:retweet`. Bấm **Tìm trên X** (bài đăng trong 7 ngày qua và tác giả của chúng).
   - Nhập các tài khoản X gốc rồi bấm **Tìm người họ theo dõi trên X**.
   - Bấm **Chấm điểm** để xếp hạng theo tiểu sử X và các bài đăng về AI/robot.
2. **Duyệt tin:**
   - Bản nháp trích nguyên văn bài đăng hoặc tiểu sử X, kèm đường dẫn tới bằng chứng đã kiểm.
   - Sửa nếu cần rồi bấm **Duyệt**.
3. **Gửi tin:**
   - **⚡ Gửi qua X API** gửi từ tài khoản bạn đã kết nối, nhưng chỉ tới tài khoản có trong `SEND_ALLOWLIST` (X cấm
     gửi DM tự động cho người không yêu cầu). Với người khác, dùng **Tự tay gửi**, giống chế độ 1.
4. **Theo dõi và lấy trả lời:**
   - Bấm **🔄 Lấy trả lời từ X**: app đọc 100 tin DM mới nhất; nếu người nhận đã nhắn lại cho bạn thì tin đã gửi được
     đánh dấu «đã trả lời» và chuyển vào **Cần xử lý**. Vẫn có thể bấm **Đánh dấu đã trả lời** bằng tay.

## Chạy thử không cần khoá nào (dữ liệu mẫu)

1. Trong `.env`, đặt `X_MODE=fake` và `SEND_ALLOWLIST=alex_builder,sarah_robotics` (hai người trong dữ liệu mẫu).
2. Chạy `streamlit run app.py`. Thanh bên trái hiện `CHẾ ĐỘ THỬ (KHÔNG CẦN MẠNG)`: hồ sơ GitHub và X mẫu, bản nháp
   theo mẫu, không dùng mạng, không cần khoá. Cả hai chế độ đều chạy được.
3. **Tìm người** → tạo chiến dịch với từ khoá `robotics, robot learning` → `Tìm trên GitHub` (hoặc `Tìm trên X`) →
   `Chấm điểm` · **Duyệt tin** → `Soạn N bản nháp tiếp theo` → `Duyệt` · **Gửi tin** → `Bắt đầu gửi` → `Tôi đã gửi`
   (hoặc `⚡ Gửi qua X API`) · **Theo dõi** → `Đánh dấu đã trả lời` → `Đã xử lý xong`.

Dữ liệu mẫu nằm ở `data/fake.db`; xoá tệp này để làm lại từ đầu. Đặt lại `X_MODE=real` để dùng dữ liệu thật
(`data/outreach.db`).

## Nhắn cho người thật (`SEND_MODE=live`)

`SEND_MODE=allowlist` (mặc định) chặn mọi người không có trong `SEND_ALLOWLIST`. Hãy giữ nguyên khi còn thử.

`SEND_MODE=live` cho phép gửi tới **bất kỳ người nào đã được duyệt, nhưng chỉ qua kênh tự tay gửi**: bạn vẫn đọc và
duyệt từng bản nháp, tự bấm Gửi trên X, và không vượt `DAILY_SEND_CAP` (mặc định 20 tin trong 24 giờ).

Kênh X API (ở cả hai chế độ) luôn chỉ gửi cho `SEND_ALLOWLIST`, kể cả khi bật live. Luật tự động hoá của X cấm gửi DM
tự động cho người chưa đồng ý được liên hệ, dù từng tin đã được người duyệt.

## Chi phí và tính năng trả phí

Chế độ GitHub + tự tay gửi + soạn nháp theo mẫu tốn **0 USD**. Mọi thứ dưới đây là tuỳ chọn và có trả phí.
Giá X là giá ước tính theo từng loại dữ liệu, ghi trong `outreach/config.py` (`PRICES`: đọc một bài đăng $0.005, đọc
một người dùng $0.010, đọc một tin DM $0.010, gửi một DM $0.015); hãy xem bảng giá hiện tại của X trước khi dựa vào.

| Tính năng | Cần bật | Chi phí ước tính | Tình trạng |
|---|---|---|---|
| X gốc: Tìm trên X | X App + Kết nối tài khoản X | tối đa 10 bài đăng + 10 tác giả ≈ $0.15 mỗi lần bấm | Mới thử bằng dữ liệu mẫu và mock |
| X gốc: Tìm người họ theo dõi | như trên | tra tài khoản gốc $0.010 + tối đa 40 tài khoản × ($0.010 + 5 bài × $0.005) ≈ tối đa $1.41 mỗi tài khoản gốc | Mới thử bằng dữ liệu mẫu và mock |
| X gốc: Thêm từ X | như trên | $0.010 + 5 bài × $0.005 = $0.035 mỗi tài khoản | Mới thử bằng dữ liệu mẫu và mock |
| Gửi qua X API (cả hai chế độ) | Chế độ 2, hoặc `SEND_CHANNEL=api` ở chế độ 1 | $0.025 mỗi tin (kiểm hội thoại cũ $0.010 + gửi $0.015), thêm $0.010 nếu chưa biết mã người dùng X | Mới thử bằng mock. Chỉ gửi cho người trong allowlist |
| X gốc: Lấy trả lời từ X | như trên | tối đa 100 tin DM × $0.010 = tối đa $1.00 mỗi lần bấm | Mới thử bằng dữ liệu mẫu và mock |
| Soạn nháp bằng Claude | `LLM_PROVIDER=anthropic`, `ANTHROPIC_API_KEY`, `LLM_MODEL`, `LLM_PRICE_IN` / `LLM_PRICE_OUT` (USD cho mỗi triệu token) | Tính theo token; thanh bên trái hiện `Chi phí hôm nay` | Mới thử bằng mock |

Hồ sơ của người thật chỉ được gửi tới mô hình chạy trên máy (Ollama) hoặc API trả phí (Anthropic). Cố ý không hỗ trợ
mô hình miễn phí trên mây: điều khoản của họ cho phép nhà cung cấp đọc những gì bạn gửi.

## Giới hạn và các thao tác bị chặn

Khi công cụ từ chối việc gì, nó hiện lý do (lý do giữ nguyên tiếng Anh như trong app, thường đứng sau chữ
«Không gửi được:»). Ý nghĩa từng lý do và cách gỡ:

| Lý do hiện ra | Vì sao | Cần làm gì |
|---|---|---|
| `not on SEND_ALLOWLIST (safety mode)` | Đang bật `SEND_MODE=allowlist` | Thêm tên X của người đó vào `SEND_ALLOWLIST`, hoặc đổi sang `SEND_MODE=live` (kênh tự tay gửi) |
| `daily cap reached (n/cap)` | Đã gửi hoặc đang gửi đủ `DAILY_SEND_CAP` tin trong 24 giờ qua | Chờ, hoặc tăng `DAILY_SEND_CAP` |
| `marked do-not-contact` | Bạn đã bật «Không liên hệ» cho người này | Tắt nó ở tab **Theo dõi** nếu bật nhầm |
| `not approved` | Chỉ tin đã duyệt mới gửi được | Duyệt tin ở tab **Duyệt tin** |
| `evidence not verified — edit the text first` | Có câu trích trong bản nháp không khớp từng chữ với nguồn | Đọc bản nháp so với bằng chứng rồi sửa; sau đó duyệt hay không là do bạn quyết |
| `existing conversation` | Bạn đã bấm `Đã liên hệ từ trước`, hoặc API thấy hai bên đã từng nhắn nhau | Không cần làm gì: công cụ sẽ không bao giờ nhắn người đó nữa |
| `api channel is limited to SEND_ALLOWLIST (X automation rules)` | Xem mục trên | Dùng kênh tự tay gửi |
| `recipient does not accept DMs from this account` | Kênh API: X báo người này không nhận DM từ bạn | Bỏ qua người này |
| Trạng thái `unknown` trong **Cần xử lý** | Kênh API: X không phản hồi kịp, nên công cụ không biết DM đã đi hay chưa | Xem hội thoại trên X, rồi bấm `Tin đã đi` hoặc `Tin chưa đi`. Công cụ không bao giờ tự gửi lại |
| GitHub chạm giới hạn số lần gọi, kèm giờ thử lại | GitHub cho mỗi token 30 lượt tìm mỗi phút và 5.000 lệnh gọi mỗi giờ | Chờ tới giờ được báo. Những người đã tìm được vẫn được lưu |

Giới hạn đã biết:
- Chế độ X gốc mới chạy với dữ liệu mẫu và phản hồi X giả lập, chưa từng chạy với X API thật.
- Chế độ GitHub chỉ tìm được người có ghi tài khoản X trên hồ sơ GitHub. Trong hai lần tìm thật, 254/264 và 480/510
  tài khoản GitHub được kiểm không có.
- Tìm trên X chỉ thấy bài đăng trong 7 ngày gần nhất.
- «Lấy trả lời từ X» chỉ nhận ra câu trả lời đầu tiên của mỗi tin; nếu người đó nhắn tiếp sau khi bạn đã bấm
  `Đã xử lý xong` thì phải bấm `Đánh dấu đã trả lời` bằng tay. Không có tính năng này (chế độ 1) thì luôn đánh dấu
  bằng tay.
- Câu trích dài tối đa 120 ký tự, cắt ở ranh giới từ, nên có thể dừng giữa câu. Hãy sửa lại khi duyệt.
- Người cần điểm phù hợp từ 40 trở lên mới được soạn nháp. Không có tin nhắn nhắc lại tự động.
- Hai chế độ dùng chung một danh sách người cho mỗi chiến dịch.
- Một lần tìm thật trên GitHub kiểm từng tài khoản tìm được, có thể mất vài phút. Trang không hiện tiến độ cho tới khi
  xong.

---

## Chạy test

Chạy toàn bộ 149 test (không cần mạng) để kiểm tra hệ thống:
```bash
pytest -q
```
Mọi test đều chạy khi lệnh gọi mạng bị tắt, để kết quả không phụ thuộc bên ngoài.

---

## Tuân thủ nền tảng và lý do an toàn

Nhắn tin làm quen người lạ (cold outreach) chạm tới luật của nền tảng và quy định, nên công cụ làm như sau:
1. **Luật tự động hoá của X:** X cấm gửi DM hàng loạt hoặc tự động cho người không yêu cầu.
   - **Chế độ GitHub** để việc gửi là thủ công: 0 USD, và mỗi DM đều do một người bấm Gửi.
   - **Kênh X API** chỉ gửi tự động tới các tài khoản trong `SEND_ALLOWLIST`, để không lỡ tay nhắn hàng loạt.
2. **Chính sách sử dụng của GitHub:** dữ liệu GitHub API chỉ dùng để liên hệ đúng người trong lĩnh vực, không cào
   dữ liệu (scraping), không spam.
3. **Chặn bịa đặt:** mô hình AI không được bịa thông tin. Câu trích nào cũng phải có nguyên văn trong kho mã hoặc tiểu
   sử nguồn (`evidence_ok=1`); nếu không, app không cho duyệt cho tới khi người kiểm và sửa.
4. **Chống trùng vĩnh viễn:** bảng tin nhắn trong SQLite có ràng buộc `UNIQUE(prospect_id)`. Không ai có thể nhận
   hai tin làm quen.

---

## Bảng cấu hình (`.env`)

| Biến | Mặc định | Ý nghĩa |
|:---|:---|:---|
| `X_MODE` | `real` | `real`: dùng GitHub và X API thật; `fake`: dữ liệu mẫu, không cần mạng (dùng để thử). |
| `GITHUB_TOKEN` | `""` | Token GitHub (chỉ đọc kho công khai). |
| `SEND_CHANNEL` | `manual` | `manual` (tự tay gửi: sao chép tin + mở trang X) hoặc `api` (X API v2). |
| `SEND_MODE` | `allowlist` | `allowlist` (chỉ người trong `SEND_ALLOWLIST` nhận được tin) hoặc `live`. |
| `SEND_ALLOWLIST` | `""` | Các tên X được phép nhận tin khi thử, cách nhau bằng dấu phẩy. |
| `DAILY_SEND_CAP` | `20` | Số tin tối đa trong 24 giờ gần nhất. |
| `LLM_PROVIDER` | `template` | `template` (0 USD), `ollama` (0 USD, chạy trên máy) hoặc `anthropic` (API trả phí). |
| `OLLAMA_MODEL` | `qwen3:4b` | Tên mô hình Ollama khi `LLM_PROVIDER=ollama`. |
| `ANTHROPIC_API_KEY`| `""` | Khoá API, bắt buộc khi `LLM_PROVIDER=anthropic`. |
| `X_CLIENT_ID` | `""` | OAuth 2.0 Client ID cho kênh DM qua X API. |
| `X_CLIENT_SECRET` | `""` | OAuth 2.0 Client Secret cho kênh DM qua X API. |
| `X_REDIRECT_URI` | `http://127.0.0.1:8765/callback` | Địa chỉ X gọi lại sau khi đăng nhập, phải trùng với địa chỉ đã đăng ký trong X Developer Portal. |

---

## Gỡ lỗi thường gặp

| Dấu hiệu | Nguyên nhân | Cách xử lý |
|:---|:---|:---|
| `doctor: Missing required configuration keys: GITHUB_TOKEN` | `.env` chưa có token | Thêm token GitHub hợp lệ vào `.env`. |
| `doctor: GitHub rejected GITHUB_TOKEN` | Token sai hoặc hết hạn | Tạo token mới tại [github.com/settings/tokens](https://github.com/settings/tokens). |
| `Không gửi được: not on SEND_ALLOWLIST (safety mode)` | Đang bật danh sách cho phép | Thêm tên X của người đó vào `SEND_ALLOWLIST` trong `.env`. |
| `evidence not verified — edit the text first` | Câu trích không khớp nguyên văn với nguồn | Sửa bản nháp ở tab Duyệt tin cho khớp bằng chứng. |
| `daily cap reached` | Đã chạm trần số tin trong 24 giờ | Chờ qua khung 24 giờ, hoặc chỉnh `DAILY_SEND_CAP` trong `.env`. |
| `streamlit is not recognized` | Chưa bật môi trường ảo | Chạy `.venv\Scripts\activate` (Windows) hoặc `source .venv/bin/activate` (macOS/Linux). |

---

## Quyền riêng tư và lưu trữ

Mọi dữ liệu chỉ nằm trên máy bạn, trong SQLite (`data/outreach.db`). Khoá và token chỉ nằm trong `.env`, không bao giờ
được commit lên git. Streamlit đã tắt gửi số liệu sử dụng (telemetry) trong `.streamlit/config.toml`.
