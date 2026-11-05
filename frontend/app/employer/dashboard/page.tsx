'use client'

import { useEffect, useState } from 'react'
import Header from '@/components/Header'
import SimBanner from '@/components/SimBanner'
import { api } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { SUPERSET_URL } from '@/lib/utils'
import { Briefcase, Users, Target, Clock, ExternalLink, BarChart3, AlertCircle } from 'lucide-react'

type Kpi = Awaited<ReturnType<typeof api.getKpi>>

export default function EmployerDashboard() {
  const { ready } = useAuth(['employer'])
  const [k, setK] = useState<Kpi | null>(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    if (ready) api.getKpi().then(setK).catch((e) => setErr(e.message))
  }, [ready])

  const f = k?.funnel
  const stages = f
    ? ([
        ['1. Nộp đơn', f.applied],
        ['2. Sàng lọc hồ sơ', f.screening],
        ['3. Mời phỏng vấn', f.interview],
        ['4. Gửi Offer', f.offer],
      ] as [string, number][])
    : []
  const max = Math.max(1, ...stages.map((s) => s[1]))
  const maxMiss = Math.max(1, ...(k?.top_missing_skills.map((s) => s.n_missing) ?? [1]))
  const pct = (a: number, b: number) => (b ? `${Math.round((a / b) * 100)}%` : '-')

  return (
    <div className="min-h-screen bg-slate-50/60">
      <Header />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Dashboard Tuyển dụng
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 mt-1 font-medium">
              Báo cáo hiệu quả & phễu tuyển dụng {k?.company ? `· ${k.company}` : ''}
            </p>
          </div>

          <a
            href={`${SUPERSET_URL}/superset/dashboard/tuyen-dung/`}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-white border border-rose-200/80 text-xs sm:text-sm font-semibold text-blue-600 hover:text-blue-700 hover:bg-rose-50/50 shadow-2xs transition"
          >
            <span>Mở Apache Superset BI</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>

        <SimBanner />

        {err && (
          <div className="bg-rose-50 border border-rose-200 text-rose-800 px-4 py-3 rounded-2xl mb-6 text-sm flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-rose-500 shrink-0" />
            <span>{err}</span>
          </div>
        )}

        {k && f && (
          <>
            {/* KPI Cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <div className="bg-white/90 backdrop-blur-sm rounded-2xl border border-blue-100 p-5 shadow-xs">
                <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center mb-3">
                  <Briefcase className="w-5 h-5" />
                </div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Tin đang mở</p>
                <p className="text-3xl font-extrabold text-slate-900 mt-1">{k.n_active_jobs}</p>
              </div>

              <div className="bg-white/90 backdrop-blur-sm rounded-2xl border border-indigo-100 p-5 shadow-xs">
                <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-3">
                  <Users className="w-5 h-5" />
                </div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Tổng đơn nhận</p>
                <p className="text-3xl font-extrabold text-slate-900 mt-1">{f.applied}</p>
              </div>

              <div className="bg-white/90 backdrop-blur-sm rounded-2xl border border-pink-100 p-5 shadow-xs">
                <div className="w-10 h-10 rounded-xl bg-pink-50 text-pink-600 flex items-center justify-center mb-3">
                  <Target className="w-5 h-5" />
                </div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Tỷ lệ phỏng vấn</p>
                <p className="text-3xl font-extrabold text-slate-900 mt-1">{pct(f.interview, f.applied)}</p>
              </div>

              <div className="bg-white/90 backdrop-blur-sm rounded-2xl border border-teal-100 p-5 shadow-xs">
                <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center mb-3">
                  <Clock className="w-5 h-5" />
                </div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Phản hồi trung bình</p>
                <p className="text-3xl font-extrabold text-slate-900 mt-1">
                  {f.avg_days_to_response ?? '-'} <span className="text-sm font-normal text-slate-400">ngày</span>
                </p>
              </div>
            </div>

            {/* Charts Section */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* Funnel Section */}
              <section className="bg-white/90 backdrop-blur-sm rounded-2xl border border-slate-200/80 p-6 shadow-sm">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="font-bold text-slate-900 text-base flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-blue-600" />
                    Phễu chuyển đổi tuyển dụng
                  </h2>
                  <span className="text-xs text-blue-700 bg-blue-50 px-2.5 py-1 rounded-lg font-semibold">
                    Điểm TB: {f.avg_match ?? '-'}
                  </span>
                </div>

                <div className="space-y-3.5">
                  {stages.map(([l, v]) => (
                    <div key={l}>
                      <div className="flex justify-between text-xs font-medium text-slate-700 mb-1.5">
                        <span>{l}</span>
                        <span className="font-bold text-slate-900">
                          {v} ứng viên ({pct(v, f.applied)})
                        </span>
                      </div>
                      <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-3 rounded-full bg-gradient-to-r from-blue-600 via-indigo-500 to-pink-500 transition-all duration-300"
                          style={{ width: `${(v / max) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              {/* Missing Skills Section */}
              <section className="bg-white/90 backdrop-blur-sm rounded-2xl border border-slate-200/80 p-6 shadow-sm">
                <h2 className="font-bold text-slate-900 text-base mb-4 flex items-center gap-2">
                  <Target className="w-4 h-4 text-pink-500" />
                  Kỹ năng ứng viên thiếu nhiều nhất
                </h2>

                {k.top_missing_skills.length === 0 && (
                  <p className="text-xs text-slate-400 italic">Chưa có dữ liệu đơn ứng tuyển.</p>
                )}

                <div className="space-y-3">
                  {k.top_missing_skills.map((s) => (
                    <div key={s.skill}>
                      <div className="flex justify-between text-xs font-medium text-slate-700 mb-1">
                        <span>{s.skill}</span>
                        <span className="font-bold text-rose-600">{s.n_missing} đơn thiếu</span>
                      </div>
                      <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-2.5 rounded-full bg-gradient-to-r from-rose-400 to-pink-500 transition-all duration-300"
                          style={{ width: `${(s.n_missing / maxMiss) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
