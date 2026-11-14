# Rà soát Giai đoạn 7 — Chạy thật, tài liệu, nộp bài

Ngày 2026-11-14 · Người rà: một subagent mới của Claude (không làm GĐ7), chỉ đọc. Nó đọc `git diff gd-6-ok..gd-7`, mục GĐ7
trong `docs/quy_trinh_trien_khai.md` và `docs/assignment.md`. Claude phiên chính kiểm lại từng mục với tệp rồi mới sửa.

## Kết luận

**Đạt sau khi sửa. Đã gắn `gd-7-ok`.**

- Bằng chứng 7.1 vững: số đếm khớp nhau (30 + 0 + 480 = 510 tài khoản, 14 bản nháp = 12 + 1 + 1, 45 = 20 + 15 + 10 điểm),
  giờ trong CSDL khớp ảnh chụp X, ba ảnh không lộ token. 7.3 đạt (115 giây).
- Có 5 mục phải sửa. Mục nặng nhất: tại `gd-7`, `pytest -q` ở gốc repo hỏng, nên câu «7.6 sạch» không lặp lại được.
- Sau khi sửa: `pytest -q` → `140 passed`; chạy chặn mạng → `140 passed`, `blocked network attempts: 0`.

## Phải sửa — đã sửa

| # | Lỗi | Tình huống hỏng | Sửa |
|---|---|---|---|
| 1 | 7.6 không lặp lại được | Bản clone thử `data/t73` (tạo sau lần đo 7.6) có test trùng tên → `pytest -q` ở gốc: `11 errors`, `import file mismatch` | Thêm `pytest.ini` với `testpaths = tests`. Kiểm: đặt tạm một test trùng tên dưới `data/` → không có `pytest.ini`: `1 error`; có: `140 passed`. Dán output chạy lại vào `gd-7.md` mục 2 |
| 2 | `writeup.md` nói sai về rà soát | «Each stage ended with a review by a fresh Claude subagent … reran the tests with the network blocked». Thực tế: GĐ1–2 do Claude rà (`gd-1-ra-soat.md`, `gd-2-ra-soat.md`), GĐ3 có subagent nhưng không chạy chặn mạng, chỉ GĐ4–6 có cả hai | Viết lại: Claude rà GĐ1–2; từ GĐ3 subagent mới; từ GĐ4 thêm chặn mạng |
| 3 | Không làm theo được `demo_script.md` | Sau 7.1, B đã có tin `sent` và đã có hội thoại với A; mỗi người chỉ một tin (`messages.prospect_id UNIQUE`). Cảnh 6 «`Start` on B again» không làm được trên giao diện: tab Send chỉ có tin `approved`, tab Review chỉ có `draft` / `failed` | Thêm bước chuẩn bị: đổi tên `data/outreach.db`, xoá hội thoại A–B của 7.1 hoặc dùng tài khoản thử mới. Cảnh 6: cho thấy B đã rời Review và Send |
| 4 | Dùng thử dữ liệu mẫu có thể đi vào ngõ cụt | README không gợi ý từ khoá. Đo bằng `score_fit` trên `FakeGitHub`: `AI` → alex 0, sarah 0 (không ai có bản nháp); `robotics` → sarah 35, dưới ngưỡng 40 dù README cho sarah vào danh sách gửi; `robotics, robot learning` → 60 và 55 | README ghi rõ từ khoá `robotics, robot learning` |
| 5 | Lộ tên một người thật ngoài cuộc | `gd-7.md:18` ghi tên X của người thật được dùng để thử chặn, trong khi ảnh đã cắt để giấu tên người thật | Thay bằng «(ẩn tên)» ở bản hiện tại. Tên vẫn còn trong lịch sử git (commit `21d2362`). Repo chưa có remote. Không viết lại lịch sử |

## Nên sửa — đã sửa luôn

- **README, mục dữ liệu:** «Keys live only in `.env`» chưa đủ: token đăng nhập X của kênh API nằm trong SQLite (`kv`
  khoá `oauth`, `auth.py:94`). «Nothing is sent anywhere except…» chưa đúng: Streamlit mặc định gửi thống kê sử dụng
  (`browser.gatherUsageStats` = `True`). Thêm `.streamlit/config.toml` tắt nó (kiểm: chạy trong repo ra `False`, ngoài
  repo ra `True`), và README nói cả hai điều.
