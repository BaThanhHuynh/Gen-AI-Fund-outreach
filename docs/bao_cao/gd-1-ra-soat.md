# Rà soát Giai đoạn 1 — Khung dự án và cơ sở dữ liệu

Ngày 2026-11-12 · Người rà: Claude · Phạm vi: `b3c3225..gd-1` (3 commit, 10 tệp).

## Kết luận

**Vòng 3 (2026-11-12, tại `29eb0cc`): đạt. Không còn mục «phải sửa». Đã gắn tag `gd-1-ok` tại `29eb0cc`.**

Vòng 2 (tại `cff0304`): mã đạt, bốn mục vòng 1 đã sửa đúng; còn 1 chỗ phải sửa ở test (mục 5) — đã sửa xong
ở vòng 3.

Vòng 1 (tại `gd-1`): còn 2 mục phải sửa, cả hai ở `outreach/config.py`. Phần cơ sở dữ liệu và test đúng thiết
kế. Hai mục này là chỗ bản quy trình không nêu, không phải làm sai quy trình.

## Rà soát lại — vòng 3

Phạm vi: `cff0304..29eb0cc` (4 commit, mỗi mục một commit đúng yêu cầu). `pytest -q` trong `.venv`
(Python 3.14.7): `12 passed`. Sau khi chạy, `git status` sạch và test không tạo thư mục `data/`.

Thử phá từng dòng mã trên bản sao:

| Dòng bị phá | Kết quả |
|---|---|
| Bỏ commit trong `kv_set` (mục 5) | `test_writes_are_visible_to_second_connection` hỏng: `assert None == {'synced': True}` |
| Bỏ commit trong `record_usage` | cùng test hỏng: `assert 0.0 == 0.01` |
| Bỏ dòng tạo thư mục trong `connect()` | cùng test hỏng: `unable to open database file` |
| Gỡ `validate_choice` ở `X_MODE` (mục 6) | `test_module_load_fails_on_invalid_x_mode` hỏng |
| Gỡ `validate_choice` ở `SEND_MODE` (mục 6) | `test_module_load_fails_on_invalid_send_mode` hỏng |
| Bỏ phép chia `1_000_000` ở nhánh `llm_in` của `record_usage` | **không test nào hỏng** — không chặn, xem «Ghi nhớ cho giai đoạn sau» |

Mục 7: đặt `.env` có `X_MODE=real`, `SEND_MODE=live`, `LLM_PRICE_IN=3`, `LLM_PRICE_OUT=15`, tên mô hình và
redirect URI khác, khoá giả. Nạp cấu hình ngoài pytest thấy `real live 3.0`, tức tệp `.env` có được đọc. Trong
pytest, cả 11 biến đều về giá trị ghim và 12 test vẫn qua.

Lời khai «đã thấy test hỏng khi tạm bỏ commit trong `kv_set`» ở `gd-1.md` khớp với kết quả tự thử.

Tuỳ chọn, không cần quay lại sửa: `docs/bao_cao/gd-1.md` còn dòng trống thừa cuối tệp
(`git diff --check gd-1..HEAD`).

## Rà soát lại — vòng 2

Phạm vi: `gd-1..cff0304` (5 commit). `pytest -q` trong `.venv`: `10 passed`.

Đã kiểm và đạt:

- Mục 1: chạy từ thư mục khác, `DB_PATH` vẫn tuyệt đối và nằm dưới gốc dự án. Đổi lại thành đường dẫn tương
  đối thì `test_db_path_is_absolute_and_anchored_to_project_root` hỏng.
- Mục 2: `X_MODE=fak` và `SEND_MODE=allowlst` làm ứng dụng dừng với `ValueError` nêu tên biến và các giá trị
  hợp lệ. `X_MODE='  REAL '` vẫn được nhận là `real`. `LLM_PRICE_IN` để trống thành `0.0`.
- Mục 3: đặt `.env` có `X_MODE=real`, `SEND_MODE=live`, khoá giả → test vẫn thấy `fake`, `allowlist`, khoá rỗng.
- Mục 4: bỏ commit trong `record_usage`, hoặc bỏ dòng tạo thư mục → test thứ 7 hỏng.

### 5. Phải sửa — test thứ 7 không còn canh được `kv_set` — `tests/test_db.py:100`

Đây là tác dụng phụ từ chính gợi ý ở mục 4 của người rà. Test gọi `kv_set` rồi `record_usage` trên cùng kết
nối A trước khi đọc. Lệnh commit trong `record_usage` lưu luôn phần ghi của `kv_set`. Đã thử: bỏ commit trong
`kv_set`, cả 10 test vẫn qua (ở vòng 1 test này hỏng). `kv_set` là nơi lưu token đổi mới, nên dòng commit
này phải có test canh.

