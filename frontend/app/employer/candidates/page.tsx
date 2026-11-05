'use client'

import { Suspense, useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Header from '@/components/Header'
import SimBanner from '@/components/SimBanner'
import ScoreBadge from '@/components/ScoreBadge'
import { api, type Job } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { Filter, UserCheck, Briefcase, AlertCircle, CheckCircle2 } from 'lucide-react'

type Cands = Awaited<ReturnType<typeof api.getJobCandidates>>['candidates']
const STATUSES = ['applied', 'screening', 'interview', 'offer', 'rejected']
const LABEL: Record<string, string> = {
  applied: '1. Đã nộp',
  screening: '2. Sàng lọc',
  interview: '3. Phỏng vấn',
  offer: '4. Offer',
  rejected: 'Từ chối'
}

function Inner() {
  const { ready } = useAuth(['employer'])
  const router = useRouter()
  const jobParam = useSearchParams().get('job')
  const [jobs, setJobs] = useState<(Job & { n_applications: number })[]>([])
  const [cands, setCands] = useState<Cands>([])
  const [missing, setMissing] = useState('')
  const [err, setErr] = useState('')
  const [updatingId, setUpdatingId] = useState<number | null>(null)

  useEffect(() => {
    if (ready) {
      api.getEmployerJobs().then((r) => {
        setJobs(r)
        if (!jobParam) {
          const first = r.find((j) => j.n_applications > 0) || r[0]
          if (first) router.replace(`/employer/candidates?job=${first.id}`)
        }
      }).catch((e) => setErr(e.message))
    }
  }, [ready, jobParam, router])

  const loadC = () => {
    if (jobParam) {
      api.getJobCandidates(jobParam, missing || undefined)
        .then((d) => setCands(d.candidates))
        .catch((e) => setErr(e.message))
    }
  }

  useEffect(loadC, [jobParam, missing]) // eslint-disable-line react-hooks/exhaustive-deps

  const change = async (id: number, status: string) => {
    setUpdatingId(id)
    try {
      await api.updateApplication(id, status)
      loadC()
    } catch (e) {
      setErr((e as Error).message)
    } finally {
      setUpdatingId(null)
    }
  }

  const selectedJob = jobs.find((j) => String(j.id) === String(jobParam))

  return (
    <div className="min-h-screen bg-slate-50/60">
      <Header />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Xếp hạng ứng viên theo độ khớp
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 mt-1">
              Mô hình AI tự động xếp hạng ứng viên nộp hồ sơ theo Matching Score giảm dần
            </p>
          </div>

          {selectedJob && (
            <div className="px-3.5 py-1.5 rounded-xl bg-white border border-rose-200/80 text-xs font-semibold text-rose-700 shadow-2xs w-fit">
              {cands.length} ứng viên cho tin này
            </div>
          )}
        </div>

        {/* Filter & Selector Bar */}
        <div className="bg-white/90 backdrop-blur-sm rounded-2xl border border-rose-200/80 p-4 shadow-sm mb-6 flex flex-col sm:flex-row gap-3">
          <div className="flex-1">
            <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
              Chọn tin tuyển dụng
            </label>
            <select
              className="w-full px-3 py-2 border border-slate-200 rounded-xl bg-white text-xs sm:text-sm text-slate-900 font-medium focus:outline-none focus:ring-2 focus:ring-blue-300"
              value={jobParam || ''}
              onChange={(e) => router.push(`/employer/candidates?job=${e.target.value}`)}
            >
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title} ({j.n_applications} ứng viên)
                </option>
              ))}
            </select>
          </div>

          <div className="sm:w-72">
            <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
              Lọc ứng viên thiếu kỹ năng
            </label>
            <div className="relative">
              <Filter className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                className="w-full pl-8 pr-3 py-2 border border-slate-200 rounded-xl text-xs sm:text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-pink-300"
                placeholder="Vd: Docker, React..."
                value={missing}
                onChange={(e) => setMissing(e.target.value)}
              />
            </div>
          </div>
        </div>

        <SimBanner />

        {err && (
          <div className="bg-rose-50 border border-rose-200 text-rose-800 px-4 py-3 rounded-2xl mb-6 text-sm flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-rose-500 shrink-0" />
            <span>{err}</span>
          </div>
        )}

        {cands.length === 0 && (
          <div className="bg-white rounded-2xl border border-slate-200/80 p-12 text-center">
            <UserCheck className="w-10 h-10 text-slate-300 mx-auto mb-2" />
            <p className="text-sm font-semibold text-slate-700">Chưa có ứng viên nào cho vị trí này</p>
            <p className="text-xs text-slate-400 mt-1">Ứng viên nộp đơn sẽ xuất hiện tại đây và được xếp hạng tự động</p>
          </div>
        )}

        {/* Candidates List */}
        <div className="space-y-3.5">
          {cands.map((c, i) => (
            <div
              key={c.application_id}
              className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm hover:border-pink-300 transition duration-150"
            >
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <span
                    className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs shrink-0 ${
                      i === 0
                        ? 'bg-amber-100 text-amber-800'
                        : i === 1
                        ? 'bg-slate-100 text-slate-700'
                        : 'bg-slate-50 text-slate-400'
                    }`}
                  >
                    #{i + 1}
                  </span>

                  <div>
                    <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
                      {c.full_name}
                      <span className="text-xs font-normal text-slate-500">
                        · {c.exp_years} năm kinh nghiệm
                      </span>
                    </h3>
                    <p className="text-xs text-slate-600 mt-1 bg-slate-50 p-2.5 rounded-xl border border-slate-100 leading-relaxed">
                      {c.explanation}
                    </p>

                    <div className="mt-2.5 flex flex-wrap gap-2 text-xs">
                      {c.matched_skills?.length > 0 && (
                        <div className="flex items-center gap-1 flex-wrap">
                          <span className="font-semibold text-emerald-700">Khớp:</span>
                          {c.matched_skills.map((s) => (
                            <span key={s} className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-medium text-[11px] border border-emerald-100">
                              {s}
                            </span>
                          ))}
                        </div>
                      )}

                      {c.missing_skills.length > 0 && (
                        <div className="flex items-center gap-1 flex-wrap">
                          <span className="font-semibold text-rose-700">Thiếu:</span>
                          {c.missing_skills.map((s) => (
                            <span key={s} className="px-2 py-0.5 rounded bg-rose-50 text-rose-700 font-medium text-[11px] border border-rose-100">
                              {s}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Score & Stage Control */}
                <div className="flex sm:flex-col items-center sm:items-end justify-between gap-3 shrink-0 pt-2 sm:pt-0 border-t sm:border-0 border-slate-100">
                  <ScoreBadge score={c.score} level={c.level} />

                  <div className="text-right">
                    <label className="block text-[10px] text-slate-400 font-medium mb-1">Cập nhật vòng tuyển:</label>
                    <select
                      value={c.status}
                      disabled={updatingId === c.application_id}
                      onChange={(e) => change(c.application_id, e.target.value)}
                      className="px-2.5 py-1.5 border border-slate-200 rounded-xl text-xs font-semibold bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-300 shadow-2xs"
                    >
                      {STATUSES.map((s) => (
                        <option key={s} value={s}>
                          {LABEL[s]}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}

export default function Page() {
  return (
    <Suspense>
      <Inner />
    </Suspense>
  )
}