- **README, kênh API:** thêm bước đăng ký callback `http://127.0.0.1:8765/callback` trong X App (`config.X_REDIRECT_URI`,
  `auth.py:147` cố định cổng 8765).
- **README, Known limits:** tìm thật mất vài phút và trang không báo tiến độ.
- **`writeup.md`:** «Every fix came with a test that failed first» → «Every code fix…» (mục phải sửa 1 của GĐ4 là sửa
  báo cáo). Writeup giờ 598 từ.
- **`demo_script.md`:** cảnh 1 bỏ «drafting model» (`doctor` không in dòng mô hình khi dùng `template`); cảnh 3 bỏ «reasons
  with links» (cột lý do ở tab Find là chữ thường, liên kết chỉ có ở Review); ghi chú quay: tìm thật mất vài phút, quay
  trước rồi cắt hoặc dùng `Add GitHub accounts`.
- **`gd-7.md` 7.6:** câu «dòng duy nhất khớp là dòng quy trình» không còn đúng sau khi chính báo cáo chứa mẫu tìm. Đã ghi rõ.

## Ghi nhận — chưa sửa

- `writeup.md` 598 từ, sát ngưỡng một trang.
- Chưa đo thời gian tải mô hình Ollama (đã nêu ở `gd-7.md`, vì dùng `template`).
- README ghi Python 3.11 trở lên, khớp `streamlit` 1.67, nhưng mới thử trên 3.14.
- `doctor` vẫn PASS khi `pip` cài hỏng giữa chừng. README có dòng xử lý lỗi `pip`.
- `doctor` in «not reachable» cho Ollama; README trích câu lỗi lúc soạn tin («Ollama is not running at…», `llm.py:110`). Cả
  hai đều có thật.
- «What comes next» trong writeup bỏ qua vài mục cố ý không làm (chạy nền, ORM, API XChat).
- `data/t73` không còn trong `data/` lúc sửa (14/11). Phiên này không xoá nó.

## Đã kiểm, thấy đúng

- README: mọi chuỗi lý do trong bảng giới hạn có trong mã (`sender.py`, `review.py`, `app.py`); tên nút, lệnh `doctor`,
  `auth`, `streamlit run app.py`, biến môi trường, tên người mẫu, ngưỡng 40 / 120 ký tự / 20 tin mỗi ngày.
- Writeup: 254/264 (`gd-3.md`), 480/510, đơn giá 0,035 USD (`config.py`), 140 test, 3 mục phải sửa của GĐ6, GĐ2 bị trả
  lại, test gọi mạng thật ở GĐ3; Antigravity viết GĐ1–2b (không commit nào tới `gd-2-ok` có dòng đồng tác giả Claude).
- `LLM_PROVIDER=template` thống nhất ở `config.py`, `.env.example`, README, `tests/conftest.py`, khớp «Đã chốt».
- Kịch bản quay đủ 8 ý; `test_approve_requires_verified_evidence` có thật.
- Không có email nào ngoài `hr@genaifund.ai` (từ đề bài), không có số điện thoại.

## Output kiểm sau khi sửa

```
git ls-files | grep -E '(^|/)\.env$|^data/|\.db$'                       → (không có dòng nào, exit 1)
git grep -nE "sk-ant-[A-Za-z0-9_-]{10,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"   → (không có dòng nào, exit 1)
pytest -q                → 140 passed in 17.55s
pytest -q -p nonet       → [nonet] blocked network attempts: 0 []
                           140 passed in 16.29s
```

Plugin `nonet` (để ngoài repo) chặn `socket.socket.connect` / `connect_ex`, `httpx.HTTPTransport.handle_request` và
`httpx.AsyncHTTPTransport.handle_async_request`. Nó chỉ cho qua cặp socket nội bộ do `socket.socketpair` tạo (asyncio cần
trên Windows). Lần chạy của subagent, cùng cách chặn: `140 passed`, 0 lần bị chặn.