Mong đợi: đọc `kv_get` qua kết nối B **trước** khi gọi `record_usage` trên A. Thứ tự: `kv_set` qua A → mở B →
`kv_get` qua B → `record_usage` qua A → `spend_since` qua B.
Kiểm: tạm bỏ `conn.commit()` trong `kv_set` thì test phải hỏng; trả lại thì qua.

### Nên sửa cùng lượt

6. **Chưa có test canh việc `config.py` thật sự gọi `validate_choice`.** Đã thử: gỡ lời gọi ở `X_MODE` hoặc ở
   `SEND_MODE`, cả 10 test vẫn qua — ba test hiện có chỉ thử hàm. Thêm một test nạp cấu hình với `X_MODE=fak`
   (ví dụ chạy tiến trình con `python -c "import outreach.config"` với biến môi trường đó, mong mã thoát khác
   0 và stderr có `X_MODE`), và một test tương tự cho `SEND_MODE`.
7. **`tests/conftest.py` chưa ghim `LLM_PRICE_IN`, `LLM_PRICE_OUT`, `LLM_MODEL`, `X_REDIRECT_URI`.** Đã thử:
   `.env` có `LLM_PRICE_IN=3` thì test thấy `3.0`. Test tính tiền mô hình ở giai đoạn 4 sẽ cho kết quả khác
   nhau tuỳ máy.

Tuỳ chọn: bốn tệp có dòng trống thừa ở cuối (`git diff --check gd-1..HEAD`).

---

*Phần dưới là nội dung vòng 1, giữ nguyên để đối chiếu.*

## Đã kiểm và đạt

- `pytest -q` trong `.venv` (Python 3.14.7): `7 passed in 0.08s`.
- Schema trong `outreach/db.py` khớp mục 3 của quy trình, đủ 6 bảng, đúng từng cột và ràng buộc.
- `requirements.txt` có đúng 5 dòng, phiên bản trùng với `pip list` trong `.venv`.
- `git status` sạch; `.env`, `data/`, `.venv/`, `*.db` đều bị bỏ qua (`git check-ignore`); không có chuỗi giống
  khoá trong tệp đã commit.
- Ba bổ sung đã duyệt đều có trong mã: `kv_set` và `record_usage` tự commit, `connect()` tạo thư mục cha, test
  thứ 7.
- `.env.example`: dòng `SEND_ALLOWLIST=   # comma-separated usernames` được đọc thành danh sách rỗng (đã thử
  với python-dotenv 1.2.4).
- Thử phá từng dòng mã trên bản sao để xem test nào bắt được:

| Dòng bị phá | Kết quả |
|---|---|
| Bỏ commit trong `kv_set` | `test_writes_are_visible_to_second_connection` hỏng |
| Bỏ `PRAGMA foreign_keys = ON` | `test_message_requires_existing_prospect` hỏng |
| Bỏ `UNIQUE` ở `messages.x_user_id` | `test_one_message_per_person` hỏng |
| Bỏ `CHECK` ở `messages.status` | `test_status_check_constraint` hỏng |
| Đổi đơn giá `post_read` | `test_record_usage_cost` hỏng |
| Bỏ `IF NOT EXISTS` | `test_init_db_is_idempotent` hỏng |
| Bỏ commit trong `record_usage` | **không test nào hỏng** (mục 4) |
| Bỏ dòng tạo thư mục trong `connect()` | **không test nào hỏng** (mục 4) |

## Phải sửa

### 1. Tệp cơ sở dữ liệu nằm ở đâu tuỳ thư mục đang đứng — `outreach/config.py:45`

`DB_PATH` là đường dẫn tương đối (`data/fake.db`), nên `connect()` tạo tệp dưới thư mục đang đứng lúc chạy
lệnh. Đã thử: chạy từ một thư mục khác, tệp nằm dưới thư mục đó, không nằm dưới thư mục dự án.

Hậu quả: chạy `streamlit run <đường dẫn>/app.py` từ chỗ khác sẽ mở một cơ sở dữ liệu mới, trống. Lịch sử «đã
nhắn ai» nằm ở tệp cũ, nên luật «mỗi người một tin» không còn chặn được việc nhắn lại.

Mong đợi: `DB_PATH` là đường dẫn tuyệt đối, neo vào thư mục gốc dự án (thư mục cha của `outreach/`).
Test: `Path(config.DB_PATH).is_absolute()` và thư mục `data/` nằm ngay dưới gốc dự án.

### 2. Gõ sai `X_MODE` hoặc `SEND_MODE` vẫn chạy, và chạy theo hướng nguy hiểm — `outreach/config.py:9, 21, 45`

