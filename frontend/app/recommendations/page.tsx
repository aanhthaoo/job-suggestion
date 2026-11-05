'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import Header from '@/components/Header'
import ScoreBadge from '@/components/ScoreBadge'
import { api, type Recommendation } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { formatSalary } from '@/lib/utils'
import { Sparkles, MapPin, Wallet, Briefcase, ArrowUpRight, Cpu, AlertCircle } from 'lucide-react'

export default function RecommendationsPage() {
  const { ready } = useAuth(['candidate'])
  const [items, setItems] = useState<Recommendation[]>([])
  const [model, setModel] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!ready) return
    api.getRecommendations(20)
      .then((d) => {
        setItems(d.recommendations)
        setModel(d.model_version)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [ready])

  return (
    <div className="min-h-screen bg-slate-50/60">
      <Header />

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Banner with Pink & Blue Gradient */}
        <div className="relative overflow-hidden bg-gradient-to-r from-blue-600 via-indigo-600 to-pink-500 rounded-3xl p-6 sm:p-8 text-white shadow-lg shadow-blue-500/10 mb-8">
          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/20 backdrop-blur-md text-xs font-semibold mb-3">
                <Sparkles className="w-3.5 h-3.5 text-pink-200" />
                <span>Gợi ý độc quyền cho bạn</span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
                Việc làm phù hợp nhất với hồ sơ
              </h1>
              <p className="mt-2 text-xs sm:text-sm text-blue-100 max-w-xl leading-relaxed">
                Các vị trí được xếp hạng theo Matching Score dựa trên hồ sơ, kỹ năng và kinh nghiệm thực tế của bạn.
              </p>
            </div>

            <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-4 text-xs shrink-0 self-start md:self-auto">
              <div className="flex items-center gap-2 mb-1">
                <Cpu className="w-4 h-4 text-pink-200" />
                <span className="font-semibold text-white">Mô hình AI: {model || 'Đang nạp...'}</span>
              </div>
              <p className="text-blue-100 text-[11px] mt-1">
                Muốn độ chính xác cao hơn?{' '}
                <Link href="/profile" className="text-pink-200 hover:text-white underline font-semibold">
                  Cập nhật CV ngay
                </Link>
              </p>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-rose-50 border border-rose-200 text-rose-800 px-4 py-3 rounded-2xl mb-6 text-sm flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-rose-500 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {loading && (
          <div className="bg-white rounded-2xl border border-slate-200/80 p-12 text-center shadow-xs">
            <div className="w-10 h-10 border-3 border-pink-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-sm font-semibold text-slate-700">Đang phân tích hồ sơ và tính điểm khớp...</p>
            <p className="text-xs text-slate-500 mt-1">Mô hình AI đang quét các tin tuyển dụng phù hợp nhất cho bạn</p>
          </div>
        )}

        {!loading && !error && items.length === 0 && (
          <div className="bg-white rounded-3xl border-2 border-dashed border-rose-200 p-8 sm:p-12 text-center shadow-sm space-y-4">
            <div className="w-14 h-14 rounded-2xl bg-pink-50 text-pink-500 flex items-center justify-center mx-auto">
              <Sparkles className="w-7 h-7" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">Chưa có dữ liệu gợi ý việc làm</h3>
            <p className="text-xs sm:text-sm text-slate-600 max-w-md mx-auto leading-relaxed">
              Tài khoản của bạn chưa tải lên CV hoặc cập nhật kỹ năng cá nhân. Hãy vào trang Hồ sơ để tải lên CV, hệ thống AI sẽ tự động phân tích và xếp hạng các việc làm phù hợp nhất cho bạn!
            </p>
            <div className="pt-2">
              <Link
                href="/profile"
                className="inline-flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl text-xs sm:text-sm font-semibold shadow-sm transition"
              >
                <span>Cập nhật Hồ sơ & Tải lên CV</span>
              </Link>
            </div>
          </div>
        )}

        {/* Recommendations List */}
        <div className="space-y-4">
          {items.map((r, i) => {
            const isTop3 = i < 3
            return (
              <Link
                key={r.job.id}
                href={`/jobs/${r.job.id}?from=recommend`}
                className="group block bg-white rounded-2xl border border-slate-200/80 p-5 sm:p-6 hover:border-pink-300 hover:shadow-lg hover:shadow-pink-500/5 hover:-translate-y-0.5 transition-all duration-200"
              >
                <div className="flex justify-between items-start gap-4">
                  <div className="flex items-start gap-3.5">
                    {/* Rank Number Badge */}
                    <span
                      className={`w-8 h-8 rounded-xl flex items-center justify-center font-extrabold text-xs shrink-0 ${
                        i === 0
                          ? 'bg-amber-100 text-amber-800 border border-amber-200'
                          : i === 1
                          ? 'bg-slate-100 text-slate-700 border border-slate-200'
                          : i === 2
                          ? 'bg-amber-50 text-amber-900 border border-amber-200'
                          : 'bg-slate-50 text-slate-500'
                      }`}
                    >
                      #{i + 1}
                    </span>

                    <div>
                      <h3 className="font-bold text-slate-900 text-lg group-hover:text-blue-600 transition-colors flex items-center gap-1.5">
                        {r.job.title}
                        <ArrowUpRight className="w-4 h-4 text-slate-300 group-hover:text-blue-600 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
                      </h3>
                      <p className="text-sm text-slate-500 font-medium mt-0.5">{r.job.company_name}</p>

                      <div className="flex flex-wrap items-center gap-2.5 mt-2.5 text-xs">
                        <span className="flex items-center text-slate-700 font-medium bg-slate-50 px-2.5 py-1 rounded-lg">
                          <MapPin className="w-3.5 h-3.5 mr-1 text-slate-400" />
                          {r.job.location}
                        </span>
                        <span className="flex items-center text-blue-700 font-bold bg-blue-50/80 px-2.5 py-1 rounded-lg border border-blue-100">
                          <Wallet className="w-3.5 h-3.5 mr-1 text-blue-500" />
                          {formatSalary(r.job.salary_min, r.job.salary_max)}
                        </span>
                        {r.job.contract_type && (
                          <span className="flex items-center text-pink-700 font-medium bg-pink-50/80 px-2.5 py-1 rounded-lg border border-pink-100">
                            <Briefcase className="w-3.5 h-3.5 mr-1 text-pink-400" />
                            {r.job.contract_type}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <ScoreBadge score={r.score} level={r.level} />
                </div>

                {/* AI Explanation Box */}
                <div className="mt-4 p-3 rounded-xl bg-gradient-to-r from-blue-50/60 via-indigo-50/30 to-pink-50/40 border border-blue-100/70 text-xs text-slate-700 leading-relaxed">
                  <div className="flex items-center gap-1.5 font-semibold text-blue-900 mb-1">
                    <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                    <span>Lý do đề xuất:</span>
                  </div>
                  {r.reason}
                </div>

                {/* Matched vs Missing Skills */}
                <div className="mt-3 flex flex-wrap items-center gap-4 text-xs pt-2">
                  {r.matched_skills?.length > 0 && (
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="font-semibold text-emerald-700">Khớp:</span>
                      {r.matched_skills.map((s) => (
                        <span key={s} className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-medium text-[11px] border border-emerald-100">
                          {s}
                        </span>
                      ))}
                    </div>
                  )}

                  {r.missing_skills?.length > 0 && (
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="font-semibold text-rose-700">Chưa có:</span>
                      {r.missing_skills.slice(0, 3).map((s) => (
                        <span key={s} className="px-2 py-0.5 rounded bg-rose-50 text-rose-700 font-medium text-[11px] border border-rose-100">
                          {s}
                        </span>
                      ))}
                      {r.missing_skills.length > 3 && (
                        <span className="text-slate-400 text-[11px]">+{r.missing_skills.length - 3}</span>
                      )}
                    </div>
                  )}
                </div>
              </Link>
            )
          })}
        </div>
      </main>
    </div>
  )
}
