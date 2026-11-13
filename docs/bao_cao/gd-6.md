# Giai đoạn 6 — Giao diện

Ngày 2026-11-13 · Người làm: Claude (phiên chính). Mọi output dưới đây chạy ở **`X_MODE=fake`**: `FakeGitHub`, soạn tin
bằng `template`, không ra mạng.

## 1. Đã làm

- **6.1** `tests/test_app_smoke.py`, commit `test(gd6)` (đỏ):
  - `test_app_runs_in_fake_mode`: đúng như kế hoạch: chạy `app.py` bằng `AppTest`, không ngoại lệ, đủ 4 tab.
  - `test_manual_flow_find_to_handled` (thêm): đi hết luồng 6.3 bằng chính các nút của giao diện (tạo chiến dịch →
    Search GitHub → Score → Draft → Approve → Start → I sent it → Mark replied → Mark handled). Cuối cùng kiểm trong
    CSDL: tin ở `sent`, kênh `manual`, có `sent_at`, `replied_at`, `handled_at` và đúng ghi chú.
  - Cả hai test trỏ `config.DB_PATH` vào thư mục tạm, không đụng `data/fake.db`.
- **6.2** `app.py` (Streamlit, 4 tab). Chỉ đọc dữ liệu để hiện và gọi hàm có sẵn ở `outreach/`:
  - **Thanh bên:** `SAMPLE DATA` / `LIVE`; kênh gửi (kênh API có «Connected as @…» hoặc nút `Connect X account` gọi
    `auth.login`); cách soạn tin; `Sent in last 24h: n / cap`; `ALLOWLIST: only @…` hoặc `Send mode: LIVE`;
    `Spend today: $…` (tính từ nửa đêm giờ máy).
  - **Find:** biểu mẫu chiến dịch, chọn chiến dịch, `Search GitHub` (hiện trước số truy vấn sẽ chạy; sau đó hiện bộ đếm
    gồm «n people had no X handle»), `Find people they follow`, `Add`, `Score`, bảng hồ sơ có liên kết GitHub / X.
    `GitHubRateLimited` → hiện giờ được gọi lại theo giờ máy; lỗi GitHub khác → hiện nguyên văn.
  - **Review:** `Draft next N` kèm thanh tiến độ. Mỗi bản nháp hiện tóm tắt hồ sơ, lý do phù hợp, câu trích kèm liên kết
    repo / hồ sơ, ô sửa, cảnh báo `draft_problems`, cảnh báo bằng chứng chưa khớp, nút `Approve` / `Reject`. Bị từ
    chối thì hiện nguyên văn lý do. Lỗi soạn tin (Ollama tắt, lỗi SDK Anthropic) dừng lượt và hiện lý do.
  - **Send:** danh sách `approved`, dòng nào bị chặn thì hiện lý do của `check_can_send`. Kênh tay: `Start` →
    `open_manual`; mục «Waiting for you to send» có `st.code` (nút chép sẵn), `Open @… on X`, hướng dẫn một dòng và ba
    nút `I sent it` / `Not sent` / `Already in contact`. Kênh API: `Send via X API`.
  - **Track:** số đã gửi, số trả lời, tỉ lệ. Needs attention: ba nút xác nhận kênh tay; `It was sent` / `It was not sent`
    cho `unknown`; `Mark handled` cho mục còn lại. Ô `Mark replied` kèm ghi chú, bảng nhật ký gửi, công tắc
    `Do not contact`.
  - **Khi khởi động:** `recover_stuck` chạy một lần cho mỗi phiên trình duyệt.
- **6.3** Đi hết luồng bằng test ở trên. Rồi dựng `data/fake.db` qua chính các nút của giao diện, chạy
  `streamlit run app.py` và chụp 4 tab: `gd-6-find.png`, `gd-6-review.png`, `gd-6-send.png`, `gd-6-track.png` (cùng
  thư mục). Ảnh ở trạng thái giữa luồng: tin của alex đang chờ xác nhận, tin của sarah còn là bản nháp.

## 2. Kết quả kiểm

Test hỏng trước khi có `app.py` (`.venv/Scripts/python.exe -m pytest -q`):
```
FAILED tests/test_app_smoke.py::test_app_runs_in_fake_mode - FileNotFoundErro...
FAILED tests/test_app_smoke.py::test_manual_flow_find_to_handled - FileNotFou...
2 failed, 131 passed in 54.30s
```
Sau khi có `app.py`, lần đầu (`pytest -q tests/test_app_smoke.py`): `2 passed in 21.16s`.

