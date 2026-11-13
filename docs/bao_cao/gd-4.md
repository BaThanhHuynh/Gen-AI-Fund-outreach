# Báo cáo Giai đoạn 4 — Chấm điểm, soạn tin, kiểm bằng chứng

Người làm: Claude (từ GĐ3 Claude tự làm hết, người dùng quyết ngày 13/11/2026).

## 1. Đã làm
- 4.1: viết test trước: `tests/test_fit.py` (7), `tests/test_llm.py` (14), `tests/test_review.py` (4), một test mới
  trong `tests/test_doctor.py`. Chạy thấy hỏng (thiếu module), commit `bebd313`.
- 4.2: viết `outreach/fit.py`, `outreach/llm.py`, `outreach/review.py`. `doctor` thêm bước kiểm Ollama (chỉ chạy khi
  `LLM_PROVIDER=ollama`). Xoá `fake_llm` khỏi `fake_x.py`. Commit `822bbb1`.
- Trước khi viết `ollama_call` đã mở tài liệu hiện hành `docs.ollama.com/api/chat` và `/api/tags` (13/11/2026):
  - `format` nhận một JSON schema;
  - `think: false` tắt suy nghĩ;
  - câu trả lời nằm ở `message.content`;
  - `/api/tags` trả `models[].name` / `models[].model`.

  Khớp với kế hoạch.
- 4.3: chạy thật, 0 USD, `X_MODE=real`, `LLM_PROVIDER=template`, CSDL tạm trong scratchpad (đã xoá sau khi chạy).
  Không gửi gì lên X.

## 2. Kết quả kiểm

Test hỏng trước khi viết mã (4.1). Output dưới đây chạy lại ở lần rà soát, trên bản xuất của commit `bebd313`
(bản cũ của báo cáo dán `1 failed, 67 passed, 3 errors` — không phải output thật; xem `gd-4-ra-soat.md` mục 1).

`pytest -q`:
```
ERROR tests/test_fit.py
ERROR tests/test_llm.py
ERROR tests/test_review.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!
3 errors in 1.02s
```

`pytest -q --continue-on-collection-errors`:
```
FAILED tests/test_doctor.py::test_doctor_fails_when_ollama_model_missing - Ty...
ERROR tests/test_fit.py
ERROR tests/test_llm.py
ERROR tests/test_review.py
1 failed, 72 passed, 3 errors in 2.31s
```

Sau 4.2, `pytest -q`. Chạy cả với một plugin chặn mọi kết nối HTTP thật: kết quả như nhau.
```
98 passed in 1.37s
```

Sau rà soát (`gd-4-ra-soat.md`), `pytest -q`, rồi `pytest -q -p nonet` (plugin chặn `httpx.HTTPTransport.handle_request`
và `socket.socket.connect`):
```
102 passed in 1.88s
```
```
[nonet] blocked network attempts: 0 []
102 passed in 1.81s
```

4.3, chạy lại sau rà soát (`X_MODE=real`, `LLM_PROVIDER=template`, CSDL tạm trong scratchpad, đã xoá sau khi chạy,
không gửi gì lên X). Cụm từ `robotics`, `machine learning`, `max_people=10`. Từ khoá chiến dịch:
`robotics,machine learning`. `sender_context`: «I'm with GenAI Fund, an early-stage fund that backs AI and robotics
builders in Southeast Asia.» `other_texts` khi tính cảnh báo = 4 bản nháp còn lại của cùng lượt. Output nguyên văn
(phần bản nháp: tên người, login và tên repo trùng tên người đã thay bằng `<name>` / `<owner>`):
```
discover: {'new': 10, 'existing': 0, 'no_x_handle': 254, 'checked': 264}
discover time: 183.8s
prospects: 10 repos: 37
scored: 10
scores: [60, 40, 40, 40, 40, 30, 30, 30, 30, 30] (>= 40: 5)
drafts: 5 attempts: 5
draft time per attempt (ms): [0.024, 0.156, 0.021, 0.088, 0.026]
evidence_ok: [1, 1, 1, 1, 1]
warnings per draft (other_texts = the other drafts of this run): [[], [], [], [], []]
```

