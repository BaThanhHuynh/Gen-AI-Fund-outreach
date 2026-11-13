# Rà soát Giai đoạn 6 — Giao diện

Ngày 2026-11-13 · Người rà: một subagent mới của Claude (không viết mã GĐ6). Nó đọc `git diff gd-5-ok..gd-6`, mục 3, 4,
5 và mục GĐ6 trong `docs/quy_trinh_trien_khai.md`, cùng `docs/bao_cao/gd-6.md`. Nó thử từng kịch bản bằng `AppTest` trên
CSDL tạm, có chặn mạng. Claude phiên chính đối chiếu từng mục với `app.py`, viết test tái hiện rồi sửa.

## Kết luận

**Đạt sau khi sửa. Đã gắn `gd-6-ok`.**

- Tại `gd-6`: `pytest -q` → `133 passed`. Chạy chặn mạng → `133 passed`, `blocked network attempts: 0`, 11 cặp socket
  nội bộ của `asyncio` được cho qua. Subagent lấy lại commit đỏ `81878fd` bằng `git archive`: `2 failed, 131 passed`,
  khớp `gd-6.md`.
- 3 mục phải sửa, 5 mục nên sửa. Đã sửa cả 8 trong một commit, kèm 7 test mới. Phần lớn sửa ở `app.py`; mục 2 sửa ở
  `outreach/llm.py`.
- Sau khi sửa: `pytest -q` → `140 passed`. Chạy chặn mạng → `140 passed`, `blocked network attempts: 0`.
- `gd-6.md` không có câu nào sai sự thật.
- Mọi output ở đây chạy ở `X_MODE=fake` (conftest ép): `FakeGitHub`, `FakeXClient`, soạn bằng `template`.

Test mới hỏng trước khi sửa (`pytest -q tests/test_app_smoke.py tests/test_llm.py -k …`):
```
E   assert 0 == 1                                              # do_not_contact bị tab B ghi đè về 0
E   AssertionError: assert not ['**![px](https://example.invalid/t.png)** · [@alex_builder](https://x.com/alex_builder) …
E   KeyError: 'reply_note_1'
E   AssertionError: assert ['alex_builde...rah_robotics'] == ['alex_builde...rah_robotics']   # một người bị gọi 2 lần
E   AssertionError: assert (not ElementList(_list=[Success(), Success()]) or False)
E   KeyError: 'send_reject_1'
E   AssertionError: assert ['oops', {'so...gineer here'}] == [{'source_id'...gineer here'}]
7 failed, 2 passed, 16 deselected in 8.94s
```
Sau khi sửa (`pytest -q`):
```
140 passed in 12.72s
```
Chặn mạng (`pytest -q -p nonet6`; plugin thay `socket.socket.connect` và `httpx.HTTPTransport.handle_request`, chỉ
cho qua lời gọi từ `socket._fallback_socketpair`). Plugin vẫn chặn 127.0.0.1:11434 qua cả `socket` lẫn `httpx`:
```
blocked network attempts: 0 [] | in-process asyncio socketpairs allowed: 54
140 passed in 12.42s
sanity: network blocked: ('127.0.0.1', 11434)
sanity: network blocked: http://127.0.0.1:11434/api/tags
```

## Phải sửa — đã sửa

| # | Lỗi | Tình huống hỏng (subagent đã chạy) | Sửa | Test |
|---|---|---|---|---|
| 1 | Tab khác lặng lẽ tắt `Do not contact` | Hai tab A, B. A bật «không liên hệ» cho @alex. B bấm bất kỳ nút nào: công tắc ở B vẫn giữ giá trị cũ, khác CSDL, nên app ghi lại `False`. Output: `dnc after A toggles on: 1; after B reruns: 0` | Khoá của công tắc chứa giá trị trong CSDL (`dnc_<id>_<0/1>`): CSDL đổi thì công tắc được tạo lại theo CSDL | `test_do_not_contact_is_not_undone_by_another_tab` |
| 2 | Một bản nháp có bằng chứng lạ làm sập cả trang | Mô hình trả `evidence: ["oops", …]` (có thể xảy ra với Anthropic, vì công cụ không bật schema chặt). `ev.get` ném lỗi, tab Send và Track không hiện, không bấm được `I sent it`, không xử lý được tin `unknown` | Sửa ở gốc, trong `draft_for_campaign`: chỉ giữ phần tử là object | `test_draft_for_campaign_drops_evidence_items_that_are_not_objects` |
| 3 | Đường dẫn X hiện ở Review trước khi giữ chỗ (luật cứng 2) | Thẻ bản nháp hiện `[@alex_builder](https://x.com/alex_builder)` khi tin còn là `draft`: người dùng nhắn được mà không qua trần gửi, danh sách cho phép, «không liên hệ» | Review chỉ hiện `@handle` dạng chữ. Liên kết X chỉ còn ở `Open @… on X`, sau khi `claim` đã commit | `test_review_shows_untrusted_text_as_plain_text_and_no_x_link` |

Về mục 3, bảng hồ sơ ở tab Find **vẫn giữ** liên kết X, vì kế hoạch GĐ6 ghi rõ «liên kết X». Đây là quyết định của Claude,
chưa hỏi người dùng. Lý do: bảng đó dùng để xem người này là ai trước khi soạn tin. Luật cứng 2 nói về thứ tự trong lượt
gửi (`claim` commit rồi mới trả đường dẫn để gửi). Không giao diện nào chặn được việc người dùng tự gõ `x.com/<tên>`. Còn
thẻ Review nằm ngay cạnh tin nhắn soạn sẵn, nên dễ bấm nhầm ở đó nhất; vì vậy bỏ liên kết ở Review.

