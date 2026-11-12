# Rà soát Giai đoạn 1 — Khung dự án và cơ sở dữ liệu

Ngày 2026-11-12 · Người rà: Claude · Phạm vi: `b3c3225..gd-1` (3 commit, 10 tệp).

## Kết luận

**Chưa gắn `gd-1-ok`: còn 2 mục phải sửa, cả hai ở `outreach/config.py`.** Phần cơ sở dữ liệu và test đúng
thiết kế. Hai mục này là chỗ bản quy trình không nêu, không phải làm sai quy trình.

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

## Câu lệnh dán cho Antigravity

```
Đọc docs/bao_cao/gd-1-ra-soat.md. Sửa mục 1 và 2 («phải sửa») theo thứ tự, mỗi mục một commit kèm test tái
hiện lỗi. Sửa tiếp mục 3 và 4, mỗi mục một commit. Chạy lại pytest -q, dán output vào cuối
docs/bao_cao/gd-1.md rồi DỪNG. Không làm sang Giai đoạn 2.
```