Thời gian soạn mỗi tin bằng `template`: 0,021–0,156 ms (dòng `draft time per attempt` ở trên).

| # | Điểm · loại | Lý do chấm | Bằng chứng (`source_id` → trích) | Cảnh báo |
|---|---|---|---|---|
| 1 | 60 · builder | bio, repo khớp, mới đẩy mã, 116 sao, Singapore | `repo:<owner>/<name>` → "<name> is an integrated visualization and diagnosis tool for robotics, available in your browser or as a desktop app on" | không |
| 2 | 40 · builder | bio, mới đẩy mã (`AI_research_team`), Viet Nam | `bio` → "I have a passion for building robots and am currently in the process of doing so." | không |
| 3 | 40 · builder | bio, mới đẩy mã, Vietnam | `bio` → "Functional programmer focused on robotics control." | không |
| 4 | 40 · builder | bio, mới đẩy mã, Singapore | `bio` → "Postdoctoral Fellow at NTU." | không |
| 5 | 40 · researcher | bio, mới đẩy mã, Singapore | `bio` → "Researcher @ AutoLife Robotics ~" | không |

Nguyên văn tin 1:
> Hi <name>, I came across <name> on GitHub: "<name> is an integrated visualization and diagnosis tool for robotics,
> available in your browser or as a desktop app on". I'm with GenAI Fund, an early-stage fund that backs AI and
> robotics builders in Southeast Asia. What are you focusing on next?

Nguyên văn tin 2:
> Hi <name>, I came across your GitHub profile: "I have a passion for building robots and am currently in the process
> of doing so.". I'm with GenAI Fund, an early-stage fund that backs AI and robotics builders in Southeast Asia. What
> are you focusing on next?

Tin 3–5 cùng khuôn với tin 2, chỉ khác câu trích như trong bảng.

So với lần chạy 4.3 đầu (trước rà soát): tin 2 từng trích mô tả repo `AI_research_team`, tin 3 từng trích mô tả một
repo hồ sơ. Cả hai repo chỉ được nêu vì «mới đẩy mã», không khớp từ khoá — đúng lỗi #2 của rà soát. Giờ cả hai
lùi về câu trong bio.

## 3. Lệch so với kế hoạch
- **Số test: 98, kế hoạch ghi 87.** Kế hoạch tính từ 63 test sau GĐ3. Thực tế sau GĐ3 và rà soát có 72 test.
  GĐ4 thêm 26 thay vì 24:
  - `test_score_campaign_writes_scores`: kiểm hàm ghi điểm vào CSDL;
  - `test_draft_for_campaign_skips_one_but_stops_when_provider_down`: kiểm luật «một hồ sơ lỗi thì bỏ qua, Ollama
    không chạy thì dừng cả lượt».
- **Thêm `LLMDown(LLMUnavailable)`.** Lớp lỗi này tách hai trường hợp:
  - «bỏ qua hồ sơ này»: `LLMUnavailable`;
  - «dừng cả lượt»: `LLMDown`, ném khi Ollama không kết nối được hoặc trả mã lỗi HTTP.

  Kế hoạch đòi cả hai hành vi nhưng chỉ có một lớp lỗi.
- **`fit.repos_of(conn, prospect_id)`** là hàm dùng chung. Nó đọc repo của một hồ sơ (chủ đề đổi từ JSON sang
  list); cả `score_campaign` và `draft_for_campaign` đều dùng.
- **Khớp từ khoá.** Vẫn khớp theo ranh giới từ như kế hoạch. Thêm ba điểm:
  - giữa các từ của một từ khoá nhiều từ chấp nhận mọi khoảng trắng;
  - từ khoá rỗng bị bỏ qua (nếu không, nó khớp mọi thứ);
  - trong tên repo và chủ đề, `-` và `_` được đổi thành khoảng trắng, nên `machine-learning` khớp
    `machine learning`.
