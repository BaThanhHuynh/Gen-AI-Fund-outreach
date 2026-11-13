# Rà soát Giai đoạn 4 — Chấm điểm, soạn tin, kiểm bằng chứng

Ngày 2026-11-13 · Người rà: một subagent mới của Claude (không viết mã GĐ4), đọc `git diff gd-3-ok..gd-4` và mục
GĐ4 trong `docs/quy_trinh_trien_khai.md`. Claude phiên chính đối chiếu từng mục với mã rồi sửa.

## Kết luận

**Đạt sau khi sửa. Đã gắn `gd-4-ok`.**

- Tại `gd-4`: `pytest -q` trong `.venv` → `98 passed`. Chạy với plugin chặn mạng (`httpx.HTTPTransport.handle_request`
  và `socket.socket.connect` đều ném lỗi) → `98 passed`, `blocked network attempts: 0`.
- Có 2 mục phải sửa: một ở báo cáo (output dán không đúng), một ở mã (tin mẫu có thể trích repo lạc đề).
- Sau khi sửa: `pytest -q` → `102 passed`; chạy chặn mạng → `102 passed`, `blocked network attempts: 0`.

## Phải sửa — đã sửa

| # | Lỗi | Tình huống hỏng | Sửa | Commit |
|---|---|---|---|---|
| 1 | `gd-4.md` mục 2: output «test hỏng» không phải output thật | Báo cáo dán `1 failed, 67 passed, 3 errors`. Chạy lại commit `bebd313`: `pytest -q` ra `Interrupted: 3 errors during collection`; thêm `--continue-on-collection-errors` ra `1 failed, 72 passed, 3 errors` | Dán lại cả hai output thật kèm đúng lệnh | commit báo cáo |
| 2 | `template_draft` trích cả repo không khớp từ khoá | Repo khớp từ khoá không có mô tả, repo `dotfiles` mới đẩy mã có 80 sao → tin trích «My zsh and vim configuration files», `evidence_ok=1`, duyệt được không cần sửa | Chỉ lấy lý do «Repo … is about …» (repo khớp từ khoá); không có thì lùi về bio. Test `test_template_draft_quotes_only_keyword_repos` | `e80081d` |

## Nên sửa — đã sửa luôn (rẻ, chạm đúng chỗ dễ hỏng)

- **3.** Từ khoá bắt đầu hoặc kết thúc bằng ký hiệu (`c++`, `c#`, `.net`) không bao giờ khớp, vì `\b` cần một chữ cái
  ở một bên. Chiến dịch dùng từ khoá đó âm thầm cho điểm 0. Đổi `\b…\b` thành `(?<!\w)…(?!\w)`: từ khoá thường vẫn
  khớp y như cũ. Test `test_keyword_with_symbols_matches_whole_word`. Commit `57367e6`.
- **4.** Ollama hết 300 giây chờ thì chỉ bỏ qua hồ sơ đó. `limit` đếm bản nháp tạo được, không đếm lần thử, nên một
  mô hình chậm có thể làm cả lượt chờ 300 giây × mọi hồ sơ. Giờ hết giờ chờ ném `LLMDown` (dừng cả lượt) kèm lời
  khuyên dùng mô hình nhỏ hơn hoặc `LLM_PROVIDER=template`. Test `test_ollama_timeout_stops_the_batch`. Commit `e80081d`.
- **5.** `doctor` kiểm Ollama cả khi `X_MODE=fake`, dù chế độ fake luôn soạn bằng `template`. Với `.env.example` mặc
  định (`X_MODE=fake`, `LLM_PROVIDER=ollama`) trên máy không có Ollama, `doctor` báo FAIL cho thứ không dùng tới.
  Giờ chỉ kiểm khi `X_MODE=real`, giống bước kiểm GitHub. Test `test_doctor_skips_ollama_in_fake_mode`; test cũ
  `test_doctor_fails_when_ollama_model_missing` thêm `X_MODE=real`. Commit `d6b6b7a`.
- **6.** `gd-4.md` 4.3: thời gian soạn «0,02–0,03 ms» không có trong output dán; không nói `other_texts` là gì khi đếm
  cảnh báo. Đã chạy lại 4.3 sau khi sửa, dán thời gian từng lần soạn và ghi rõ `other_texts` = các bản nháp khác
  của cùng lượt.

Một test cũ phải đổi dữ liệu: `test_template_draft_passes_verification` dùng lý do `{"claim": "repo"}` — dạng
`score_fit` không bao giờ sinh ra. Đổi thành `"Repo agri is about robot"` (dạng thật). Kết quả mong đợi của test giữ nguyên.

## Ghi nhận — chưa sửa

- Địa điểm khớp theo ranh giới từ thay vì «chứa»: «Vietnamese living abroad» không được +10.
- Từ khoá chiến dịch trùng (`AI,ai`) bị tính hai lần.
- Gạch nối chỉ được chuẩn hoá ở tên repo và chủ đề; mô tả ghi «machine-learning» không khớp «machine learning».
- Từ khoá CJK trong đoạn chữ CJK liền không bao giờ khớp.
- Phân loại theo ranh giới từ bỏ sót số nhiều và «Ph.D.» («Founders», «researchers»). Vẫn tốt hơn regex thô của kế
  hoạch, vốn xếp «director» vào `founder` vì chứa «cto».