## Nên sửa — đã sửa luôn

| # | Lỗi | Tình huống hỏng (subagent đã chạy) | Sửa | Test |
|---|---|---|---|---|
| 4 | `Mark replied` bấm hai lần đánh dấu nhầm người | Sau lần bấm đầu, ô ghi chú vẫn giữ chữ cũ. Bấm lần nữa thì người kế tiếp bị đánh dấu đã trả lời, kèm ghi chú của người trước | Khoá ô ghi chú và nút theo từng tin (`reply_note_<id>`, `reply_<id>`) | `test_mark_replied_twice_does_not_mark_the_next_person` |
| 5 | `Draft next N` gọi lại hồ sơ hỏng ở mỗi vòng | Có hồ sơ soạn lỗi: 6 lần gọi mô hình thay vì 4. Với Anthropic mỗi lần là tiền, với Ollama mỗi lần tới 300 giây | Gọi `draft_for_campaign(limit=N)` một lần; bộ soạn được bọc để đẩy thanh tiến độ theo từng người | `test_draft_next_n_tries_each_person_once` |
| 6 | Ollama tắt mà vẫn hiện «Nobody left to draft» | Hiện cả lỗi lẫn câu thành công, gây hiểu sai | Chỉ hiện câu thành công khi không có lỗi | `test_drafting_error_shows_no_success_message` |
| 7 | Dữ liệu ngoài thành markdown | Tên GitHub `![px](https://example.invalid/t.png)` thành ảnh: trình duyệt tải URL lạ khi mở Review. `source_id` do mô hình sinh được ghép thẳng vào liên kết | Tên, handle, điểm hiện bằng `st.text`. Chỉ tạo liên kết khi `source_id` là `bio`, `location` hoặc `repo:<owner>/<name>` hợp lệ | `test_review_shows_untrusted_text_as_plain_text_and_no_x_link` |
| 8 | Tin đã duyệt không còn cách từ chối | `review.reject` cho phép `approved`, nhưng giao diện không có nút | Thêm nút `Reject` cho mỗi tin ở tab Send | `test_approved_message_can_be_rejected_in_send` |

Test cũ `test_manual_flow_find_to_handled` đổi theo khoá mới của mục 4 (`reply_note_<id>`, `reply_<id>`).

## Ghi nhận — chưa sửa

- **`recover_stuck` chỉ chạy một lần mỗi phiên trình duyệt** (subagent đã chạy). Tin kênh API kẹt `sending` phát sinh
  sau đó vẫn ở `sending`, không vào Needs attention, và vẫn tính vào trần. Chỉ ảnh hưởng kênh API, vốn chưa chạy thật.
  `XClient` có `timeout=30`, nên gọi hàm ở mỗi lần chạy lại là an toàn nếu sau này cần.
- **Lỗi 429 ở kênh API hiện `@alex_builder: approved`.** Khó hiểu, và mất giờ được gửi lại.
- **`SEND_MODE=live` với kênh API:** thanh bên ghi `Send mode: LIVE`, tab Send vẫn hiện nút cho người ngoài danh sách.
  Bấm thì bị chặn và báo lý do, nên vẫn an toàn.
- **Sửa một ký tự là qua được kiểm bằng chứng.** Đây là thiết kế của GĐ4: sửa nghĩa là người duyệt chịu trách nhiệm.
  Cảnh báo «quotes not found» vẫn hiện sau khi sửa.
- Chỉ đọc mã, chưa chạy: bấm hai lần `Create campaign` tạo chiến dịch trùng; tin `blocked` do bấm nhầm
  `Already in contact` không hoàn tác được; `st.error` hiện văn bản lỗi của X / GitHub dạng markdown.

## Đã kiểm, thấy đúng

- Hai phiên cùng bấm `Start`: chỉ giữ chỗ một lần, trần đếm 1, cú bấm thừa bị bỏ qua. Liên kết X chỉ hiện sau khi giữ chỗ.
- Bật «không liên hệ» trong cùng phiên: tab Send hiện `Can't send: marked do-not-contact`, không có nút `Start`.
- Kênh API ở chế độ giả lập: `Connect X account` → «Connected as @genaifund_test»; `Send via X API` → `sent`, kênh
  `api`; người ngoài danh sách bị chặn, tin vẫn `approved`; X không trả lời kịp → `unknown`, tab Track có giải thích
  và hai nút; `It was not sent` → `failed`, hiện ở Review (kèm lý do, nút Approve) và Track (nút `Mark handled`).
- Review: `Approve` bị từ chối hiện nguyên văn lý do; cảnh báo `draft_problems` tính lại theo nội dung vừa sửa; `Reject`
  đưa tin về `rejected`.
- Find: `GitHubRateLimited` hiện giờ được gọi lại theo giờ máy, không ngoại lệ.
- Streamlit «magic»: quét cây cú pháp chỉ còn hai docstring, không hiện ra màn hình.
- Luật cứng 3 (đọc mã): tin kênh tay `sending` và tin `unknown` chỉ đổi trạng thái qua `confirm_manual` /
  `resolve_unknown`. `recover_stuck` chỉ đụng kênh API. `mark_handled`, `set_text`, `reject` từ chối hai trạng thái này.
- Hợp đồng gọi hàm (đọc mã): chữ ký, giá trị trả về, ngoại lệ của mọi hàm `outreach/` mà `app.py` gọi đều khớp. Không có
  `unsafe_allow_html`.
- `data/fake.db` không bị đụng: mọi lần chạy trỏ `DB_PATH` sang thư mục tạm.
