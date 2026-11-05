"""Render docs/bao-cao-danh-gia.md (+ .docx) from reports/metrics.json. Numbers are never typed by hand.

Usage: python scripts/gen_report.py
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
M = json.loads((ROOT / "reports" / "metrics.json").read_text(encoding="utf-8"))
OUT_MD = ROOT / "docs" / "bao-cao-danh-gia.md"
OUT_DOCX = ROOT / "docs" / "bao-cao-danh-gia.docx"

NAMES = {"random": "Ngẫu nhiên", "tfidf_only": "Chỉ TF-IDF", "skill_cov_only": "Chỉ độ phủ kỹ năng",
         "heuristic-v1": "heuristic-v1 (6 đặc trưng, trọng số cố định)", "lr-v1": "lr-v1 (hồi quy logistic)"}
R = M["ranking"]


def cell(d):
    return f"{d['mean']:.3f} [{d['ci95'][0]:.3f}; {d['ci95'][1]:.3f}]"


def ranking_table():
    rows = ["| Phương pháp | P@5 | Recall@10 | MRR | nDCG@10 |", "|---|---|---|---|---|"]
    for k, name in NAMES.items():
        rows.append(f"| {name} | " + " | ".join(cell(R[k][m]) for m in ("P@5", "Recall@10", "MRR", "nDCG@10")) + " |")
    return "\n".join(rows)


def overlap(a, b):
    return not (a["ci95"][1] < b["ci95"][0] or b["ci95"][1] < a["ci95"][0])


def lr_vs_heuristic():
    d = {m: (R["lr-v1"][m], R["heuristic-v1"][m]) for m in ("P@5", "MRR", "nDCG@10")}
    sig = [m for m, (a, b) in d.items() if a["mean"] > b["mean"] and not overlap(a, b)]
    if sig:
        return f"lr-v1 cao hơn heuristic-v1 có ý nghĩa (khoảng tin cậy 95% không giao nhau) ở: {', '.join(sig)}."
    return ("lr-v1 nhỉnh hơn heuristic-v1 về giá trị trung bình nhưng các khoảng tin cậy 95% chồng lên nhau, "
            "nên chưa thể kết luận chắc chắn mô hình học tốt hơn trọng số cố định.")


def band_rows():
    b = M["outcome_by_score_band_simulated"]
    order = ["<0.55", "0.55-0.75", ">=0.75"]
    return "\n".join(f"| {k} | {b[k]['n']} | {b[k]['interview_rate']:.1%} | {b[k]['offer_rate']:.1%} |" for k in order if k in b)


def latency_rows():
    return "\n".join(f"| {k} | {v['p50_ms']} | {v['p95_ms']} |" for k, v in M["latency"].items())


def errors_md():
    out = []
    for i, e in enumerate(M["error_examples"], 1):
        out.append(f"**Ví dụ {i}.** Ứng viên sinh từ tin *{e['source_job']}* với kỹ năng {', '.join(e['candidate_skills'])}. "
                   f"Mô hình xếp hạng 1 tin *{e['top1_job']}* với điểm {e['top1_score']:.2f} (khớp: {', '.join(e['matched']) or '-'}). "
                   f"Tin này không thuộc tập liên quan vì {e['why_wrong']}.")
    return "\n\n".join(out)


def human_stats():
    """Within-slot agreement and human-rated precision of the model's top pick (None if no labels)."""
    import csv
    from scipy.stats import spearmanr
    try:
        h = {r["pair_id"]: float(r["human_score_1_to_5"]) for r in csv.DictReader(open(ROOT / "reports" / "label_me.csv", encoding="utf-8-sig")) if r["human_score_1_to_5"].strip()}
        k = {r["pair_id"]: (float(r["model_score"]), r["slot"]) for r in csv.DictReader(open(ROOT / "reports" / "label_me_key.csv", encoding="utf-8"))}
    except (OSError, ValueError):
        return None
    top = [p for p in h if p in k and k[p][1] == "top"]
    mid = [p for p in h if p in k and k[p][1] == "mid"]
    if len(top) < 5 or len(mid) < 5:
        return None
    rt = spearmanr([h[p] for p in top], [k[p][0] for p in top])
    return {"n_top": len(top), "top_ge4": sum(h[p] >= 4 for p in top) / len(top), "rho_top": float(rt[0]), "p_top": float(rt[1]),
            "mean_top": sum(h[p] for p in top) / len(top), "mean_mid": sum(h[p] for p in mid) / len(mid)}


