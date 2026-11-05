"""Generate 3 sample CVs (good / average / poor) as .docx into data/sample_cvs/. Deterministic."""
import sys
from pathlib import Path

from docx import Document

OUT = Path(__file__).resolve().parents[1] / "data" / "sample_cvs"

GOOD = """Nguyễn Minh Anh
Email: minhanh.dev@gmail.com | Điện thoại: 0912 345 678 | github.com/minhanh-dev | Hà Nội

Mục tiêu nghề nghiệp
Backend developer 3 năm kinh nghiệm, tập trung xây dựng API hiệu năng cao và pipeline dữ liệu.

Học vấn
Cử nhân Công nghệ thông tin - Đại học Bách Khoa Hà Nội (2018 - 2022)
GPA: 3.4/4

Kinh nghiệm làm việc
Backend Developer - Công ty FPT Software (06/2022 - nay)
- Thiết kế 12 REST API bằng Python và FastAPI, phục vụ 50000 người dùng mỗi ngày
- Tối ưu truy vấn PostgreSQL, giảm 40% thời gian phản hồi trung bình
- Đóng gói dịch vụ bằng Docker, thiết lập CI/CD với GitHub Actions, rút ngắn 60% thời gian triển khai
Thực tập sinh Data - Công ty VNG (06/2021 - 09/2021)
- Xây dựng 5 báo cáo SQL và Excel cho đội kinh doanh, tiết kiệm 10 giờ làm việc mỗi tuần

Dự án
Hệ thống gợi ý việc làm
- Dùng Python, scikit-learn, TF-IDF để xếp hạng 3000 tin tuyển dụng, đạt nDCG@10 là 0.82
Ứng dụng quản lý chi tiêu
- Xây dựng bằng React và Node.js, 200 người dùng thử nghiệm

Kỹ năng
Python, FastAPI, Django, PostgreSQL, MySQL, Redis, Docker, Git, Linux, React, SQL, pandas, scikit-learn, AWS

Chứng chỉ
AWS Cloud Practitioner (2023); IELTS 7.0
"""

AVERAGE = """Trần Văn Bình
Email: binh.tran@gmail.com
Hà Nội

Học vấn
Đại học Công nghiệp Hà Nội - Công nghệ thông tin (2019 - 2023)

Kinh nghiệm
Lập trình viên - Công ty ABC (2023 - 2024)
- Tham gia phát triển website bán hàng bằng PHP và MySQL
- Viết các chức năng quản lý đơn hàng
- Sửa lỗi theo yêu cầu của khách hàng

Kỹ năng
HTML, CSS, JavaScript, PHP, MySQL, Git
Chăm chỉ, nhiệt tình, ham học hỏi
"""

POOR = """Lê Văn C
tôi là người chăm chỉ, nhiệt tình, năng động, ham học hỏi, cầu tiến, có trách nhiệm, chịu khó, làm việc nhóm tốt.
Muốn tìm việc làm ổn định.
Biết dùng máy tính.
"""


def write(name: str, body: str):
    doc = Document()
    for line in body.strip().split("\n"):
        doc.add_paragraph(line)
    OUT.mkdir(parents=True, exist_ok=True)
    doc.save(OUT / name)


def main():
    write("cv_tot.docx", GOOD)
    write("cv_trung_binh.docx", AVERAGE)
    write("cv_kem.docx", POOR)
    print("wrote", sorted(p.name for p in OUT.glob("*.docx")))


if __name__ == "__main__":
    sys.exit(main())