- **Phân loại cũng khớp theo ranh giới từ.** Nhờ vậy `cto` không khớp nhầm trong `director`.
- **«Repo điểm cao nhất» được hiểu là repo nhiều sao nhất trong số repo khớp từ khoá.** Lý do repo được xếp theo sao
  giảm dần, và `template_draft` lấy repo khớp từ khoá đầu tiên có mô tả; không có thì lùi về bio. (Bản đầu của GĐ4
  còn trích cả repo chỉ được nêu vì «mới đẩy mã» / «nhiều sao» — đã sửa sau rà soát, commit `e80081d`.)
- **Sau rà soát:** hết 300 giây chờ Ollama giờ là `LLMDown` (dừng cả lượt); từ khoá có ký hiệu (`c++`, `.net`) khớp
  được; `doctor` bỏ bước Ollama khi `X_MODE=fake`. Chi tiết và commit: `gd-4-ra-soat.md`.
- **`build_prompt` chỉ đổi `<` thành `&lt;` trong văn bản không tin cậy.** Bio không đóng được thẻ `</profile>`.
  Ngoài `<`, không đổi gì khác, nên câu mô hình trích nguyên văn vẫn khớp nguồn.
- **`verify_evidence` chuẩn hoá Unicode NFC** trước khi so. Cùng một chữ Việt có thể được mã hoá theo hai cách.
- **`review`:**
  - đổi trạng thái bằng `UPDATE … WHERE status IN (…)`, nên bấm hai lần cũng an toàn;
  - `set_text` từ chối văn bản rỗng;
  - `reject` được phép từ `draft`, `approved`, `failed`; trạng thái khác thì ném `ValueError`.
- **`run_doctor` nhận thêm `ollama_transport`** để test không ra mạng.
- **4.3 dùng hồ sơ thật tìm lại, không phải hồ sơ của 3.3.** CSDL tạm của 3.3 đã bị xoá. Tìm lại với cùng tham số
  cho ra cùng bộ đếm.
- **4.3 không dùng mô hình.** `LLM_PROVIDER` chốt ở GĐ0 là `template`.

## 4. Chưa kiểm được
- `ollama_call` chưa chạy với Ollama thật, chỉ kiểm bằng `MockTransport`. Bước `doctor` kiểm Ollama cũng vậy.
- `anthropic_call` chưa gọi API thật (tốn tiền, trái ràng buộc 0 USD). Mới kiểm bằng client giả: lời gọi ép `tools` +
  `tool_choice`, sổ ghi đúng số token. Lời gọi viết theo hiểu biết về Messages API, chưa mở lại tài liệu Anthropic
  hiện hành.
- Chất lượng tin do mô hình soạn: chưa có, vì chỉ dùng `template`.
- Thời gian tìm người: 268 giây (3.3), 208 giây (4.3 lần 1), 184 giây (4.3 sau rà soát), cùng bộ đếm. Có thể
  nhờ dùng lại kết nối HTTP sau rà soát GĐ3, nhưng mạng mỗi lần mỗi khác, nên chưa kết luận được.

## 5. Câu hỏi cho người dùng
- **Câu trích cắt ở 120 ký tự nên đứt giữa câu** (tin 1: «…as a desktop app on»). Có muốn:
  - ưu tiên cắt ở cuối câu nếu có dấu chấm trong 120 ký tự, hoặc thêm «…» sau dấu ngoặc kép?
  - hay giữ đúng kế hoạch, để người sửa khi duyệt?
- **Chỉ 5/10 hồ sơ đạt `MIN_SCORE=40`.** Nhiều người chỉ khớp một từ khoá trong bio (20 điểm) cộng địa điểm (10 điểm).
  Giữ ngưỡng 40 hay hạ?
- **Mặc định `LLM_PROVIDER` trong `config.py` và `.env.example` vẫn là `ollama`.** Đổi sang `template` không? Việc
  này nằm ngoài danh sách tệp của GĐ4 nên chưa làm.
- **Mẫu lấy câu bio đầu tiên đủ dài, không phải câu có từ khoá** (tin 4: «Postdoctoral Fellow at NTU.» thay vì câu
  nói về robotics). Đúng kế hoạch («một câu trong bio»). Có muốn ưu tiên câu chứa từ khoá không?