- `_cut` bỏ từ cuối khi ký tự thứ 121 là khoảng trắng (vẫn đúng kế hoạch). Cắt cứng 120 ký tự khi không có khoảng
  trắng có thể tách dấu kết hợp; rất hiếm.
- Ollama trả mã lỗi HTTP thì dừng cả lượt (đã ghi trong `gd-4.md`). Lỗi SDK Anthropic (khoá sai, hết lượt) ném thẳng
  và dừng lượt — giao diện GĐ6 phải bắt.
- `doctor`: `/api/tags` trả JSON không phải object thì `.get` ném `AttributeError`, không được bắt.
- `reject` một tin đã `rejected` ném `ValueError` (bấm hai lần). Trạng thái vẫn đúng.
- `draft_problems` không được gọi trong `draft_for_campaign` — đúng kế hoạch: cảnh báo hiện lúc xem (GĐ6).
- Tham số `limit` của `draft_for_campaign` chưa có test.
- Mặc định `LLM_PROVIDER` trong `config.py` / `.env.example` vẫn là `ollama` (câu hỏi mở, chưa có quyết định).

## Đã kiểm, thấy đúng

- **Điểm:** +20 mỗi từ khoá khớp ở bio (tối đa 40); +15 mỗi repo khớp qua tên, chủ đề hoặc mô tả (tối đa 45); +10 khi
  có repo đẩy mã trong 90 ngày tính đến `today`; +5 khi repo nhiều sao nhất có ≥ 50 sao; +10 khi địa điểm thuộc
  `SEA_LOCATIONS`; tổng tối đa 100. Không khớp từ khoá nào → 0.
- **Khớp từ khoá:** casefold, từ khoá nhiều từ chấp nhận mọi khoảng trắng, bỏ từ khoá rỗng, dùng `re.escape`, chữ
  Việt khớp đúng. Phân loại dùng bio + company, `founder` ưu tiên trước `researcher`.
- **`template_draft`:** đúng khuôn chữ của kế hoạch; mô tả rỗng / `None` bị bỏ qua; câu trích đã cắt vẫn là chuỗi
  con của nguồn nên qua `verify_evidence`; không có gì để trích → `LLMUnavailable("no quotable evidence")`.
- **`ollama_call`:** thân request có `model`, `messages`, `stream: false`, `think: false`, `format`, `temperature
  0.3`; timeout 300 giây; đọc `message.content`; không kết nối được → `LLMDown` với đúng thông điệp; JSON hỏng →
  `LLMUnavailable` (bỏ qua hồ sơ đó).
- **`anthropic_call`:** ép JSON bằng `tools` + `tool_choice`; ghi `llm_in` / `llm_out` qua `record_usage`; tên mô hình
  lấy từ `config.LLM_MODEL` (mặc định `claude-fable-5-2`).
- **`build_prompt`:** bọc `<profile>`, `<source id>`, `<repo id>`; đổi `<` thành `&lt;` trong văn bản không tin cậy,
  nên bio / tên repo / tên người không đóng được thẻ. Lời nhắc hệ thống có đủ luật và điều cấm.
- **`verify_evidence`:** chuẩn hoá NFC, casefold, gộp khoảng trắng; dữ liệu hỏng (không phải list, `{}`, giá trị
  `None`, chuỗi) trả `False`, không ném lỗi.
- **`draft_problems`:** độ dài, `http`, năm cụm tỏ ra quen biết, Jaccard ≥ 0,8, bỏ qua tin dưới 5 từ.
- **`draft_for_campaign`:** lọc `min_score`, `do_not_contact`, chưa có dòng `messages`; chèn `ON CONFLICT DO NOTHING`
  với `draft` và `evidence_ok`; `LLMUnavailable` bỏ qua một hồ sơ, `LLMDown` dừng và ném lại, bản nháp trước đó đã
  commit.
- **`review.py`:** `set_text`, `approve`, `reject` đổi trạng thái bằng một câu `UPDATE … WHERE id=? AND status IN (…)`
  và kiểm `rowcount`, nên không ghi đè tin đang `sending` / `sent`. Chuỗi lý do đúng nguyên văn.
- **`doctor`:** `GET /api/tags`; khớp tên đúng hoặc dạng `:latest`; dòng FAIL kèm `ollama pull …` hoặc
  `LLM_PROVIDER=template`.
- `fake_llm` đã xoá, không còn nơi nào import. Không thêm thư viện. Thông điệp tiếng Anh. Không in khoá.
- Báo cáo `gd-4.md` có đúng 5 mục; giải thích 98 thay vì 87 test là đúng (72 + 26); 4.3 ghi nhãn `X_MODE=real`,
  `LLM_PROVIDER=template`; đường Ollama / Anthropic chưa chạy thật nằm ở «Chưa kiểm được».