Toàn bộ, bản cuối (`pytest -q`):
```
133 passed in 6.99s
```
Chặn mạng. Plugin của lần rà GĐ5 chặn cả cặp socket nội bộ mà `asyncio` tạo trên Windows (xem mục 3):
```
FAILED tests/test_app_smoke.py::test_manual_flow_find_to_handled - RuntimeErr...
2 failed, 131 passed in 4.61s
blocked network attempts: 1 ["socket ('127.0.0.1', 52100)"]     # từ asyncio/proactor_events.py _make_self_pipe → socket.socketpair()
```
Plugin sửa lại, chỉ cho qua lời gọi từ `socket._fallback_socketpair` (`pytest -q -p noNet2`):
```
blocked network attempts: 0 [] | in-process asyncio socketpairs allowed: 11
133 passed in 6.36s
```
Dựng dữ liệu cho ảnh (`X_MODE=fake`, `SEND_ALLOWLIST=alex_builder,sarah_robotics`, bấm nút qua `AppTest` trên
`data/fake.db`; trước đó `data/` trống):
```
search: ['4 new, 0 already known, 2 people had no X handle (6 GitHub accounts checked).', 'Nothing needs your attention.']
score: ['Scored 4 people.', 'Nothing needs your attention.']
draft: ['2 new drafts.', 'Nothing needs your attention.'] []
drafts: {'alex_builder': 1, 'sarah_robotics': 2}
exceptions: []
{'status': 'sending', 'channel': 'manual'}
```
Chụp ảnh (Edge chạy nền, điều khiển qua DevTools, bấm từng tab):
```
Find selected: Find height: 1400 bytes: 85770
Review selected: Review height: 1400 bytes: 79557
Send selected: Send height: 1400 bytes: 66117
Track selected: Track height: 1400 bytes: 62628
```
Lỗi tìm thấy khi xem ảnh và đã sửa trước commit: tab Track in nguyên trang tài liệu `DeltaGenerator` dưới bảng nhật ký
gửi (lần chụp trước cao 5059 px). Nguyên nhân: dòng `st.dataframe(...) if log else st.caption(...)` là một biểu thức
đứng riêng, và «magic» của Streamlit in giá trị của nó. Đổi thành `if/else`. Quét cây cú pháp `app.py`: không còn biểu
thức đứng riêng nào khác ngoài lời gọi hàm. `AppTest` không bắt được lỗi này vì nó không ném ngoại lệ.

## 3. Lệch so với kế hoạch

- **Thêm test luồng** `test_manual_flow_find_to_handled`. Lý do: để 6.3 chạy lại được bằng máy, không chỉ một lần bằng
  tay. Số test là 133 chứ không phải 109: kế hoạch tính từ 108, nhưng GĐ5 kết thúc ở 131.
- **Ảnh chụp không do người bấm trong trình duyệt.** Dữ liệu được dựng bằng `AppTest` bấm đúng các nút của giao diện.
  Ảnh chụp từ server Streamlit thật, qua Edge chạy nền. `msedge --headless --screenshot` chỉ ra khung đang tải, vì nó
  không chờ websocket của Streamlit. Script chụp nằm ở thư mục nháp, không vào repo.
- **Plugin chặn mạng phải cho qua `socket.socketpair()` nội bộ.** Trên Windows, mỗi vòng lặp `asyncio` tự nối một cặp
  socket qua 127.0.0.1 trong cùng tiến trình. Đây không phải ra mạng. Kết nối tới Ollama (127.0.0.1:11434) vẫn bị chặn.
- **Tạo chiến dịch** bằng một câu `INSERT` trong `app.py`, vì `outreach/` không có hàm nào làm việc này. Câu đó chỉ ghi
  bốn ô người dùng nhập, không có luật.
- **Tab Review hiện cả tin `failed`**, kèm lý do lỗi, để sửa và duyệt lại. Đây là điều kiện kèm theo quyết định 13/11
  («failed được ẩn bằng handled»), do lần rà GĐ5 đề nghị.
- **`Draft next N`** gọi `draft_for_campaign(…, limit=1)` N lần để thanh tiến độ chạy theo từng bản. Hồ sơ bị bỏ qua
  (`LLMUnavailable`) có thể được thử lại ở lần gọi sau trong cùng lượt.
- **`Mark replied`** nằm ở ô riêng dưới Needs attention. Tin đã gửi mà chưa có trả lời không thuộc Needs attention, nên
  không có chỗ để đặt nút trong danh sách đó.
- **Thanh bên ghi `Drafts: template` khi `X_MODE=fake`**, dù `LLM_PROVIDER` khác. Lý do: `get_drafter` luôn soạn bằng
  `template` ở chế độ giả lập, nên nhãn ghi đúng cách thật sự được dùng.

## 4. Chưa kiểm được

- Chưa có người mở giao diện và bấm trong trình duyệt. Luồng chỉ được đi bằng `AppTest`, cùng 4 ảnh chụp.
- Kênh API trong giao diện (`Send via X API`, `Connect X account`, «Connected as @…») chưa chạy lần nào, kể cả ở chế độ
  giả lập. Không test giao diện nào đặt `SEND_CHANNEL=api`.
- `X_MODE=real` qua giao diện (GitHub thật, Ollama, Anthropic) chưa chạy. Thanh tiến độ với mô hình chậm chưa kiểm.
- Thông báo `GitHubRateLimited` và lỗi GitHub khác trong tab Find chưa được kích hoạt lần nào.
- Các nút `Already in contact`, `Not sent`, `It was sent` / `It was not sent`, `Reject`, công tắc `Do not contact` chưa có
  test giao diện riêng. Các hàm bên dưới đã có test ở GĐ5.

## 5. Câu hỏi cho người dùng

Không có câu hỏi mới. Các câu còn mở vẫn ở `docs/knowledge/trang_thai.md`.
