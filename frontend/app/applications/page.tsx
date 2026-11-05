'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import Header from '@/components/Header'
import { api, type Application } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { formatDate } from '@/lib/utils'
import { Briefcase, Calendar, MapPin, CheckCircle2, Clock, AlertCircle, ArrowRight } from 'lucide-react'

const STATUS: Record<string, { label: string; cls: string; step: number }> = {
  applied: { label: 'Đã nộp đơn', cls: 'bg-blue-50 text-blue-700 border-blue-200', step: 1 },
  screening: { label: 'Đang sàng lọc', cls: 'bg-indigo-50 text-indigo-700 border-indigo-200', step: 2 },
  interview: { label: 'Vào phỏng vấn', cls: 'bg-amber-50 text-amber-800 border-amber-200', step: 3 },
  offer: { label: 'Nhận Offer', cls: 'bg-emerald-50 text-emerald-700 border-emerald-200', step: 4 },
  rejected: { label: 'Chưa phù hợp', cls: 'bg-rose-50 text-rose-700 border-rose-200', step: 0 },
}

const STAGES = ['Đã nộp', 'Sàng lọc', 'Phỏng vấn', 'Offer']

export default function ApplicationsPage() {
  const { ready } = useAuth(['candidate'])
  const [items, setItems] = useState<Application[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (ready) {
      api.getApplications()
        .then(setItems)
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false))
    }
  }, [ready])

  return (
    <div className="min-h-screen bg-slate-50/60">
      <Header />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="mb-6 flex justify-between items-center">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Đơn ứng tuyển của tôi
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 mt-1">
              Theo dõi tiến trình xét duyệt hồ sơ tại các doanh nghiệp
            </p>
          </div>
          <span className="px-3.5 py-1.5 rounded-xl bg-white border border-rose-200/80 text-xs font-semibold text-rose-700 shadow-2xs">
            {items.length} hồ sơ đã nộp
          </span>
        </div>

        {error && (
          <div className="bg-rose-50 border border-rose-200 text-rose-800 px-4 py-3 rounded-2xl mb-6 text-sm flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-rose-500 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {ready && items.length === 0 && !error && !loading && (
          <div className="bg-white rounded-3xl border border-slate-200/80 p-12 text-center shadow-xs">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-pink-100 to-rose-50 text-pink-600 flex items-center justify-center mx-auto mb-3">
              <Briefcase className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-slate-800 text-base mb-1">Bạn chưa nộp đơn vào vị trí nào</h3>
            <p className="text-xs sm:text-sm text-slate-500 max-w-md mx-auto mb-5">
              Khám phá danh sách việc làm thông minh phù hợp với kỹ năng của bạn để ứng tuyển ngay.
            </p>
            <Link
              href="/recommendations"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold text-xs sm:text-sm shadow-sm hover:shadow-md transition"
            >
              <span>Xem việc làm gợi ý</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        )}

        <div className="space-y-4">
          {items.map((a) => {
            const st = STATUS[a.status] || { label: a.status, cls: 'bg-slate-100 text-slate-700', step: 1 }
            const isRejected = a.status === 'rejected'

            return (
              <div
                key={a.id}
                className="bg-white rounded-2xl border border-slate-200/80 p-5 sm:p-6 shadow-sm hover:border-pink-300 transition"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
                  <div>
                    <Link
                      href={`/jobs/${a.job_id}`}
                      className="font-bold text-slate-900 text-lg hover:text-blue-600 transition"
                    >
                      {a.title}
                    </Link>
                    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 mt-1">
                      <span className="font-medium text-slate-700">{a.company_name}</span>
                      <span>·</span>
                      <span className="flex items-center">
                        <MapPin className="w-3.5 h-3.5 mr-1 text-slate-400" />
                        {a.location || 'Toàn quốc'}
                      </span>
                      <span>·</span>
                      <span className="flex items-center">
                        <Calendar className="w-3.5 h-3.5 mr-1 text-slate-400" />
                        Nộp ngày {formatDate(a.applied_at)}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-start sm:self-center">
                    {a.match_score != null && (
                      <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200">
                        Khớp {Math.round(a.match_score * 100)}%
                      </span>
                    )}
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${st.cls}`}>
                      {st.label}
                    </span>
                  </div>
                </div>

                {/* Funnel Progress Tracker */}
                <div className="mt-4 pt-1">
                  <p className="text-[11px] font-semibold text-slate-400 mb-2">Tiến trình xét tuyển:</p>
                  <div className="grid grid-cols-4 gap-2 text-center text-xs">
                    {STAGES.map((stg, idx) => {
                      const stepNum = idx + 1
                      const reached = !isRejected && st.step >= stepNum
                      const current = !isRejected && st.step === stepNum

                      return (
                        <div key={stg} className="flex flex-col items-center">
                          <div
                            className={`w-full h-1.5 rounded-full mb-1.5 transition-all ${
                              reached
                                ? 'bg-gradient-to-r from-blue-500 to-indigo-600'
                                : isRejected && idx === 0
                                ? 'bg-rose-400'
                                : 'bg-slate-100'
                            }`}
                          />
                          <span
                            className={`text-[11px] font-medium ${
                              current
                                ? 'text-blue-700 font-bold'
                                : reached
                                ? 'text-slate-700'
                                : 'text-slate-400'
                            }`}
                          >
                            {stg}
                          </span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </main>
    </div>
  )
}