def human_md():
    h = M["human_labels"]
    if h["status"] == "validated":
        hs = human_stats()
        detail = ""
        if hs:
            detail = (f"\n\nChi tiết: người chấm cho các cặp mô hình xếp cao nhất trung bình **{hs['mean_top']:.1f}/5**, các cặp ở mức giữa danh sách **{hs['mean_mid']:.1f}/5**. "
                      f"Trong {hs['n_top']} cặp mô hình xếp hạng 1, **{hs['top_ge4']:.0%}** được người chấm ≥ 4 điểm (đây là con số chuẩn xác theo người, so với mục tiêu 85%). "
                      f"Riêng trong nhóm xếp cao, Spearman = {hs['rho_top']:.2f} (p = {hs['p_top']:.3f}).\n\n"
                      "**Lưu ý khi diễn giải:** (1) chỉ 1 người chấm với 20 cặp, nên khoảng bất định lớn; (2) bộ cặp gồm một nửa xếp cao và một nửa xếp giữa, "
                      "nên Spearman tổng thể được nâng lên nhờ phân biệt hai nhóm dễ; mức đồng thuận trong nhóm xếp cao (số trên) mới phản ánh khả năng chọn đúng tin tốt nhất; "
                      "(3) các cặp lệch lớn thường là tin khác ngành vẫn được điểm cao (ví dụ kho/logistics với ứng viên xây dựng) hoặc tin cấp quản lý bị chấm thấp dù người chấm thấy phù hợp.")
        extra = (f" Độ đồng thuận giữa các người chấm (Spearman trung bình từng cặp): {h['inter_rater_spearman_mean']}."
                 if "inter_rater_spearman_mean" in h else "")
        return (f"{h['n_raters']} người chấm, {h['n_labeled']} cặp (điểm trung bình các người chấm, thang 1-5). "
                f"Hệ số Spearman giữa điểm người và điểm mô hình là **{h['spearman_rho']}** (p = {h['p_value']}).{extra} "
                "Quy ước đọc: ≥ 0,6 khá tốt; 0,3-0,6 trung bình; dưới 0,3 yếu (xem `docs/huong-dan-cham-nhan.md`)." + detail)
    return ("**Chưa kiểm chứng bằng người.** File `reports/label_me.csv` có 20 cặp (ứng viên, tin) chờ chấm 1-5; "
            f"hiện có {h.get('n_labeled', 0)} dòng đã điền (hướng dẫn: `docs/huong-dan-cham-nhan.md`). Mọi kết quả xếp hạng ở trên chỉ dựa trên nhãn tổng hợp.")


B = json.loads((ROOT / "reports" / "metrics_before_level_fit.json").read_text(encoding="utf-8"))["ranking"]


def before_after():
    rows = ["| Mô hình | Chỉ số | Trước (6 đặc trưng) | Sau (7 đặc trưng, có level_fit) |", "|---|---|---|---|"]
    for k in ("heuristic-v1", "lr-v1"):
        for m in ("P@5", "MRR", "nDCG@10"):
            rows.append(f"| {k} | {m} | {B[k][m]['mean']:.3f} | {R[k][m]['mean']:.3f} |")
    return chr(10).join(rows)


def error_common():
    n_cat = sum("khác ngành" in e["why_wrong"] for e in M["error_examples"])
    n_lvl = sum("cấp bậc" in e["why_wrong"] for e in M["error_examples"])
    msg = f"Trong {len(M['error_examples'])} ví dụ: {n_cat} lỗi khác ngành, {n_lvl} lỗi khác cấp bậc. "
    if n_cat:
        msg += ("Lỗi khác ngành xảy ra khi ứng viên có kỹ năng dùng chung nhiều ngành (Photoshop, Revit, Tin học văn phòng...) "
                "và nhãn ngành của VietJobs thô; mô hình chưa có đặc trưng khớp ngành giữa `candidate.major` và `category` của tin.")
    return msg


def _ratio():
    b = M["outcome_by_score_band_simulated"]
    hi, lo = b.get(">=0.75"), b.get("<0.55")
    if hi and lo and lo["interview_rate"]:
        return f"{hi['interview_rate'] / lo['interview_rate']:.1f} lần (qua phỏng vấn, điểm ≥ 0,75 so với < 0,55)"
    return "không tính được"


