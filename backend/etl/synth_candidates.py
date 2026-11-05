"""Simulated candidates (is_simulated=true). Skills sampled from the skill
distribution of jobs in the candidate's field, so supply tracks real demand structure."""
import random
from collections import defaultdict
from psycopg2.extras import execute_values
from app.db import connect

N_CANDIDATES = 400
SEED = 42
HO = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Vũ", "Đặng", "Bùi", "Đỗ", "Ngô", "Dương", "Lý"]
DEM = ["Văn", "Thị", "Minh", "Quốc", "Thu", "Ngọc", "Hải", "Thanh", "Đức", "Mai", "Anh", "Gia"]
TEN = ["An", "Bình", "Châu", "Dũng", "Giang", "Hà", "Hiếu", "Hương", "Khoa", "Lan", "Linh", "Long",
       "Nam", "Phúc", "Quân", "Sơn", "Thảo", "Trang", "Tuấn", "Vy", "Yến", "Hùng", "Nhung", "Tâm"]
LOCS = ["Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Hải Phòng", "Bắc Ninh", "Hưng Yên"]
LOC_W = [38, 36, 10, 6, 5, 5]


def main():
    rng = random.Random(SEED)
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM candidate WHERE is_simulated")
    if cur.fetchone()[0] >= N_CANDIDATES:
        print("candidates already seeded")
        return
    cur.execute("""SELECT j.category, js.skill_id, COUNT(*) FROM job_posting j
                   JOIN job_skill js ON js.job_id=j.id GROUP BY 1,2""")
    dist = defaultdict(lambda: ([], []))
    for cat, sid, n in cur.fetchall():
        dist[cat][0].append(sid)
        dist[cat][1].append(n)
    cur.execute("SELECT category, COUNT(*) FROM job_posting GROUP BY 1")
    cats = cur.fetchall()
    cat_names = [c for c, _ in cats]
    cat_w = [n for _, n in cats]
    edus = ["THPT", "Cao đẳng", "Đại học", "Đại học", "Thạc sĩ"]
    for _ in range(N_CANDIDATES):
        cat = rng.choices(cat_names, cat_w)[0]
        edu = rng.choice(edus)
        exp = round(max(0.0, rng.gauss(2.5, 2.0)), 1)
        name = f"{rng.choice(HO)} {rng.choice(DEM)} {rng.choice(TEN)}"
        cur.execute("""INSERT INTO candidate (full_name, major, gpa, exp_years, education, location,
                       expected_salary, is_simulated) VALUES (%s,%s,%s,%s,%s,%s,%s,true) RETURNING id""",
                    (name, cat, round(rng.uniform(2.2, 3.9), 2), min(exp, 15), edu,
                     rng.choices(LOCS, LOC_W)[0], round(max(5, rng.gauss(8 + 2.5 * exp, 3)), 1)))
        cid = cur.fetchone()[0]
        sids, w = dist[cat]
        k = min(len(sids), rng.randint(3, 10))
        chosen = set()
        while len(chosen) < k:
            chosen.add(rng.choices(sids, w)[0])
        execute_values(cur, "INSERT INTO candidate_skill (candidate_id, skill_id, source) VALUES %s",
                       [(cid, s, "manual") for s in chosen])
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM candidate_skill")
    print("candidates:", N_CANDIDATES, "candidate_skill:", cur.fetchone()[0])
    conn.close()


if __name__ == "__main__":
    main()
