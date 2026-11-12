# Báo cáo Giai đoạn 3 — Tìm người qua GitHub

## 1. Đã làm
- 3.1: viết test trước (`tests/test_github.py`, `tests/test_discover.py`, một test trong `tests/test_doctor.py`); chạy thấy lỗi thiếu module.
- 3.2: viết `outreach/github.py` (client GitHub, `FakeGitHub`, kiểm định dạng tên X), `outreach/discover.py` (tìm theo cụm từ, theo hạt giống, nhập tay), sửa `outreach/doctor.py` (kiểm token GitHub ở chế độ thật qua `/rate_limit`).
- 3.3: chạy thật với GitHub, `X_MODE=real`, cụm từ `robotics`, `machine learning`, `max_people=10`, CSDL tạm (đã xoá).

## 2. Kết quả kiểm
- `pytest -q`: 67 passed (commit `cf01cdd`).
- 3.3 lần 1: lỗi mạng (`GitHubError`, mã 0) sau 303 giây; đã lưu 8 hồ sơ, 27 repo; bộ đếm không in được.
- 3.3 lần 2 (sau khi người dùng yêu cầu chạy lại):
  - status: ok
  - thời gian: 268.3 giây
  - counts: `{'new': 10, 'existing': 0, 'no_x_handle': 254, 'checked': 264}`
  - hồ sơ đã lưu: 10 · repo đã lưu: 37

## 3. Lệch so với kế hoạch
- Số test: kế hoạch ghi 63 passed, thực tế 67. Thêm 4 test biên: `user` trả None khi 404; lỗi 500 là `GitHubError` thường; tham số hoá 403/429 thành 2 test; `discover_by_seeds` dùng `following`.
- `GitHubClient.rate_limit()` và `run_doctor(gh=...)` thêm vào để kiểm token; kế hoạch không ghi rõ.
- Tỉ lệ `no_x_handle` rất cao (254/264): phần lớn người tìm được không có tên X hợp lệ. Đây là số đo được (10 + 0 + 254 = 264); chưa lấy mẫu để kiểm bước dò tên X có bỏ sót không.

## 4. Chưa kiểm được
- Lần chạy thật đầu bị lỗi mạng, nguyên nhân chưa rõ; lần hai chạy trơn. Chưa biết lỗi đầu có tái diễn không.
- Rà soát độc lập: xem `gd-3-ra-soat.md` (đạt sau sửa, tag `gd-3-ok`).

## 5. Câu hỏi cho người dùng
- `.env` đang có `LLM_PROVIDER=ollama`, chỉ đạo là `template`. Bạn tự đổi giúp (không sửa `.env` theo luật).
- Có muốn giữ `no_x_handle` cao như vậy, hay nới cụm từ tìm kiếm ở GĐ4?

## Sau rà soát (2026-11-13)

Sửa 5 mục «phải sửa» và 4 mục «nên sửa» của `gd-3-ra-soat.md` (`b283bb8`, `2a7ecb1`, `f8d7611`). `pytest -q`:

```
........................................................................ [100%]
72 passed in 1.31s
```
