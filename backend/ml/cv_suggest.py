"""CV improvement suggestions. Gemini (free tier) when a key exists, deterministic fallback otherwise.

Result schema: {summary, add_keywords, rewrite_bullets, priority_fixes}. `source` = gemini | fallback.
"""
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutTimeout
from typing import Dict, List

TIMEOUT_S = 15


def fallback(job: Dict, missing: List[str], health_issues: List[str], matched: List[str]) -> Dict:
    kws = missing[:6]
    return {
        "summary": (f"CV hiện khớp {len(matched)} kỹ năng với vị trí '{job['title']}'. "
                    f"Cần bổ sung {len(missing)} kỹ năng còn thiếu và khắc phục {len(health_issues)} vấn đề về chất lượng CV."),
        "add_keywords": kws,
        "rewrite_bullets": [f"Nếu đã từng dùng {k}, thêm 1 gạch đầu dòng nêu bối cảnh, công cụ và kết quả đo được "
                            f"(ví dụ: 'Dùng {k} để ..., giúp giảm X% thời gian')." for k in kws[:3]],
        "priority_fixes": health_issues[:4] or ["CV đã đầy đủ các mục cơ bản — tập trung bổ sung từ khoá còn thiếu."],
    }


def _prompt(job: Dict, cv_text: str, missing: List[str], matched: List[str]) -> str:
    return (
        "Bạn là chuyên gia tuyển dụng. Dựa trên CV và tin tuyển dụng dưới đây, trả về DUY NHẤT một JSON "
        'với các khoá: "summary" (string, 2 câu), "add_keywords" (list string, tối đa 8, chỉ từ kỹ năng thiếu hoặc '
        'liên quan), "rewrite_bullets" (list string, tối đa 3 câu viết lại mẫu, không bịa số liệu — dùng X/Y làm chỗ '
        'trống), "priority_fixes" (list string, tối đa 4). Trả lời bằng tiếng Việt.\n\n'
        f"TIN: {job['title']} — {job.get('category')}\nYêu cầu: {(job.get('requirements') or '')[:600]}\n"
        f"Kỹ năng đã khớp: {', '.join(matched) or '-'}\nKỹ năng còn thiếu: {', '.join(missing) or '-'}\n\n"
        f"CV:\n{cv_text[:3500]}")


def _call_gemini(prompt: str) -> Dict:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"],
                          http_options=types.HttpOptions(timeout=TIMEOUT_S * 1000))
    resp = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest"), contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.4))
    text = re.sub(r"^```(?:json)?|```$", "", (resp.text or "").strip(), flags=re.M).strip()
    data = json.loads(text)
    out = {k: data.get(k) for k in ("summary", "add_keywords", "rewrite_bullets", "priority_fixes")}
    if not isinstance(out["summary"], str) or not all(isinstance(out[k], list) for k in list(out)[1:]):
        raise ValueError("bad schema from model")
    return out


def suggest(job: Dict, cv_text: str, missing: List[str], matched: List[str], health_issues: List[str]) -> Dict:
    """Never raises: any Gemini failure (no key, quota, timeout, bad JSON) degrades to the template."""
    if os.getenv("GEMINI_API_KEY"):
        try:
            with ThreadPoolExecutor(max_workers=1) as ex:
                content = ex.submit(_call_gemini, _prompt(job, cv_text, missing, matched)).result(timeout=TIMEOUT_S + 2)
            return {"content": content, "source": "gemini"}
        except (FutTimeout, Exception):  # noqa: BLE001
            pass
    return {"content": fallback(job, missing, health_issues, matched), "source": "fallback"}
