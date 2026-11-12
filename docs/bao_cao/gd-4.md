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

Test hỏng trước khi viết mã (4.1, lúc đó có 67 test cũ):
```
FAILED tests/test_doctor.py::test_doctor_fails_when_ollama_model_missing - Ty...
ERROR tests/test_fit.py
ERROR tests/test_llm.py
ERROR tests/test_review.py
1 failed, 67 passed, 3 errors in 1.77s
```

Sau 4.2, `pytest -q`. Chạy cả với một plugin chặn mọi kết nối HTTP thật: kết quả như nhau.
```
98 passed in 1.37s
```

4.3: cụm từ `robotics`, `machine learning`, `max_people=10`. Từ khoá chiến dịch: `robotics,machine learning`.
`sender_context`: «I'm with GenAI Fund, an early-stage fund that backs AI and robotics builders in Southeast Asia.»
Output nguyên văn, trừ bản nháp: tên người, login và tên chủ repo đã thay bằng `<name>` / `<owner>`.
```
discover: ok {'new': 10, 'existing': 0, 'no_x_handle': 254, 'checked': 264}
discover time: 208.2s
prospects: 10 repos: 37
scored: 10
scores: [60, 40, 40, 40, 40, 30, 30, 30, 30, 30] (>= 40: 5)
categories: {'builder': 9, 'researcher': 1}
drafts: 5
attempts: 5 skipped (LLMUnavailable or empty): 0
evidence_ok: [1, 1, 1, 1, 1]
warnings per draft: [0, 0, 0, 0, 0]
```

Ba bản nháp đầu. Thời gian soạn mỗi tin bằng `template`: 0,02–0,03 ms.

| # | Điểm · loại | Bằng chứng (`source_id` → trích) | Cảnh báo |
|---|---|---|---|
| 1 | 60 · builder | `repo:<owner>/<name>` → "<name> is an integrated visualization and diagnosis tool for robotics, available in your browser or as a desktop app on" | không |
| 2 | 40 · builder | `repo:<owner>/AI_research_team` → "Multiple agents research the same topic, locate materials, verify sources, engage in critical discussion, and" | không |
| 3 | 40 · builder | `repo:<owner>/<name>` → "Infrastructure engineer. Notes, experiments and things I build." | không |

Nguyên văn tin 1:
> Hi <name>, I came across <name> on GitHub: "<name> is an integrated visualization and diagnosis tool for robotics,
> available in your browser or as a desktop app on". I'm with GenAI Fund, an early-stage fund that backs AI and
> robotics builders in Southeast Asia. What are you focusing on next?

Tin 2 và tin 3 cùng khuôn, chỉ khác tên repo và câu trích như trong bảng.

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
  giảm dần, và `template_draft` lấy repo đầu tiên có mô tả. Giới hạn đã biết, ghi bằng chú thích `ponytail:` trong
  mã: nếu không repo khớp từ khoá nào có mô tả, mẫu có thể trích repo «mới đẩy mã» hoặc «nhiều sao» trước khi lùi
  về bio.
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
- Thời gian tìm người lần này 208 giây, lần trước 268 giây (cùng bộ đếm). Có thể nhờ dùng lại kết nối HTTP sau rà
  soát GĐ3, nhưng mạng mỗi lần mỗi khác, nên chưa kết luận được.

## 5. Câu hỏi cho người dùng
- **Câu trích cắt ở 120 ký tự nên đứt giữa câu** (tin 1, 2: «…as a desktop app on»). Có muốn:
  - ưu tiên cắt ở cuối câu nếu có dấu chấm trong 120 ký tự, hoặc thêm «…» sau dấu ngoặc kép?
  - hay giữ đúng kế hoạch, để người sửa khi duyệt?
- **Chỉ 5/10 hồ sơ đạt `MIN_SCORE=40`.** Nhiều người chỉ khớp một từ khoá trong bio (20 điểm) cộng địa điểm (10 điểm).
  Giữ ngưỡng 40 hay hạ?
- **Mặc định `LLM_PROVIDER` trong `config.py` và `.env.example` vẫn là `ollama`.** Đổi sang `template` không? Việc
  này nằm ngoài danh sách tệp của GĐ4 nên chưa làm.
