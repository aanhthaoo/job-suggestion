'use client'

import { useEffect, useState } from 'react'
import Header from '@/components/Header'
import SimBanner from '@/components/SimBanner'
import { api } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { SUPERSET_URL } from '@/lib/utils'
import { Database, ExternalLink, BarChart3, TrendingUp, Layers, AlertCircle, Briefcase, Users, FileText, CheckCircle2 } from 'lucide-react'

type Stats = Awaited<ReturnType<typeof api.getAdminStats>>
type Market = Awaited<ReturnType<typeof api.getMarketStats>>

const TABLE_LABEL: Record<string, string> = {
  job_posting: 'Tin tuyển dụng',
  candidate: 'Ứng viên',
  application: 'Đơn ứng tuyển',
  company: 'Doanh nghiệp',
  skill: 'Kỹ năng chuẩn',
  candidate_skill: 'Kỹ năng ứng viên',
  job_skill: 'Kỹ năng tin yêu cầu',
  users: 'Tài khoản người dùng',
}

export default function AdminDashboard() {
  const { ready } = useAuth(['admin'])
  const [s, setS] = useState<Stats | null>(null)
  const [m, setM] = useState<Market | null>(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    if (!ready) return
    api.getAdminStats().then(setS).catch((e) => setErr(e.message))
    api.getMarketStats().then(setM).catch(() => {})
  }, [ready])

  const maxSd = Math.max(1, ...(m?.skill_supply_demand.map((x) => Math.max(x.n_candidates, x.n_jobs)) ?? [1]))

  return (
    <div className="min-h-screen bg-slate-50/60">
      <Header />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Quản trị Hệ thống & BI
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 mt-1">
              Giám sát cơ sở dữ liệu, kho dữ liệu Data Warehouse và phân tích chuyên sâu
            </p>
          </div>

          <div className="flex flex-wrap gap-2.5">
            <a
              target="_blank"
              rel="noreferrer"
              href={`${SUPERSET_URL}/superset/dashboard/thi-truong-lao-dong/`}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white border border-blue-200 text-xs font-semibold text-blue-700 hover:bg-blue-50/70 shadow-2xs transition"
            >
              <span>Superset: Thị trường lao động</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
            <a
              target="_blank"
              rel="noreferrer"
              href={`${SUPERSET_URL}/superset/dashboard/tuyen-dung/`}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white border border-pink-200 text-xs font-semibold text-pink-700 hover:bg-pink-50/70 shadow-2xs transition"
            >
              <span>Superset: Hiệu quả tuyển dụng</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>

        <SimBanner />

        {err && (
          <div className="bg-rose-50 border border-rose-200 text-rose-800 px-4 py-3 rounded-2xl text-sm flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-rose-500 shrink-0" />
            <span>{err}</span>
          </div>
        )}

        {/* Database Record Counts */}
        {s && (
          <section className="bg-white/90 backdrop-blur-sm rounded-2xl border border-rose-200/80 p-6 shadow-sm">
            <div className="flex justify-between items-center mb-5">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                  <Database className="w-4 h-4" />
                </div>
                <h2 className="text-base font-bold text-slate-900">
                  Dữ liệu PostgreSQL
                </h2>
              </div>
              <span className="text-xs px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 font-mono font-medium">
                SEED_MODE: {s.seed_mode}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3.5">
              {Object.entries(s.counts).map(([k, v]) => (
                <div key={k} className="bg-slate-50/80 border border-slate-100 rounded-xl p-3.5 hover:border-pink-200 transition">
                  <p className="text-xs text-slate-500 font-medium truncate">{TABLE_LABEL[k] || k}</p>
                  <p className="text-2xl font-extrabold text-slate-900 mt-1">{v.toLocaleString('vi-VN')}</p>
                </div>
              ))}
            </div>

            <div className="mt-4 pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-600">
              <div>
                <b>Nguồn tin tuyển dụng:</b>{' '}
                {Object.entries(s.job_sources).map(([k, v]) => `${k}: ${v}`).join(' · ')}
              </div>
              <div>
                <b>Ứng viên:</b> Mô phỏng {s.candidates_by_origin.sim} · Thật {s.candidates_by_origin.real}
              </div>
            </div>
          </section>
        )}

        {/* Analytics Section */}
        {m && (
          <div className="grid lg:grid-cols-2 gap-6">
            {/* Skill Supply & Demand */}
            <section className="bg-white/90 backdrop-blur-sm rounded-2xl border border-slate-200/80 p-6 shadow-sm">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-blue-600" />
                  Cung - Cầu kỹ năng (Top 15)
                </h2>
                <div className="flex items-center gap-3 text-[11px] font-semibold">
                  <span className="flex items-center gap-1 text-blue-600">
                    <span className="w-2.5 h-2.5 rounded-sm bg-blue-500" /> Ứng viên
                  </span>
                  <span className="flex items-center gap-1 text-pink-600">
                    <span className="w-2.5 h-2.5 rounded-sm bg-pink-500" /> Tin tuyển dụng
                  </span>
                </div>
              </div>

              <div className="space-y-3">
                {m.skill_supply_demand.map((x) => (
                  <div key={x.skill} className="text-xs">
                    <div className="flex justify-between text-slate-700 font-medium mb-1">
                      <span>{x.skill}</span>
                      <span className="text-slate-500 text-[11px]">
                        {x.n_candidates} ứng viên vs {x.n_jobs} tin
                      </span>
                    </div>
                    {/* Blue bar: Candidates */}
                    <div className="h-2 bg-slate-100 rounded-full overflow-hidden mb-1">
                      <div
                        className="h-2 bg-blue-500 rounded-full transition-all"
                        style={{ width: `${(x.n_candidates / maxSd) * 100}%` }}
                      />
                    </div>
                    {/* Pink bar: Jobs */}
                    <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className="h-2 bg-gradient-to-r from-pink-500 to-rose-400 rounded-full transition-all"
                        style={{ width: `${(x.n_jobs / maxSd) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* Salary Median by Category */}
            <section className="bg-white/90 backdrop-blur-sm rounded-2xl border border-slate-200/80 p-6 shadow-sm">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-emerald-600" />
                  Lương trung vị theo ngành (triệu VND/tháng)
                </h2>
                <span className="text-[11px] text-slate-400">Dữ liệu VietJobs thật</span>
              </div>

              <div className="space-y-2.5">
                {m.salary_by_category.map((x) => {
                  const maxSal = m.salary_by_category[0]?.p50 || 1
                  return (
                    <div key={x.category} className="text-xs">
                      <div className="flex justify-between text-slate-700 font-medium mb-1">
                        <span className="truncate pr-2">{x.category}</span>
                        <span className="font-bold text-emerald-700 shrink-0">
                          {x.p50} tr <span className="text-[10px] text-slate-400 font-normal">(n={x.n})</span>
                        </span>
                      </div>
                      <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-2 bg-gradient-to-r from-emerald-400 to-teal-500 rounded-full transition-all"
                          style={{ width: `${(x.p50 / maxSal) * 100}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </section>
          </div>
        )}
      </main>
    </div>
  )
}
