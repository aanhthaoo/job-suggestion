'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import Header from '@/components/Header'
import JobCard from '@/components/JobCard'
import { api, type Job } from '@/lib/api'
import { Search, Sparkles, FileText, Target, TrendingUp, ArrowRight, ShieldCheck, Briefcase } from 'lucide-react'

const TOP_CATEGORIES = [
  'Công nghệ thông tin',
  'Kinh doanh - Bán hàng',
  'Marketing - Truyền thông',
  'Tài chính - Kế toán',
  'Thiết kế - Nghệ thuật',
  'Nhân sự - Hành chính'
]

export default function Home() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [total, setTotal] = useState(0)
  const [q, setQ] = useState('')

  useEffect(() => {
    api.getJobs({ limit: 6 }).then((d) => {
      setJobs(d.items)
      setTotal(d.total)
    }).catch(() => {})
  }, [])

  return (
    <div className="min-h-screen bg-slate-50/60">
      <Header />

      {/* Hero Section with Soft Pink & Blue Gradient */}
      <section className="relative overflow-hidden bg-gradient-to-b from-rose-50/80 via-pink-50/30 to-slate-50/60 pt-16 pb-20 border-b border-rose-100/60">
        {/* Decorative background glows */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-400/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute top-10 right-1/4 w-96 h-96 bg-pink-400/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative max-w-5xl mx-auto px-4 text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/80 backdrop-blur-sm border border-rose-200/80 text-xs font-semibold text-rose-700 shadow-xs mb-6">
            <Sparkles className="w-3.5 h-3.5 text-pink-500" />
            <span>Nền tảng Tuyển dụng thông minh kết hợp AI & BI</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-slate-900 tracking-tight leading-[1.15]">
            Tìm việc làm phù hợp với{' '}
            <span className="bg-gradient-to-r from-blue-600 via-indigo-600 to-pink-500 bg-clip-text text-transparent">
              năng lực của bạn
            </span>
          </h1>

          <p className="mt-4 text-base sm:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
            Tải CV lên để nhận <b>Matching Score</b> tự động, phân tích kỹ năng còn thiếu và nhận tư vấn tối ưu CV từ AI cho từng vị trí tuyển dụng.
          </p>

          {/* Search Box */}
          <form
            action="/jobs"
            className="mt-8 flex flex-col sm:flex-row gap-2 max-w-2xl mx-auto bg-white/90 backdrop-blur-sm p-2 rounded-2xl border border-rose-200/80 shadow-lg shadow-blue-500/5"
          >
            <div className="flex-1 flex items-center px-3 gap-2">
              <Search className="w-5 h-5 text-slate-400 shrink-0" />
              <input
                name="search"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Vị trí tuyển dụng, kỹ năng (Python, React...), công ty..."
                className="w-full py-2.5 text-sm text-slate-900 bg-transparent focus:outline-none placeholder:text-slate-400"
              />
            </div>
            <button
              type="submit"
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold text-sm rounded-xl shadow-sm transition-all hover:shadow-md hover:shadow-blue-500/20"
            >
              Tìm kiếm
            </button>
          </form>

          {/* Quick Category Chips */}
          <div className="mt-6 flex flex-wrap items-center justify-center gap-2 max-w-3xl mx-auto">
            <span className="text-xs text-slate-500 font-medium">Gợi ý nhanh:</span>
            {TOP_CATEGORIES.map((cat) => (
              <Link
                key={cat}
                href={`/jobs?category=${encodeURIComponent(cat)}`}
                className="px-3 py-1 rounded-full text-xs font-medium bg-white/80 hover:bg-rose-50 text-slate-600 hover:text-rose-700 border border-slate-200/70 hover:border-rose-200 transition-colors shadow-2xs"
              >
                {cat}
              </Link>
            ))}
          </div>

          <div className="mt-8 flex items-center justify-center gap-6 text-xs sm:text-sm text-slate-500 font-medium">
            <span className="flex items-center gap-1.5">
              <Briefcase className="w-4 h-4 text-blue-500" />
              <b>{total.toLocaleString('vi-VN')}</b> tin tuyển dụng đang mở
            </span>
            <span className="w-1.5 h-1.5 rounded-full bg-slate-300" />
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-500" />
              Dữ liệu thị trường thật từ VietJobs
            </span>
          </div>
        </div>
      </section>

      {/* 3 Core Smart Features */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8 relative z-10">
        <div className="grid md:grid-cols-3 gap-5">
          <div className="bg-white/90 backdrop-blur-sm rounded-2xl border border-slate-200/80 p-6 shadow-sm hover:border-pink-300 hover:shadow-md transition duration-200">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-blue-100 to-blue-50 text-blue-600 flex items-center justify-center mb-4 border border-blue-200/60">
              <Target className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-slate-900 text-base mb-1.5">Matching Score AI</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Mô hình học máy chấm điểm độ phù hợp (0-100%) dựa trên 7 đặc trưng: kỹ năng, nội dung CV-JD, kinh nghiệm, bằng cấp và dải lương.
            </p>
          </div>

          <div className="bg-white/90 backdrop-blur-sm rounded-2xl border border-slate-200/80 p-6 shadow-sm hover:border-pink-300 hover:shadow-md transition duration-200">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-pink-100 to-rose-50 text-pink-600 flex items-center justify-center mb-4 border border-pink-200/60">
              <FileText className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-slate-900 text-base mb-1.5">Chấm sức khỏe CV (Health Score)</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Tự động phân tích CV theo 6 luật định lượng minh bạch: cấu trúc, liên hệ, từ khóa kỹ năng, số liệu định lượng và cảnh báo từ ngữ sáo rỗng.
            </p>
          </div>

          <div className="bg-white/90 backdrop-blur-sm rounded-2xl border border-slate-200/80 p-6 shadow-sm hover:border-pink-300 hover:shadow-md transition duration-200">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-purple-100 to-indigo-50 text-indigo-600 flex items-center justify-center mb-4 border border-indigo-200/60">
              <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-slate-900 text-base mb-1.5">Tối ưu CV với Gemini AI</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Đề xuất từ khóa cần bổ sung, viết lại các gạch đầu dòng thành tích và xếp thứ tự ưu tiên điều chỉnh để nâng cao cơ hội trúng tuyển.
            </p>
          </div>
        </div>
      </section>

      {/* Latest Jobs Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-bold text-slate-900">Tin tuyển dụng mới nhất</h2>
            <p className="text-xs text-slate-500 mt-1">Cập nhật liên tục từ thị trường việc làm Việt Nam</p>
          </div>
          <Link
            href="/jobs"
            className="inline-flex items-center gap-1 text-sm font-semibold text-blue-600 hover:text-blue-700 bg-blue-50/70 hover:bg-blue-100/70 px-4 py-2 rounded-xl transition"
          >
            <span>Xem tất cả</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          {jobs.map((j) => (
            <JobCard key={j.id} job={j} />
          ))}
        </div>
      </section>
    </div>
  )
}