S, A, SAL = M["setup"], M["classification_auc_test"], M["salary_model"]
SENS = M["sensitivity_lr"]
COEF = M["lr_coefficients"]
rf, bl = SAL["random_forest"], SAL["baseline_median"]
RATIO = _ratio()
_hs = human_stats()
HUMAN_P = (f"{_hs['top_ge4']:.0%} số tin xếp hạng 1 được người chấm ≥ 4 điểm (n = {_hs['n_top']}, 1 người chấm) - vẫn chưa đạt 85%" if _hs else "chưa có nhãn người")

DOC = f"""# Báo cáo đánh giá hiệu quả gợi ý

*Sinh tự động bởi `scripts/gen_report.py` từ `reports/metrics.json` ngày {date.today().isoformat()}. Số liệu không gõ tay.*

## 1. Phương pháp

**Matching Score** là điểm 0-1 cho mỗi cặp (ứng viên, tin), tính từ 7 đặc trưng: độ phủ kỹ năng có trọng số (`skill_cov`),
độ tương đồng văn bản TF-IDF (từ 1-2 gram và ký tự 3-5 gram), mức đáp ứng kinh nghiệm, học vấn, địa điểm, lương mong muốn và
mức khớp cấp bậc hai chiều (`level_fit`, phạt cả ứng viên thiếu lẫn thừa cấp).
Hai bộ chấm điểm được so sánh: `heuristic-v1` (tổng có trọng số cố định) và `lr-v1` (hồi quy logistic học từ nhãn yếu).
Mô hình mặc định đang dùng: **{S['default_model']}**.

**Nhãn yếu để huấn luyện lr-v1.** Mẫu dương là ứng viên giả lập lấy 50-80% kỹ năng của một tin, thêm 1-3 kỹ năng nhiễu,
kinh nghiệm lệch ±1 năm. Mẫu âm khó là tin cùng ngành nhưng khác cấp bậc hoặc trùng dưới 30% kỹ năng; mẫu âm dễ là tin khác ngành.
Để tránh học vẹt, **chia train/test theo ngành**: mô hình không thấy 4 ngành kiểm tra ({', '.join(S['test_categories'])}).

**Bài toán xếp hạng để đánh giá.** Với {S['n_candidates']} ứng viên kiểm tra, xếp hạng {S['pool_size']} tin của các ngành giữ lại.
Một tin được coi là liên quan nếu {S['relevance']}; trung bình mỗi ứng viên có {S['mean_relevant']} tin liên quan.
Mỗi chỉ số kèm khoảng tin cậy 95% bằng bootstrap 1000 lần trên ứng viên (seed {S['seed']}).

## 2. Dữ liệu: phần thật và phần mô phỏng

| Thành phần | Nguồn | Thật hay mô phỏng |
|---|---|---|
| Tên việc, mô tả, yêu cầu, kỹ năng kỹ thuật, mức lương, địa điểm, kinh nghiệm | VietJobs (HuggingFace `dinhieufam/VietJobs`), mẫu ≤ 5000 dòng, giữ tin có ≥ 2 kỹ năng | **Thật** |
| Ngày đăng tin (`posted_at`) | Rải đều 12 tháng, seed 42 (VietJobs không có cột ngày) | **Mô phỏng** |
| Công ty | Sinh theo ngành (VietJobs không có cột công ty) | **Mô phỏng** |
| Ứng viên, kỹ năng ứng viên | Lấy mẫu theo phân bố kỹ năng của tin cùng ngành | **Mô phỏng** |
| Đơn ứng tuyển và kết quả qua vòng | Xác suất sigmoid theo Matching Score, seed 42 | **Mô phỏng** |

Hệ quả: các biểu đồ xu hướng theo thời gian và mọi chỉ số tuyển dụng (funnel, tỷ lệ qua vòng) **không phản ánh thị trường thật**;
chúng chứng minh hệ thống vận hành đúng, không chứng minh hiệu quả thực tế. Các chart liên quan đều ghi "(mô phỏng)".

## 3. Kết quả

### 3.1 Phân loại cặp (AUC trên ngành giữ lại)

| Mô hình | AUC |
|---|---|
| skill_cov đơn lẻ | {A['skill_cov']} |
| heuristic-v1 | {A['heuristic-v1']} |
| lr-v1 | {A['lr-v1']} |

### 3.2 Xếp hạng (trung bình [khoảng tin cậy 95%])

{ranking_table()}

**Nhận xét.** Cả hai bộ chấm điểm vượt xa ngẫu nhiên và vượt xa từng đặc trưng đơn lẻ, cho thấy việc kết hợp kỹ năng với
kinh nghiệm, học vấn, địa điểm có ích. TF-IDF đơn lẻ yếu hơn độ phủ kỹ năng vì văn bản ứng viên chỉ gồm danh sách kỹ năng. {lr_vs_heuristic()}
Giá trị tuyệt đối còn thấp (P@5 khoảng {R['lr-v1']['P@5']['mean']:.2f}) vì tập liên quan định nghĩa chặt (cùng cấp bậc, kinh nghiệm sát,
kỹ năng chồng lấn ≥ 40%) trong khi nhiều tin cùng ngành gần như tương đương với ứng viên.

Hệ số lr-v1 (đặc trưng đã chuẩn hóa 0-1): {', '.join(f'{k} = {v}' for k, v in COEF.items())}. Hệ số `edu_fit` lớn phản ánh
cách sinh nhãn (mẫu dương luôn đủ học vấn), không nên diễn giải như tầm quan trọng trong thực tế.

**Sửa lỗi cấp bậc (trước/sau).** Lần đánh giá đầu cho thấy mô hình gán điểm cao cho tin khác cấp bậc vì `exp_fit` chỉ phạt một phía.
Mình thêm đặc trưng `level_fit` rồi huấn luyện và đánh giá lại với cùng seed:

{before_after()}

Cảnh báo công bằng: tập "liên quan" của bài đánh giá có điều kiện *cùng cấp bậc*, nên đặc trưng mới được hưởng lợi một phần do cách đặt nhãn.
Cải thiện này chưa phải bằng chứng trên dữ liệu thật.

### 3.3 Độ nhạy của điểm

Thêm 1 kỹ năng còn thiếu: điểm tăng trung bình {SENS['add_required_skill']['mean_delta']:+.3f}, không giảm ở {SENS['add_required_skill']['pct_non_decreasing']:.0%} trường hợp (n = {SENS['add_required_skill']['n']}).
Bớt 1 kỹ năng đã khớp: điểm đổi trung bình {SENS['remove_matched_skill']['mean_delta']:+.3f}, không tăng ở {SENS['remove_matched_skill']['pct_non_increasing']:.0%} trường hợp (n = {SENS['remove_matched_skill']['n']}).
Điểm đơn điệu theo kỹ năng, đúng kỳ vọng.

### 3.4 Độ trễ API (100 request, gọi trong tiến trình, kể cả truy vấn Postgres)

| Endpoint | p50 (ms) | p95 (ms) |
|---|---|---|
{latency_rows()}

### 3.5 Mô hình ước lượng lương

Tập kiểm tra {SAL['n_test']} tin (chia theo hash `job_key`), đơn vị triệu VND/tháng.

| Mô hình | MAE | MAPE |
|---|---|---|
| Trung vị theo (ngành, cấp bậc) | {bl['mae']} | {bl['mape']:.1%} |
| RandomForest | {rf['mae']} | {rf['mape']:.1%} |

{'RandomForest tốt hơn baseline về MAE nên được dùng làm ước lượng chính.' if SAL['use_model'] else 'RandomForest **không** tốt hơn baseline về MAE, nên API trả trung vị phân khúc làm ước lượng chính và chỉ kèm dự đoán RandomForest để tham khảo.'}
Lương trong VietJobs nhiễu và nhiều tin không công khai lương, nên sai số quanh {bl['mape']:.0%} là hợp lý.

### 3.6 Tỷ lệ qua vòng theo nhóm điểm khớp (mô phỏng)

| Nhóm điểm | Số đơn | Qua phỏng vấn | Nhận offer |
|---|---|---|---|
{band_rows()}

**Lưu ý quan trọng:** kết quả này là **vòng lặp tự xác nhận**: xác suất qua vòng trong dữ liệu mô phỏng được sinh từ chính Matching Score,
nên nhóm điểm cao đương nhiên qua vòng nhiều hơn. Bảng chỉ kiểm tra pipeline (điểm -> đơn -> funnel -> chart) chạy thông, không phải bằng chứng hiệu quả tuyển dụng thật.

### 3.7 Kiểm chứng bằng người

{human_md()}

## 4. Đối chiếu 4 chỉ số mục tiêu (slide 10)

| Chỉ số mục tiêu | Mục tiêu | Đo được | Kết luận |
|---|---|---|---|
| Độ chuẩn xác gợi ý | 85% | P@5 = {R['lr-v1']['P@5']['mean']:.1%} (nhãn tổng hợp, tập liên quan định nghĩa chặt) | **Chưa đạt** theo nhãn tổng hợp; theo nhãn người: {HUMAN_P} |
| Sai số dự báo lương | ±10% | MAPE tốt nhất = {min(rf['mape'], bl['mape']):.1%} (MAE {min(rf['mae'], bl['mae'])} triệu) | **Chưa đạt**; lương trong VietJobs nhiễu và là dải rộng |
| Tỷ lệ qua vòng lọc khi điểm cao | 3,2 lần | {RATIO} | Số này sinh từ dữ liệu **mô phỏng tự xác nhận** (mục 3.6), **không** dùng làm bằng chứng đạt |
| Thời gian phản hồi | dưới 5 giây | p95 gợi ý = {M['latency']['GET /recommendations?k=20']['p95_ms']} ms | **Đạt** |

Kết luận trung thực: chỉ chỉ số thời gian phản hồi được chứng minh. Hai chỉ số chất lượng (chuẩn xác, sai số lương) đã đo thật nhưng **chưa đạt** mục tiêu;
chỉ số tỷ lệ qua vòng không đo được trên dữ liệu thật vì không có đơn ứng tuyển thật.

Về các nhóm yêu cầu chức năng của đề bài: Matching Score có giải thích; phân tích CV (parser, CV health, gợi ý sửa CV bằng Gemini có fallback);
2 dashboard Superset (15 chart, đều trả dữ liệu) và KPI nhà tuyển dụng lọc theo công ty; tìm kiếm, lọc, gợi ý top-K và xếp hạng ứng viên. Các chức năng này đều chạy được.

## 5. Phân tích lỗi: 3 ví dụ mô hình sai

{errors_md()}

{error_common()}

## 6. Hạn chế

- Nhãn huấn luyện và đánh giá đều tổng hợp; chưa có nhãn người (xem 3.7). Con số xếp hạng có thể lạc quan so với dữ liệu thật.
- Dữ liệu ứng viên, đơn ứng tuyển, công ty, ngày đăng là mô phỏng; kết quả BI về thời gian và funnel chỉ có giá trị minh họa.
- Văn bản ứng viên chỉ gồm tên kỹ năng và ngành, chưa dùng toàn văn CV, nên đặc trưng TF-IDF yếu.
- Chưa có đặc trưng khớp ngành (ứng viên so với tin); đã thêm `level_fit` nhưng đánh giá cấp bậc dùng nhãn tổng hợp (xem mục 3.2).
- Từ vựng kỹ năng gồm 140 mục chuẩn hóa từ VietJobs, nhiều mục là kỹ năng mềm; thiếu bao phủ cho kỹ năng kỹ thuật hiếm.
- Gemini chỉ dùng cho gợi ý sửa CV; chất lượng phụ thuộc quota và model miễn phí, luôn có fallback mẫu.

## 7. Hướng phát triển

Embedding đa ngôn ngữ và pgvector; đặc trưng khớp ngành (`field_fit`); skill graph; thu nhãn thật từ nhà tuyển dụng (nhấp, mời phỏng vấn) để huấn luyện lại;
quét ATS và lập lịch ETL; cookie httpOnly, audit log; nhúng Superset bằng guest token; E2E tự động và load test song song.
"""


