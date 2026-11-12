# Báo cáo Giai đoạn 1 — Khung dự án và cơ sở dữ liệu

## 1. Đã làm

- Tạo commit gốc riêng lưu giữ thư mục `docs/` hiện có theo chỉ đạo (`docs: add assignment and delivery process`).
- Thiết lập tệp `.gitignore` bỏ qua các tệp/thư mục nhạy cảm và tạm thời: `.env`, `data/`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `*.db`.
- Tạo mẫu cấu hình `.env.example` với đầy đủ các tham số và ghi chú tiếng Anh.
- Khởi tạo môi trường ảo `.venv`, cài đặt thành công 5 thư viện bắt buộc và tạo tệp `requirements.txt` với đúng 5 dòng ghim phiên bản (`streamlit==1.67.0`, `httpx==0.28.1`, `anthropic==2.8.0`, `python-dotenv==1.2.4`, `pytest==9.2.0`).
- Commit nhiệm vụ 1.1: `55c5664` (`build: scaffold project, gitignore, requirements, and env template`).
- Viết bộ kiểm thử `tests/conftest.py` và `tests/test_db.py` với 7 bài test (6 bài theo tài liệu quy trình + bài thứ 7 kiểm tra đa kết nối theo yêu cầu duyệt).
- Chạy `pytest -q` ghi nhận lỗi thất bại ban đầu khi chưa có mã nguồn (Red phase).
- Xây dựng mô-đun `outreach/config.py`: nạp biến môi trường, định nghĩa đơn giá X API `PRICES` kèm liên kết tài liệu chính thức (`https://docs.x.com/x-api/getting-started/pricing`, kiểm ngày 2026-11-12), các hằng số giới hạn, scopes OAuth và đường dẫn CSDL động `DB_PATH`.
- Xây dựng mô-đun `outreach/db.py`:
  - `now()`: thời gian chuẩn ISO-8601 UTC.
  - `init_db()`: thiết lập đầy đủ 6 bảng (`kv`, `campaigns`, `prospects`, `posts`, `messages`, `usage`) với ràng buộc khóa ngoại, `UNIQUE(x_user_id)` và `CHECK` trên trạng thái tin nhắn.
  - `connect()`: tự động tạo thư mục cha nếu lưu trên đĩa, kích hoạt `Row` factory, `foreign_keys = ON`, `journal_mode = WAL` (với file DB) và tự động gọi `init_db()`.
  - `kv_get()` & `kv_set()`: lưu trữ/truy xuất JSON, tự động commit ngay trong hàm.
  - `record_usage()`: tính chi phí chính xác theo `PRICES` và đơn giá token LLM, tự động commit.
  - `spend_since()`: tổng hợp chi phí từ mốc thời gian.
- Chạy lại kiểm thử với kết quả 7/7 passed (Green phase).
- Commit nhiệm vụ 1.3: `ad16d07` (`feat(db): implement database schema, connection and usage tracking`).

## 2. Kết quả kiểm

### Lần chạy kiểm thử thất bại ở bước 1.2 (Red phase)
```
ImportError while loading conftest 'D:\codevstdio\repo\GenAIFund\tests\conftest.py'.
tests\conftest.py:4: in <module>
    from outreach.db import connect, init_db
E   ModuleNotFoundError: No module named 'outreach'
```

### Lần chạy kiểm thử thành công ở bước 1.3 (Green phase)
```
.......                                                                  [100%]
7 passed in 0.08s
```

### Kiểm tra trạng thái Git và loại trừ bảo mật
```
On branch master
nothing to commit, working tree clean
```
*(Đã kiểm chứng tạo thử file `.env` và thư mục `data/` đều được Git bỏ qua hoàn toàn, không xuất hiện trong danh sách theo dõi)*.

## 3. Lệch so với kế hoạch

Theo các điểm bổ sung được duyệt trước khi viết mã:
- **db.py:**
  - `kv_set` và `record_usage` được thiết kế tự động commit (`conn.commit()`) trước khi trả về nhằm bảo đảm dữ liệu ghi xuống đĩa ngay lập tức, ngăn ngừa thất thoát trạng thái khi xảy ra sự cố đột ngột.
  - `connect()` tự động kiểm tra và tạo thư mục cha của tệp CSDL nếu chưa có (`parent_dir.mkdir(parents=True, exist_ok=True)`), tránh lỗi `sqlite3.OperationalError` khi chạy với đường dẫn như `data/fake.db`.
- **Kiểm thử đa kết nối (Bài test thứ 7):**
  - Bổ sung `test_writes_are_visible_to_second_connection` dùng fixture `file_db` để xác nhận dữ liệu ghi nhận từ kết nối A hiển thị ngay lập tức khi mở kết nối B tới cùng file CSDL. Tiêu chí hoàn thành giai đoạn được nâng từ 6 passed lên 7 passed.
- **tests/conftest.py:**
  - Bổ sung cấu hình `sys.path.insert(0, ...)` đảm bảo `pytest -q` chạy trực tiếp từ dòng lệnh mà không bắt buộc dùng cú pháp `python -m pytest`.

## 4. Chưa kiểm được

- Chưa gọi ra mạng tới API thật của X và Anthropic (tuân thủ nguyên tắc cách ly mạng của test; việc kết nối thật sẽ được thực hiện tại Giai đoạn 2).
- Chưa kiểm tra xử lý xung đột ghi đồng thời ở tải cực cao (được xử lý thông qua cơ chế khóa nguyên tử `claim` và hàng đợi tuần tự ở Giai đoạn 5).

## 5. Câu hỏi cho người dùng

- Bạn đã hoàn thành các bước chuẩn bị của Giai đoạn 0 (tài khoản X Developer, ứng dụng OAuth Web App với callback `http://127.0.0.1:8765/callback`, mua credit tối thiểu và tạo khóa Anthropic) chưa?
- Khi sẵn sàng bước vào Giai đoạn 2, chúng ta sẽ cần các thông tin cấu hình thực tế này để chạy công cụ `doctor` và kiểm nghiệm gửi DM thử nghiệm.

---

## 6. Kết quả sửa sau rà soát (`docs/bao_cao/gd-1-ra-soat.md`)

Đã hoàn thành sửa toàn bộ 4 mục theo đúng yêu cầu:
1. **Mục 1 (commit `afc3b2a`):** Neo `DB_PATH` tuyệt đối vào thư mục gốc dự án (`PROJECT_ROOT / "data"`), kèm test tái hiện lỗi `test_db_path_is_absolute_and_anchored_to_project_root`.
2. **Mục 2 (commit `c78b2eb`):** Thêm hàm `validate_choice` dừng ngay và ném `ValueError` nếu `X_MODE` hoặc `SEND_MODE` sai giá trị cho phép, kèm test tái hiện lỗi `test_invalid_x_mode_raises_value_error` và `test_invalid_send_mode_raises_value_error`.
3. **Mục 3 (commit `022018e`):** Thiết lập trước các biến môi trường kiểm thử an toàn (`fake`, `allowlist`) ở đầu `tests/conftest.py` trước khi load `outreach`, cô lập hoàn toàn test suite khỏi `.env` thật của máy.
4. **Mục 4 (commit `5640e75`):** Mở rộng test đa kết nối `test_writes_are_visible_to_second_connection` với thư mục con chưa tồn tại (`tmp_path / "sub" / "test.db"`) và xác thực khả năng hiển thị liên kết của `record_usage` qua `spend_since` khi kết nối A vẫn mở.

### Kết quả chạy lại `pytest -q`
```
..........                                                               [100%]
10 passed in 0.17s
```

