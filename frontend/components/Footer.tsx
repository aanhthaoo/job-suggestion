'use client'

import Link from 'next/link'
import { Sparkles, Briefcase, FileText, BarChart3, Users, ExternalLink, Heart } from 'lucide-react'

export function Footer() {
  return (
    <footer className="mt-20 border-t border-rose-100/80 bg-gradient-to-b from-white/60 via-pink-50/20 to-blue-50/30">
      <div className="max-w-6xl mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-10">
          {/* Brand Info */}
          <div className="md:col-span-1 space-y-3">
            <Link href="/" className="inline-flex items-center gap-2">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-pink-500 via-rose-500 to-blue-600 flex items-center justify-center text-white shadow-md shadow-pink-500/20">
                <Sparkles className="w-5 h-5" />
              </div>
              <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-slate-900 via-blue-900 to-pink-700 bg-clip-text text-transparent">
                JobPortal <span className="text-pink-600 text-xs px-1.5 py-0.5 rounded-md bg-pink-50 border border-pink-200">AI</span>
              </span>
            </Link>
            <p className="text-xs text-slate-600 leading-relaxed">
              Hệ thống tìm việc và kết nối tuyển dụng thông minh ứng dụng AI Matching 5 thành phần & Business Intelligence Analytics cho thị trường lao động Việt Nam.
            </p>
            <div className="pt-1 flex items-center gap-1.5 text-xs text-slate-500">
              <span>Được thiết kế với</span>
              <Heart className="w-3.5 h-3.5 text-rose-500 fill-rose-500" />
              <span>tông Hồng Pastel & Xanh Dương</span>
            </div>
          </div>

          {/* Dành cho Ứng viên */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-1.5">
              <Briefcase className="w-3.5 h-3.5 text-pink-600" />
              Dành cho Ứng viên
            </h4>
            <ul className="space-y-2 text-xs text-slate-600">
              <li>
                <Link href="/jobs" className="hover:text-pink-600 transition">
                  Tra cứu 3.500+ việc làm
                </Link>
              </li>
              <li>
                <Link href="/recommendations" className="hover:text-pink-600 transition flex items-center gap-1">
                  <span>AI Gợi ý việc làm</span>
                  <span className="text-[10px] bg-pink-100 text-pink-700 font-semibold px-1 rounded">HOT</span>
                </Link>
              </li>
              <li>
                <Link href="/profile" className="hover:text-pink-600 transition">
                  Chấm điểm CV Health (6 luật)
                </Link>
              </li>
              <li>
                <Link href="/applications" className="hover:text-pink-600 transition">
                  Tiến trình đơn ứng tuyển (Funnel)
                </Link>
              </li>
            </ul>
          </div>

          {/* Dành cho Nhà tuyển dụng */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-1.5">
              <Users className="w-3.5 h-3.5 text-blue-600" />
              Nhà tuyển dụng
            </h4>
            <ul className="space-y-2 text-xs text-slate-600">
              <li>
                <Link href="/employer/dashboard" className="hover:text-blue-600 transition">
                  Dashboard hiệu quả tuyển dụng
                </Link>
              </li>
              <li>
                <Link href="/employer/candidates" className="hover:text-blue-600 transition">
                  AI Xếp hạng & Phễu ứng viên
                </Link>
              </li>
              <li>
                <Link href="/employer/jobs" className="hover:text-blue-600 transition">
                  Đăng tin tuyển dụng đa thông tin
                </Link>
              </li>
            </ul>
          </div>

          {/* Quản trị & BI Analytics */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-1.5">
              <BarChart3 className="w-3.5 h-3.5 text-indigo-600" />
              Dữ liệu & Phân tích
            </h4>
            <ul className="space-y-2 text-xs text-slate-600">
              <li>
                <Link href="/admin/dashboard" className="hover:text-indigo-600 transition">
                  Cung - Cầu kỹ năng & Lương median
                </Link>
              </li>
              <li>
                <a
                  href="http://localhost:8088"
                  target="_blank"
                  rel="noreferrer"
                  className="hover:text-indigo-600 transition inline-flex items-center gap-1"
                >
                  <span>Apache Superset BI</span>
                  <ExternalLink className="w-3 h-3 text-slate-400" />
                </a>
              </li>
              <li>
                <a
                  href="http://localhost:8000/docs"
                  target="_blank"
                  rel="noreferrer"
                  className="hover:text-indigo-600 transition inline-flex items-center gap-1"
                >
                  <span>FastAPI Swagger Docs</span>
                  <ExternalLink className="w-3 h-3 text-slate-400" />
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom copyright */}
        <div className="pt-6 border-t border-slate-200/60 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500">
          <p>© 2026 JobPortal AI. Bài tập lớn Hệ thống Trí tuệ Doanh nghiệp (Business Intelligence).</p>
          <div className="flex items-center gap-4">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-pink-100/70 text-pink-700 font-medium text-[11px] border border-pink-200/50">
              <span className="w-1.5 h-1.5 rounded-full bg-pink-500 animate-pulse"></span>
              Pastel Rose & Sky Blue Theme
            </span>
          </div>
        </div>
      </div>
    </footer>
  )
}

