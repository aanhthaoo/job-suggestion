'use client'

import { Suspense, useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import Header from '@/components/Header'
import JobCard from '@/components/JobCard'
import { api, type Job } from '@/lib/api'
import { Search, Filter, ChevronLeft, ChevronRight, Briefcase } from 'lucide-react'

const CATEGORIES = [
  'Công nghệ thông tin',
  'Kinh doanh - Bán hàng',
  'Marketing - Truyền thông',
  'Tài chính - Kế toán',
  'Thiết kế - Nghệ thuật',
  'Nhân sự - Hành chính',
  'Xây dựng - Kiến trúc',
  'Logistics - Vận tải',
  'Điện - Điện tử',
  'Giáo dục - Đào tạo',
  'Y tế - Dược',
  'Sản xuất - Cơ khí',
  'Du lịch - Dịch vụ',
]
const LOCATIONS = ['Hà Nội', 'Hồ Chí Minh', 'Đà Nẵng', 'Hải Phòng', 'Bắc Ninh', 'Hưng Yên']
const LEVELS = ['Intern', 'Junior', 'Mid', 'Senior', 'Manager']
const LIMIT = 10

function JobsInner() {
  const sp = useSearchParams()
  const [search, setSearch] = useState(sp.get('search') || '')
  const [category, setCategory] = useState(sp.get('category') || '')
  const [location, setLocation] = useState('')
  const [level, setLevel] = useState('')
  const [page, setPage] = useState(1)
  const [data, setData] = useState<{ items: Job[]; total: number }>({ items: [], total: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    api.getJobs({ search, category, location, level, page, limit: LIMIT })
      .then((d) => {
        setData(d)
        setError('')
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [search, category, location, level, page])

  const reset = (fn: (v: string) => void) => (e: React.ChangeEvent<HTMLSelectElement>) => {
    fn(e.target.value)
    setPage(1)
  }

  const pages = Math.max(1, Math.ceil(data.total / LIMIT))
  const selCls = 'px-3 py-2.5 border border-slate-200 rounded-xl bg-white text-xs sm:text-sm text-slate-700 font-medium focus:outline-none focus:ring-2 focus:ring-pink-300 focus:border-pink-400 transition shadow-2xs'

  return (
    <div className="min-h-screen bg-slate-50/60">
      <Header />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Header Title */}
        <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Khám phá việc làm
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 mt-1">
              Tìm kiếm và lọc cơ hội nghề nghiệp phù hợp với tiêu chí của bạn
            </p>
          </div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white border border-rose-200/80 text-xs font-semibold text-rose-700 shadow-2xs w-fit">
            <Briefcase className="w-3.5 h-3.5 text-pink-500" />
            <span>{data.total.toLocaleString('vi-VN')} tin tuyển dụng</span>
          </div>
        </div>

        {/* Filter Bar Card */}
        <div className="bg-white/90 backdrop-blur-sm rounded-2xl border border-rose-200/80 p-4 shadow-sm mb-6">
          <div className="flex flex-col lg:flex-row gap-3">
            {/* Search Input */}
            <div className="flex-1 relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value)
                  setPage(1)
                }}
                placeholder="Từ khóa, kỹ năng (Python, SQL, React...), công ty..."
                className="w-full pl-9 pr-4 py-2.5 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 bg-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-300 focus:border-blue-400 transition shadow-2xs"
              />
            </div>

            {/* Dropdown Filters */}
            <div className="flex flex-wrap sm:flex-nowrap gap-2.5">
              <select className={selCls} value={category} onChange={reset(setCategory)}>
                <option value="">Tất cả ngành nghề</option>
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>

              <select className={selCls} value={location} onChange={reset(setLocation)}>
                <option value="">Tất cả địa điểm</option>
                {LOCATIONS.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>

              <select className={selCls} value={level} onChange={reset(setLevel)}>
                <option value="">Tất cả cấp bậc</option>
                {LEVELS.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-rose-50 border border-rose-200 text-rose-800 px-4 py-3 rounded-2xl mb-6 text-sm">
            {error}
          </div>
        )}

        {/* Status text */}
        <div className="flex justify-between items-center mb-4">
          <p className="text-xs sm:text-sm text-slate-600 font-medium">
            {loading ? 'Đang lọc việc làm...' : `Hiển thị ${data.items.length} tin (Trang ${page}/${pages})`}
          </p>
          {(search || category || location || level) && (
            <button
              onClick={() => {
                setSearch('')
                setCategory('')
                setLocation('')
                setLevel('')
                setPage(1)
              }}
              className="text-xs text-rose-600 hover:text-rose-700 font-semibold hover:underline"
            >
              Xóa bộ lọc
            </button>
          )}
        </div>

        {/* Jobs List */}
        <div className="space-y-3.5">
          {data.items.map((j) => (
            <JobCard key={j.id} job={j} />
          ))}

          {!loading && data.items.length === 0 && (
            <div className="bg-white rounded-2xl border border-slate-200/80 p-12 text-center">
              <div className="w-12 h-12 rounded-full bg-rose-50 text-pink-500 flex items-center justify-center mx-auto mb-3">
                <Filter className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-slate-800 text-base mb-1">Không tìm thấy việc làm phù hợp</h3>
              <p className="text-xs sm:text-sm text-slate-500 max-w-md mx-auto">
                Hãy thử nới lỏng từ khóa tìm kiếm hoặc chọn lại địa điểm, ngành nghề để có thêm kết quả.
              </p>
            </div>
          )}
        </div>

        {/* Pagination Controls */}
        {pages > 1 && (
          <div className="flex justify-center items-center gap-3 mt-10">
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="inline-flex items-center gap-1 px-4 py-2 bg-white border border-slate-200 rounded-xl text-xs sm:text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition shadow-2xs"
            >
              <ChevronLeft className="w-4 h-4" />
              Trước
            </button>
            <span className="text-xs sm:text-sm text-slate-600 font-semibold px-3 py-1 bg-white border border-slate-200 rounded-lg">
              {page} / {pages}
            </span>
            <button
              disabled={page >= pages}
              onClick={() => setPage(page + 1)}
              className="inline-flex items-center gap-1 px-4 py-2 bg-white border border-slate-200 rounded-xl text-xs sm:text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition shadow-2xs"
            >
              Sau
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </main>
    </div>
  )
}

export default function JobsPage() {
  return (
    <Suspense>
      <JobsInner />
    </Suspense>
  )
}
