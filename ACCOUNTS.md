# Tài khoản demo

Tạo tự động bởi `python -m app.seed_db`. Mật khẩu băm bcrypt trong bảng `users`.

| Vai trò | Email | Mật khẩu |
|---|---|---|
| Ứng viên | candidate@demo.com | demo123 |
| Nhà tuyển dụng (công ty A) | employer@demo.com | demo123 |
| Nhà tuyển dụng (công ty B, dùng thử phân quyền) | employer2@demo.com | demo123 |
| Quản trị | admin@demo.com | demo123 |

Superset: admin / admin (http://localhost:8088, cần chạy Phiên 6 để có dashboard).
