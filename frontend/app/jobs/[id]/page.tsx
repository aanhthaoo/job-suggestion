'use client'

import { useEffect, useState, Suspense } from 'react'
import { useParams, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import Header from '@/components/Header'
import ScoreBadge from '@/components/ScoreBadge'
import { api, type CvSuggestion, type Job, type MatchExplain } from '@/lib/api'
import { formatDate, formatSalary } from '@/lib/utils'
import {
  MapPin,
  Clock,
  Briefcase,
  Globe,
  GraduationCap,
  Calendar,
  Gift,
  CheckCircle2,
  Sparkles,
  Zap
} from 'lucide-react'

const COMP_LABEL: Record<string, string> = {
  skill_cov: 'Kỹ năng',
  text_sim: 'Nội dung CV-JD',
  exp_fit: 'Kinh nghiệm',
  edu_fit: 'Học vấn',
  loc_fit: 'Địa điểm',
  salary_fit: 'Lương',
  level_fit: 'Cấp bậc',
}

function JobDetail() {
  const { id } = useParams<{ id: string }>()
  const from = useSearchParams().get('from')
  const [job, setJob] = useState<Job | null>(null)
  const [match, setMatch] = useState<MatchExplain | null>(null)
  const [salary, setSalary] = useState<{ segment: { p25: number; p50: number; p75: number; n: number }; estimate: number } | null>(null)
  const [sug, setSug] = useState<CvSuggestion | null>(null)
  const [role, setRole] = useState<string | null>(null)
  const [msg, setMsg] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    try { setRole(JSON.parse(localStorage.getItem('user') || 'null')?.role ?? null) } catch { /* guest */ }
    api.getJob(id).then(setJob).catch((e) => setMsg(e.message))
    api.getSalary(id).then(setSalary).catch(() => {})
  }, [id])

  useEffect(() => {
    if (role === 'candidate') api.getMatch(id).then(setMatch).catch(() => {})
  }, [role, id])

  const apply = async () => {
    setBusy(true)
    try {
      const r = await api.apply(Number(id), from === 'recommend' ? 'recommend' : 'search')
      setMsg(`Đã ứng tuyển (Matching Score ${r.match_score !== null ? Math.round(r.match_score * 100) + '%' : 'n/a'})`)
    } catch (e) { setMsg((e as Error).message) } finally { setBusy(false) }
  }
  const suggest = async () => {
    setBusy(true); setMsg('')
    try { setSug(await api.suggestCV(id)) } catch (e) { setMsg((e as Error).message) } finally { setBusy(false) }
  }

  if (!job) return <div className="min-h-screen bg-gray-50"><Header /><p className="p-8 text-gray-600">{msg || 'Đang tải thông tin...'}</p></div>

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-6xl mx-auto px-4 py-8 grid md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          {/* Main Job Overview Card */}
          <div className="bg-white border rounded-xl p-6 shadow-sm">
            <div className="flex justify-between items-start gap-4">
              <div>
                <span className="inline-block px-2.5 py-0.5 text-xs font-semibold rounded bg-blue-50 text-blue-700 mb-2">
                  {job.category || 'Việc làm'}
                </span>
                <h1 className="text-2xl font-bold text-gray-900 leading-tight">{job.title}</h1>
                <p className="text-gray-600 text-base mt-1 font-medium">{job.company_name}</p>
              </div>
              {match && <ScoreBadge score={match.score} level={match.level} />}
            </div>

            {/* Quick Info Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mt-5 pt-4 border-t border-gray-100 text-sm">
              <div className="flex items-center text-gray-700">
                <span className="w-8 h-8 rounded-lg bg-green-50 text-green-700 flex items-center justify-center mr-2.5 shrink-0">💵</span>
                <div>
                  <p className="text-xs text-gray-500">Mức lương</p>
                  <p className="font-semibold text-gray-900">{formatSalary(job.salary_min, job.salary_max)}</p>
                </div>
              </div>

              <div className="flex items-center text-gray-700">
                <span className="w-8 h-8 rounded-lg bg-blue-50 text-blue-700 flex items-center justify-center mr-2.5 shrink-0">
                  <MapPin className="w-4 h-4" />
                </span>
                <div>
                  <p className="text-xs text-gray-500">Địa điểm</p>
                  <p className="font-semibold text-gray-900">{job.location || 'Toàn quốc'}</p>
                </div>
              </div>

              <div className="flex items-center text-gray-700">
                <span className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-700 flex items-center justify-center mr-2.5 shrink-0">
                  <Briefcase className="w-4 h-4" />
                </span>
                <div>
                  <p className="text-xs text-gray-500">Hình thức / Cấp bậc</p>
                  <p className="font-semibold text-gray-900">{job.contract_type || 'Toàn thời gian'} · {job.level || 'Junior'}</p>
                </div>
              </div>

              <div className="flex items-center text-gray-700">
                <span className="w-8 h-8 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center mr-2.5 shrink-0">
                  <Clock className="w-4 h-4" />
                </span>
                <div>
                  <p className="text-xs text-gray-500">Giờ làm việc</p>
                  <p className="font-semibold text-gray-900">{job.working_hours || 'Giờ hành chính'}</p>
                </div>
              </div>

              <div className="flex items-center text-gray-700">
                <span className="w-8 h-8 rounded-lg bg-purple-50 text-purple-700 flex items-center justify-center mr-2.5 shrink-0">
                  <GraduationCap className="w-4 h-4" />
                </span>
                <div>
                  <p className="text-xs text-gray-500">Kinh nghiệm & Học vấn</p>
                  <p className="font-semibold text-gray-900">{job.exp_years_min || 0} năm · {job.education || 'Đại học'}</p>
                </div>
              </div>

              {job.languages_required && (
                <div className="flex items-center text-gray-700">
                  <span className="w-8 h-8 rounded-lg bg-teal-50 text-teal-700 flex items-center justify-center mr-2.5 shrink-0">
                    <Globe className="w-4 h-4" />
                  </span>
                  <div>
                    <p className="text-xs text-gray-500">Ngoại ngữ</p>
                    <p className="font-semibold text-gray-900">{job.languages_required}</p>
                  </div>
                </div>
              )}

              <div className="flex items-center text-gray-700">
                <span className="w-8 h-8 rounded-lg bg-gray-50 text-gray-600 flex items-center justify-center mr-2.5 shrink-0">
                  <Calendar className="w-4 h-4" />
                </span>
                <div>
                  <p className="text-xs text-gray-500">Ngày đăng</p>
                  <p className="font-semibold text-gray-900">{formatDate(job.posted_at)}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Benefits Card */}
          {job.benefits && (
            <div className="bg-gradient-to-br from-emerald-50/50 to-white border border-emerald-200/70 rounded-xl p-6 shadow-sm">
              <div className="flex items-center gap-2 mb-3">
                <span className="p-1.5 bg-emerald-100 text-emerald-800 rounded-lg">
                  <Gift className="w-5 h-5" />
                </span>
                <h2 className="text-lg font-bold text-gray-900">Quyền lợi & Chế độ đãi ngộ</h2>
              </div>
              <div className="text-gray-700 text-sm whitespace-pre-line leading-relaxed space-y-1.5 pl-1">
                {job.benefits}
              </div>
            </div>
          )}

          {/* Job Description Card */}
          <div className="bg-white border rounded-xl p-6 shadow-sm space-y-3">
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <span className="w-2 h-5 bg-blue-600 rounded-sm"></span>
              Mô tả công việc
            </h2>
            <div className="whitespace-pre-line text-gray-700 text-sm leading-relaxed pl-3">
              {job.description}
            </div>
          </div>

          {/* Requirements Card */}
          {job.requirements && (
            <div className="bg-white border rounded-xl p-6 shadow-sm space-y-3">
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <span className="w-2 h-5 bg-blue-600 rounded-sm"></span>
                Yêu cầu ứng viên
              </h2>
              <div className="whitespace-pre-line text-gray-700 text-sm leading-relaxed pl-3">
                {job.requirements}
              </div>
            </div>
          )}

          {/* Skills Details */}
          <div className="bg-white border rounded-xl p-6 shadow-sm space-y-4">
            <h2 className="text-lg font-bold text-gray-900">Kỹ năng liên quan</h2>
            
            {/* Technical Skills */}
            {job.skills_required && job.skills_required.length > 0 && (
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">Kỹ năng chuyên môn kỹ thuật</p>
                <div className="flex flex-wrap gap-2">
                  {job.skills_required.map((s) => (
                    <span key={s} className="px-3 py-1 bg-blue-50 text-blue-800 font-medium rounded-lg text-xs border border-blue-100">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Soft Skills */}
            {job.soft_skills && job.soft_skills.length > 0 && (
              <div className="pt-2">
                <p className="text-xs font-semibold uppercase tracking-wider text-purple-700 mb-2">Kỹ năng mềm yêu cầu</p>
                <div className="flex flex-wrap gap-2">
                  {job.soft_skills.map((s) => (
                    <span key={s} className="px-3 py-1 bg-purple-50 text-purple-800 font-medium rounded-lg text-xs border border-purple-100">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar Actions & AI Insights */}
        <aside className="space-y-5">
          {role === 'candidate' && (
            <div className="bg-white border rounded-xl p-5 shadow-sm space-y-3">
              <button
                onClick={apply}
                disabled={busy}
                className="w-full bg-blue-600 text-white font-medium py-2.5 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition shadow-sm"
              >
                Ứng tuyển ngay
              </button>
              <button
                onClick={suggest}
                disabled={busy}
                className="w-full border border-blue-600 text-blue-700 font-medium py-2 rounded-lg hover:bg-blue-50 disabled:opacity-50 transition flex items-center justify-center gap-1.5"
              >
                <Sparkles className="w-4 h-4 text-blue-600" />
                Gợi ý sửa CV theo tin (AI)
              </button>
              {msg && <p className="text-sm text-green-700 bg-green-50 p-2.5 rounded border border-green-200">{msg}</p>}
            </div>
          )}

          {!role && (
            <div className="bg-white border rounded-xl p-5 text-sm shadow-sm">
              <p className="text-gray-600 mb-2">Bạn đang xem tin với tư cách Khách.</p>
              <Link className="text-blue-600 font-semibold hover:underline" href="/auth/login">
                Đăng nhập
              </Link>{' '}
              để xem điểm khớp AI, phân tích hồ sơ và nộp đơn ứng tuyển.
            </div>
          )}

          {/* AI Match Explanation */}
          {match && (
            <div className="bg-white border rounded-xl p-5 shadow-sm">
              <h2 className="font-bold text-gray-900 mb-2 flex items-center gap-1.5">
                <Zap className="w-4 h-4 text-amber-500" />
                Vì sao khớp?
              </h2>
              <p className="text-xs text-gray-700 mb-3 bg-gray-50 p-2 rounded leading-relaxed">{match.explanation}</p>
              
              <div className="space-y-2 mt-3">
                {Object.entries(match.components).map(([k, v]) => (
                  <div key={k}>
                    <div className="flex justify-between text-xs text-gray-600 mb-1">
                      <span>{COMP_LABEL[k] || k}</span>
                      <span className="font-medium text-gray-900">{Math.round(v * 100)}%</span>
                    </div>
                    <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div className="h-1.5 bg-blue-500 rounded-full transition-all" style={{ width: `${v * 100}%` }} />
                    </div>
                  </div>
                ))}
              </div>

              {match.missing_skills.length > 0 && (
                <div className="mt-4 pt-3 border-t border-gray-100 text-xs text-gray-700">
                  <b className="text-red-700">Kỹ năng còn thiếu:</b>{' '}
                  <span className="text-gray-800">{match.missing_skills.join(', ')}</span>
                </div>
              )}
            </div>
          )}

          {/* Salary Estimate */}
          {salary && (
            <div className="bg-white border rounded-xl p-5 text-sm shadow-sm">
              <h2 className="font-bold text-gray-900 mb-1">Ước lượng thị trường</h2>
              <p className="text-gray-900 font-semibold text-lg text-emerald-600">
                {salary.estimate} triệu <span className="text-xs font-normal text-gray-500">/tháng</span>
              </p>
              <p className="text-xs text-gray-600 mt-1">
                Dải thực tế cùng phân khúc: <b>{salary.segment.p25} - {salary.segment.p75} triệu</b> (mẫu {salary.segment.n} tin tuyển dụng)
              </p>
            </div>
          )}

          {/* AI CV Suggestion */}
          {sug && (
            <div className="bg-white border rounded-xl p-5 text-sm shadow-sm space-y-3">
              <div className="flex justify-between items-center">
                <h2 className="font-bold text-gray-900 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-purple-600" />
                  Gợi ý tối ưu CV
                </h2>
                <span className={`text-[10px] uppercase font-semibold px-2 py-0.5 rounded ${sug.source === 'gemini' ? 'bg-purple-100 text-purple-800' : 'bg-gray-100 text-gray-700'}`}>
                  {sug.source === 'gemini' ? 'Gemini AI' : 'Offline'}
                </span>
              </div>
              <p className="text-xs text-gray-700 bg-purple-50/50 p-2 rounded leading-relaxed">{sug.content.summary}</p>
              
              {sug.content.add_keywords.length > 0 && (
                <div className="text-xs">
                  <p className="font-semibold text-gray-800 mb-1">Từ khóa nên thêm vào CV:</p>
                  <div className="flex flex-wrap gap-1">
                    {sug.content.add_keywords.map((k) => (
                      <span key={k} className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-[11px] font-mono">
                        {k}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {sug.content.rewrite_bullets.length > 0 && (
                <div className="text-xs">
                  <p className="font-semibold text-gray-800 mb-1">Gợi ý viết lại thành tích:</p>
                  <ul className="list-disc pl-4 space-y-1 text-gray-600">
                    {sug.content.rewrite_bullets.map((b, i) => <li key={i}>{b}</li>)}
                  </ul>
                </div>
              )}

              {sug.content.priority_fixes.length > 0 && (
                <div className="text-xs pt-1">
                  <p className="font-semibold text-amber-800 mb-1">Ưu tiên điều chỉnh:</p>
                  <ul className="list-disc pl-4 space-y-1 text-amber-900">
                    {sug.content.priority_fixes.map((b, i) => <li key={i}>{b}</li>)}
                  </ul>
                </div>
              )}
            </div>
          )}
        </aside>
      </main>
    </div>
  )
}

export default function Page() {
  return (
    <Suspense>
      <JobDetail />
    </Suspense>
  )
}