def md_to_docx(md: str, path: Path):
    from docx import Document
    doc = Document()
    lines = md.split("\n")
    i = 0
    strip = lambda t: re.sub(r"[*`]", "", t)  # noqa: E731
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"-+", c) for c in cells):
                    rows.append(cells)
                i += 1
            t = doc.add_table(rows=len(rows), cols=len(rows[0]))
            t.style = "Table Grid"
            for r, row in enumerate(rows):
                for c, txt in enumerate(row[:len(rows[0])]):
                    t.cell(r, c).text = strip(txt)
            continue
        if ln.startswith("#"):
            level = len(ln) - len(ln.lstrip("#"))
            doc.add_heading(strip(ln.lstrip("# ")), level=min(level, 3))
        elif ln.startswith("- "):
            doc.add_paragraph(strip(ln[2:]), style="List Bullet")
        elif ln.strip():
            doc.add_paragraph(strip(ln))
        i += 1
    doc.save(path)


def main():
    OUT_MD.write_text(DOC, encoding="utf-8")
    try:
        md_to_docx(DOC, OUT_DOCX)
    except Exception as e:  # noqa: BLE001 - docx is optional (plan: cut if stuck)
        print("docx skipped:", e)
    print("wrote", OUT_MD.relative_to(ROOT), "and", OUT_DOCX.name)


if __name__ == "__main__":
    sys.exit(main())