Đã thử:
- `X_MODE=fak` → không báo lỗi, `DB_PATH` thành `data/outreach.db` (cơ sở dữ liệu thật).
- `SEND_MODE=allowlst` → không báo lỗi, giá trị giữ nguyên `'allowlst'`. Mã giai đoạn 5 nếu viết
  `if SEND_MODE == "allowlist"` thì lỗi gõ này tắt luôn danh sách cho phép.

Mong đợi: `X_MODE` chỉ nhận `fake` hoặc `real`; `SEND_MODE` chỉ nhận `allowlist` hoặc `live`. Giá trị khác thì
dừng ngay lúc nạp cấu hình, thông báo nêu tên biến và các giá trị hợp lệ. Không in giá trị của biến chứa khoá.
Test: một giá trị sai cho mỗi biến → `ValueError`. Gợi ý: tách việc đọc-và-kiểm thành một hàm nhỏ để test gọi
thẳng, khỏi phải nạp lại mô-đun.

## Nên sửa (không chặn, làm cùng lượt)

3. **Test đang đọc `.env` thật của máy.** `config.py` gọi `load_dotenv()` lúc nạp. Đã thử: đặt `.env` có
   `X_MODE=real`, test thấy `X_MODE='real'` và `DB_PATH='data/outreach.db'`. Hiện chưa có `.env` nên chưa lộ.
   Khi có khoá thật, một test gọi `connect()` không tham số sẽ ghi vào cơ sở dữ liệu thật. Mong đợi: đầu
   `tests/conftest.py`, trước khi nạp `outreach`, gán sẵn các biến cấu hình (`X_MODE=fake`,
   `SEND_MODE=allowlist`, các khoá để rỗng); `load_dotenv()` không ghi đè biến đã có.
4. **Hai dòng mã chưa có test canh** (hai dòng cuối bảng trên). Mở rộng test thứ 7: giữ kết nối A đang mở, gọi
   thêm `record_usage` qua A, rồi kiểm `spend_since` qua kết nối B; và cho `file_db` trỏ vào một thư mục con
   chưa tồn tại (`tmp_path / "sub" / "test.db"`).

## Tuỳ chọn

- Import thừa: `os` (`outreach/db.py:2`), `sqlite3` và `init_db` (`tests/conftest.py:7, 9`). `Path` ở
  `outreach/config.py:2` hiện thừa, sẽ được dùng sau khi sửa mục 1.
- `LLM_PRICE_IN=` để trống làm ứng dụng dừng với `ValueError: could not convert string to float: ''`, không
  nêu tên biến. Sửa chung với hàm kiểm ở mục 2 nếu tiện.

## Ghi nhớ cho giai đoạn sau

- `kv_set` và `record_usage` commit mọi thay đổi đang chờ trên cùng kết nối. Giai đoạn 5 không được gọi hai
  hàm này giữa lúc đang giữ chỗ một tin (`approved → sending`) mà chưa commit.
- Username trên X không phân biệt hoa thường; giai đoạn 5 so `SEND_ALLOWLIST` phải đưa cả hai về chữ thường.
- Test và mã nằm chung commit `ad16d07`, nên lịch sử git không chứng minh được «viết test trước»; chỉ có
  output dán trong `gd-1.md`. Từ giai đoạn 2, commit test riêng trước commit mã.
- (Vòng 3) Nhánh `llm_in` / `llm_out` của `record_usage` chưa có test, và `tests/conftest.py` ghim đơn giá mô
  hình bằng 0 nên phép tính nào cũng ra 0. Test tính tiền mô hình ở giai đoạn 4 phải tự đặt đơn giá khác 0 và
  khác nhau cho hai chiều (ví dụ `monkeypatch.setattr(config, "LLM_PRICE_IN", 3.0)`, `LLM_PRICE_OUT` là
  `15.0`), rồi so `spend_since` với con số tính tay.
- (Vòng 3) Giai đoạn 1 kết thúc với 12 test, quy trình tính từ 6. Các mốc «N test qua» ở giai đoạn sau cộng
  thêm 6 (giai đoạn 2: 23 thay vì 17).

## Câu lệnh dán cho Antigravity

Giai đoạn 1 đã đóng. Bắt đầu Giai đoạn 2:

```
Đọc docs/quy_trinh_trien_khai.md (mục 0, 3, 4, 5 và «Giai đoạn 2»), docs/assignment.md,
docs/knowledge/trang_thai.md và mục «Ghi nhớ cho giai đoạn sau» trong docs/bao_cao/gd-1-ra-soat.md. Thực hiện
ĐÚNG Giai đoạn 2 theo vòng 4 bước ở mục 0, không làm sang giai đoạn khác. Trình Implementation Plan và chờ
tôi duyệt trước khi viết mã. Commit test riêng, trước commit mã. Xong thì ghi docs/bao_cao/gd-2.md, cập nhật
trang_thai.md, commit, gắn tag gd-2 rồi DỪNG.
```
