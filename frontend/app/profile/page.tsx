'use client'

import { useEffect, useState } from 'react'
import Header from '@/components/Header'
import { api, type Health, type Profile, type ParsedCvData } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import {
  User,
  UploadCloud,
  FileCheck,
  CheckCircle2,
  AlertTriangle,
  Award,
  Sparkles,
  Zap,
  Briefcase,
  GraduationCap,
  Mail,
  Phone,
  MapPin,
  FileText,
  Layers,
  Globe,
  Printer,
  TrendingUp,
  BookmarkCheck,
  Code
} from 'lucide-react'

const RULE_LABEL: Record<string, [string, number]> = {
  sections: ['Đủ các mục chính', 20],
  contact: ['Thông tin liên hệ', 15],
  skills: ['Kỹ năng chuyên môn', 15],
  quantified: ['Số liệu định lượng', 20],
  length: ['Độ dài văn bản', 15],
  cliche: ['Tránh từ sáo rỗng', 15],
}

export default function ProfilePage() {
  const { ready } = useAuth(['candidate'])
  const [p, setP] = useState<Profile | null>(null)
  const [activeTab, setActiveTab] = useState<'preview' | 'health' | 'edit'>('preview')
  const [form, setForm] = useState({
    full_name: '',
    major: '',
    exp_years: '',
    education: '',
    location: '',
    expected_salary: '',
    skills: '',
  })
  const [health, setHealth] = useState<Health | null>(null)
  const [parsedCv, setParsedCv] = useState<ParsedCvData | null>(null)
  const [msg, setMsg] = useState('')
  const [busy, setBusy] = useState(false)
  const [presetLoading, setPresetLoading] = useState<string | null>(null)

  const load = (prof: Profile) => {
    setP(prof)
    setForm({
      full_name: prof.full_name || '',
      major: prof.major || '',
      exp_years: prof.exp_years ? String(prof.exp_years) : '',
      education: prof.education || '',
      location: prof.location || '',
      expected_salary: prof.expected_salary ? String(prof.expected_salary) : '',
      skills: prof.skills?.filter((s) => s.source === 'manual').map((s) => s.name).join(', ') || '',
    })

    if (prof.latest_cv) {
      setHealth(prof.latest_cv.health_issues_json || null)
      if (prof.latest_cv.parsed_json) {
        setParsedCv(prof.latest_cv.parsed_json)
      } else {
        setParsedCv(null)
      }
    } else {
      setHealth(null)
      setParsedCv(null)
    }
  }

  useEffect(() => {
    if (ready) {
      api.getProfile().then(load).catch((e) => setMsg(e.message))
    }
  }, [ready])

  const save = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setMsg('')
    try {
      const prof = await api.updateProfile({
        full_name: form.full_name,
        major: form.major || undefined,
        education: form.education || undefined,
        location: form.location || undefined,
        exp_years: form.exp_years ? Number(form.exp_years) : undefined,
        expected_salary: form.expected_salary ? Number(form.expected_salary) : undefined,
        skills: form.skills.split(',').map((s) => s.trim()).filter(Boolean),
      })
      load(prof)
      setMsg('Đã lưu thông tin hồ sơ và tính toán lại Matching Score với 3.500+ việc làm!')
    } catch (err) {
      setMsg((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const upload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (!f) return
    setBusy(true)
    setMsg('Đang phân tích CV và chấm điểm sức khỏe theo 6 quy tắc định lượng...')
    try {
      const r = await api.uploadCV(f)
      setHealth(r.health)
      setMsg(`Đã trích xuất ${r.parsed.skills.length} kỹ năng, ${r.parsed.experience_years} năm kinh nghiệm và cập nhật ${r.matches_updated} việc làm.`)
      const fresh = await api.getProfile()
      load(fresh)
    } catch (err) {
      setMsg((err as Error).message)
    } finally {
      setBusy(false)
      e.target.value = ''
    }
  }

  const switchPreset = async (preset: 'realistic' | 'perfect' | 'needs_work') => {
    setPresetLoading(preset)
    setMsg('')
    try {
      const res = await api.loadDemoPreset(preset)
      setHealth(res.health)
      setParsedCv(res.parsed)
      const fresh = await api.getProfile()
      load(fresh)
      setMsg(`Đã chuyển sang mẫu ${preset === 'realistic' ? 'CV Thực tế (78 điểm)' : preset === 'perfect' ? 'CV Xuất sắc (100 điểm)' : 'CV Cần cải thiện (51 điểm)'} và cập nhật điểm khớp AI!`)
    } catch (err) {
      setMsg((err as Error).message)
    } finally {
      setPresetLoading(null)
    }
  }

  const inp = 'w-full px-3.5 py-2.5 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 bg-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-300 focus:border-blue-400 transition shadow-2xs'
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [k]: e.target.value })

  // Correct derived CV data: NO hardcoded demo fallbacks for new users
  const hasCv = Boolean(p?.latest_cv)
  const candidateName = p?.full_name || parsedCv?.full_name || 'Ứng viên'
  const candidateTitle = parsedCv?.title || (p?.major ? `${p.major} Specialist` : (hasCv ? 'Chuyên viên kỹ thuật' : 'Chưa cập nhật chức danh'))
  const candidateEmail = p?.email || parsedCv?.contacts?.email || ''
  const candidatePhone = parsedCv?.contacts?.phone || ''
  const candidateLocation = p?.location || parsedCv?.contacts?.address || ''
  const candidateGithub = parsedCv?.contacts?.github || ''
  const candidateLinkedin = parsedCv?.contacts?.linkedin || ''
  const candidateSummary = parsedCv?.summary || (parsedCv?.sections?.summary) || ''

  return (
    <div className="min-h-screen bg-slate-50/60 pb-16">
      <Header />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Top Header Card */}
        <div className="bg-white/80 backdrop-blur-md rounded-3xl border border-rose-100 p-6 sm:p-8 shadow-sm mb-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-pink-50 border border-pink-200 text-pink-700 text-xs font-semibold">
                <Sparkles className="w-3.5 h-3.5 text-pink-500" />
                <span>Hồ sơ & CV Ứng viên</span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                {candidateName}
              </h1>
              <p className="text-xs sm:text-sm text-slate-600 max-w-2xl leading-relaxed">
                {hasCv
                  ? 'Trình bày chuẩn mẫu CV chuyên nghiệp, tự động bóc tách kỹ năng, đo lường điểm sức khỏe CV theo 6 quy tắc định lượng và đồng bộ hóa Matching Engine với 3.500+ tin tuyển dụng.'
                  : 'Tài khoản của bạn chưa nộp CV. Hãy tải lên CV (PDF/DOCX) để hệ thống bóc tách thông tin và đề xuất việc làm chuẩn xác.'}
              </p>
            </div>

            {/* Health Score Badge & Preset Selector */}
            <div className="flex flex-col sm:flex-row md:flex-col lg:flex-row items-start sm:items-center gap-4 bg-gradient-to-br from-pink-50/50 via-white to-blue-50/50 p-4 rounded-2xl border border-rose-100/80 shadow-2xs">
              <div className="text-center sm:text-left pr-3 sm:border-r border-rose-100">
                <span className="block text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  Điểm Sức Khỏe CV
                </span>
                {hasCv && health ? (
                  <>
                    <div className="flex items-baseline gap-1.5 mt-0.5">
                      <span className={`text-3xl font-black ${
                        health.score >= 80 ? 'text-emerald-600' : health.score >= 60 ? 'text-blue-600' : 'text-amber-600'
                      }`}>
                        {Math.round(health.score)}
                      </span>
                      <span className="text-xs text-slate-400 font-semibold">/100</span>
                    </div>
                    <span className="text-[11px] text-slate-500 block">
                      {health.score >= 80 ? 'Đạt chuẩn xuất sắc' : health.score >= 60 ? 'Chất lượng khá tốt' : 'Cần cải thiện'}
                    </span>
                  </>
                ) : (
                  <>
                    <div className="flex items-baseline gap-1.5 mt-0.5">
                      <span className="text-3xl font-black text-slate-400">--</span>
                      <span className="text-xs text-slate-400 font-semibold">/100</span>
                    </div>
                    <span className="text-[11px] text-amber-600 font-medium block">
                      Chưa nộp CV
                    </span>
                  </>
                )}
              </div>

              {/* Demo Presets Switcher */}
              <div className="space-y-1">
                <span className="text-[11px] font-medium text-slate-600 block">
                  Đổi mẫu CV thử nghiệm:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  <button
                    type="button"
                    onClick={() => switchPreset('realistic')}
                    disabled={presetLoading !== null}
                    className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 transition disabled:opacity-50"
                    title="CV thực tế đạt 78 điểm, có 2 điểm cần cải thiện"
                  >
                    {presetLoading === 'realistic' ? 'Đang tải...' : '⚡ Thực tế (78đ)'}
                  </button>
                  <button
                    type="button"
                    onClick={() => switchPreset('perfect')}
                    disabled={presetLoading !== null}
                    className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-pink-50 hover:bg-pink-100 text-pink-700 border border-pink-200 transition disabled:opacity-50"
                    title="CV hoàn hảo 100 điểm, không có lỗi"
                  >
                    {presetLoading === 'perfect' ? 'Đang tải...' : '⭐ Xuất sắc (100đ)'}
                  </button>
                  <button
                    type="button"
                    onClick={() => switchPreset('needs_work')}
                    disabled={presetLoading !== null}
                    className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-700 border border-amber-200 transition disabled:opacity-50"
                    title="CV ngắn, thiếu số liệu định lượng (51 điểm)"
                  >
                    {presetLoading === 'needs_work' ? 'Đang tải...' : '⚠️ Cần sửa (51đ)'}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-2 mt-6 pt-4 border-t border-slate-100">
            <button
              onClick={() => setActiveTab('preview')}
              className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition flex items-center gap-2 ${
                activeTab === 'preview'
                  ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-sm shadow-blue-500/20'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
              }`}
            >
              <FileText className="w-4 h-4" />
              <span>Bản xem CV Chuẩn</span>
            </button>
            <button
              onClick={() => setActiveTab('health')}
              className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition flex items-center gap-2 ${
                activeTab === 'health'
                  ? 'bg-gradient-to-r from-pink-500 to-rose-600 text-white shadow-sm shadow-pink-500/20'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
              }`}
            >
              <Sparkles className="w-4 h-4" />
              <span>Chẩn đoán Sức khỏe CV {hasCv && health ? `(${Math.round(health.score)}đ)` : ''}</span>
            </button>
            <button
              onClick={() => setActiveTab('edit')}
              className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition flex items-center gap-2 ${
                activeTab === 'edit'
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
              }`}
            >
              <User className="w-4 h-4" />
              <span>Chỉnh sửa Thông tin</span>
            </button>
          </div>
        </div>

        {/* Global Notification */}
        {msg && (
          <div className="mb-6 p-3.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-2xl text-xs sm:text-sm font-medium flex items-center justify-between gap-3 shadow-2xs">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>{msg}</span>
            </div>
            <button onClick={() => setMsg('')} className="text-emerald-700 hover:text-emerald-900 text-xs">
              Đóng
            </button>
          </div>
        )}

        {/* TAB 1: Professional CV View (Full Resume Layout or Clean Empty State) */}
        {activeTab === 'preview' && (
          <div className="space-y-6">
            {!hasCv ? (
              /* EMPTY STATE: FOR NEWLY REGISTERED USERS WITH NO CV */
              <div className="bg-white rounded-3xl border-2 border-dashed border-rose-200/90 p-8 sm:p-14 text-center shadow-sm space-y-6">
                <div className="w-16 h-16 rounded-3xl bg-gradient-to-tr from-pink-100 to-blue-100 flex items-center justify-center text-pink-600 mx-auto shadow-inner">
                  <FileText className="w-8 h-8 text-pink-600" />
                </div>

                <div className="max-w-md mx-auto space-y-2">
                  <h2 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
                    Hồ sơ mới — Bạn chưa có bản CV nào
                  </h2>
                  <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                    Chào mừng <strong>{candidateName}</strong>! Hãy tải lên file CV đầu tiên để hệ thống AI tự động trích xuất kỹ năng, kinh nghiệm, chấm điểm sức khỏe CV và xếp hạng việc làm phù hợp.
                  </p>
                </div>

                <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
                  <label className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-2xl text-xs sm:text-sm font-bold cursor-pointer shadow-md shadow-blue-500/20 transition hover:scale-102">
                    <UploadCloud className="w-4 h-4" />
                    <span>Tải lên file CV (PDF / DOCX)</span>
                    <input type="file" accept=".pdf,.docx" onChange={upload} disabled={busy} className="hidden" />
                  </label>

                  <button
                    type="button"
                    onClick={() => switchPreset('realistic')}
                    disabled={presetLoading !== null}
                    className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-3 bg-white border border-rose-200 hover:border-pink-300 rounded-2xl text-xs sm:text-sm font-semibold text-pink-700 hover:bg-pink-50/50 shadow-2xs transition"
                  >
                    <Sparkles className="w-4 h-4 text-pink-500" />
                    <span>{presetLoading === 'realistic' ? 'Đang nạp...' : '⚡ Nạp thử CV Demo (78đ)'}</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setActiveTab('edit')}
                    className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-4 py-3 bg-slate-100 hover:bg-slate-200 rounded-2xl text-xs sm:text-sm font-medium text-slate-700 transition"
                  >
                    <User className="w-4 h-4 text-slate-500" />
                    <span>Tự điền thông tin</span>
                  </button>
                </div>

                <div className="pt-8 border-t border-slate-100 max-w-3xl mx-auto grid grid-cols-1 sm:grid-cols-3 gap-3 text-left">
                  <div className="p-4 rounded-2xl bg-slate-50/70 border border-slate-100 space-y-1">
                    <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                      <Zap className="w-3.5 h-3.5 text-blue-600" />
                      Tự động trích xuất
                    </span>
                    <p className="text-[11px] text-slate-500 leading-relaxed">
                      Nhận diện hơn 100+ kỹ năng công nghệ và số năm kinh nghiệm từ file CV của bạn.
                    </p>
                  </div>

                  <div className="p-4 rounded-2xl bg-slate-50/70 border border-slate-100 space-y-1">
                    <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-pink-600" />
                      Chấm điểm 6 quy tắc
                    </span>
                    <p className="text-[11px] text-slate-500 leading-relaxed">
                      Đo lường định lượng minh bạch: độ dài, số liệu định lượng, cấu trúc đề mục, tránh từ sáo rỗng.
                    </p>
                  </div>

                  <div className="p-4 rounded-2xl bg-slate-50/70 border border-slate-100 space-y-1">
                    <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                      <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
                      Matching AI tức thì
                    </span>
                    <p className="text-[11px] text-slate-500 leading-relaxed">
                      Đồng bộ Matching Engine xếp hạng độ phù hợp với 3.500+ việc làm ngay lập tức.
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              /* REAL RESUME PAPER CARD: WHEN CANDIDATE HAS CV */
              <>
                {/* Action Bar for CV Print / Upload */}
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white/70 backdrop-blur-sm p-4 rounded-2xl border border-rose-100 text-xs text-slate-600">
                  <div className="flex items-center gap-2">
                    <FileCheck className="w-4 h-4 text-emerald-600" />
                    <span>
                      Đang hiển thị bản CV: <strong className="text-slate-900 font-semibold">{p?.latest_cv?.filename || 'Bản CV đã nộp'}</strong>
                    </span>
                    <span className="text-slate-400">·</span>
                    <span className="text-slate-500">Cập nhật: {p?.latest_cv?.created_at ? new Date(p.latest_cv.created_at).toLocaleDateString('vi-VN') : 'Gần đây'}</span>
                  </div>

                  <div className="flex items-center gap-2 w-full sm:w-auto">
                    <button
                      type="button"
                      onClick={() => window.print()}
                      className="flex-1 sm:flex-none inline-flex items-center justify-center gap-1.5 px-3 py-1.5 bg-white border border-slate-200 hover:border-pink-300 rounded-xl font-medium text-slate-700 hover:bg-slate-50 transition shadow-2xs"
                    >
                      <Printer className="w-3.5 h-3.5 text-slate-500" />
                      <span>In / Xuất PDF</span>
                    </button>
                    <label className="flex-1 sm:flex-none inline-flex items-center justify-center gap-1.5 px-3.5 py-1.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl font-semibold cursor-pointer shadow-sm transition">
                      <UploadCloud className="w-3.5 h-3.5" />
                      <span>Tải lên CV khác</span>
                      <input type="file" accept=".pdf,.docx" onChange={upload} disabled={busy} className="hidden" />
                    </label>
                  </div>
                </div>

                {/* RESUME PAPER CARD */}
                <div className="bg-white rounded-3xl border border-rose-200/90 shadow-lg shadow-pink-500/5 p-6 sm:p-10 text-slate-800 space-y-8">
                  {/* CV HEADER */}
                  <div className="pb-6 border-b border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <div className="space-y-2">
                      <div className="flex items-center gap-3">
                        <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-pink-500 via-rose-500 to-blue-600 flex items-center justify-center text-white text-xl font-black shadow-md shadow-pink-500/20">
                          {candidateName.charAt(0)}
                        </div>
                        <div>
                          <h2 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
                            {candidateName}
                          </h2>
                          <p className="text-sm sm:text-base font-semibold text-blue-600">
                            {candidateTitle}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Contact Badges */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-slate-600">
                      {candidateEmail && (
                        <div className="flex items-center gap-2 p-1.5 rounded-lg bg-slate-50 border border-slate-100">
                          <Mail className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                          <span className="truncate">{candidateEmail}</span>
                        </div>
                      )}
                      {candidatePhone && (
                        <div className="flex items-center gap-2 p-1.5 rounded-lg bg-slate-50 border border-slate-100">
                          <Phone className="w-3.5 h-3.5 text-rose-600 shrink-0" />
                          <span>{candidatePhone}</span>
                        </div>
                      )}
                      {candidateLocation && (
                        <div className="flex items-center gap-2 p-1.5 rounded-lg bg-slate-50 border border-slate-100">
                          <MapPin className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                          <span>{candidateLocation}</span>
                        </div>
                      )}
                      {candidateGithub && (
                        <div className="flex items-center gap-2 p-1.5 rounded-lg bg-slate-50 border border-slate-100">
                          <svg className="w-3.5 h-3.5 text-slate-700 shrink-0" fill="currentColor" viewBox="0 0 24 24">
                            <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
                          </svg>
                          <span className="truncate">{candidateGithub}</span>
                        </div>
                      )}
                      {candidateLinkedin && (
                        <div className="flex items-center gap-2 p-1.5 rounded-lg bg-slate-50 border border-slate-100 sm:col-span-2">
                          <svg className="w-3.5 h-3.5 text-blue-700 shrink-0" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z" />
                          </svg>
                          <span className="truncate">{candidateLinkedin}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* SUMMARY / OBJECTIVE */}
                  {candidateSummary && (
                    <div>
                      <h3 className="text-xs font-bold uppercase tracking-wider text-pink-700 flex items-center gap-2 mb-2.5">
                        <BookmarkCheck className="w-4 h-4 text-pink-600" />
                        Mục tiêu nghề nghiệp & Tóm tắt bản thân
                      </h3>
                      <p className="text-xs sm:text-sm text-slate-700 leading-relaxed bg-pink-50/20 p-4 rounded-2xl border border-pink-100/60">
                        {candidateSummary}
                      </p>
                    </div>
                  )}

                  {/* TWO COLUMN BODY */}
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                    {/* LEFT: WORK EXPERIENCE & PROJECTS (7 cols) */}
                    <div className="lg:col-span-7 space-y-7">
                      {/* WORK EXPERIENCE */}
                      <div>
                        <h3 className="text-xs font-bold uppercase tracking-wider text-blue-700 flex items-center gap-2 mb-4 pb-1 border-b border-blue-100">
                          <Briefcase className="w-4 h-4 text-blue-600" />
                          Kinh nghiệm làm việc thực tế
                        </h3>

                        {Array.isArray(parsedCv?.experience) && parsedCv.experience.length > 0 ? (
                          <div className="space-y-5">
                            {parsedCv.experience.map((exp: any, idx: number) => {
                              if (typeof exp === 'string') {
                                return (
                                  <div key={idx} className="relative pl-5 border-l-2 border-blue-200 space-y-1">
                                    <div className="absolute -left-[7px] top-1 w-3 h-3 rounded-full bg-blue-600 ring-4 ring-blue-100" />
                                    <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-line">{exp}</p>
                                  </div>
                                )
                              }
                              return (
                                <div key={idx} className="relative pl-5 border-l-2 border-blue-200 space-y-2">
                                  <div className="absolute -left-[7px] top-1 w-3 h-3 rounded-full bg-blue-600 ring-4 ring-blue-100" />
                                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                                    <h4 className="text-sm font-bold text-slate-900">{exp.position || 'Chuyên viên kỹ thuật'}</h4>
                                    <span className="text-[11px] font-semibold text-blue-700 px-2 py-0.5 rounded-md bg-blue-50 border border-blue-100">
                                      {exp.period || 'Gần đây'}
                                    </span>
                                  </div>
                                  {exp.company && (
                                    <p className="text-xs font-medium text-slate-600">
                                      {exp.company} {exp.location ? `· ${exp.location}` : ''}
                                    </p>
                                  )}
                                  {Array.isArray(exp.responsibilities) && exp.responsibilities.length > 0 && (
                                    <ul className="space-y-1.5 text-xs text-slate-700 pt-1">
                                      {exp.responsibilities.map((r: string, ridx: number) => (
                                        <li key={ridx} className="flex items-start gap-1.5">
                                          <span className="text-blue-500 font-bold">•</span>
                                          <span>{r}</span>
                                        </li>
                                      ))}
                                    </ul>
                                  )}
                                </div>
                              )
                            })}
                          </div>
                        ) : parsedCv?.sections?.experience ? (
                          <div className="p-4 rounded-2xl bg-blue-50/20 border border-blue-100/70 text-xs text-slate-700 whitespace-pre-line leading-relaxed">
                            {parsedCv.sections.experience}
                          </div>
                        ) : (
                          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 text-xs text-slate-500 italic">
                            Chưa ghi nhận kinh nghiệm làm việc trong file CV này.
                          </div>
                        )}
                      </div>

                      {/* PROJECTS */}
                      <div>
                        <h3 className="text-xs font-bold uppercase tracking-wider text-pink-700 flex items-center gap-2 mb-4 pb-1 border-b border-pink-100">
                          <Code className="w-4 h-4 text-pink-600" />
                          Dự án tiêu biểu
                        </h3>

                        {Array.isArray(parsedCv?.projects) && parsedCv.projects.length > 0 ? (
                          <div className="space-y-3.5">
                            {parsedCv.projects.map((proj: any, idx: number) => (
                              <div key={idx} className="p-4 rounded-2xl bg-gradient-to-br from-pink-50/20 to-blue-50/20 border border-slate-200/80 space-y-2">
                                <div className="flex items-baseline justify-between gap-2">
                                  <h4 className="text-xs sm:text-sm font-bold text-slate-900">{proj.name}</h4>
                                  {proj.role && (
                                    <span className="text-[10px] bg-pink-100 text-pink-700 font-semibold px-2 py-0.5 rounded-md">
                                      {proj.role}
                                    </span>
                                  )}
                                </div>
                                {proj.description && (
                                  <p className="text-xs text-slate-600 leading-relaxed">{proj.description}</p>
                                )}
                                {proj.tech_stack && (
                                  <p className="text-[11px] text-slate-500 font-medium pt-1">
                                    <strong className="text-slate-700">Công nghệ:</strong> {proj.tech_stack}
                                  </p>
                                )}
                              </div>
                            ))}
                          </div>
                        ) : parsedCv?.sections?.projects ? (
                          <div className="p-4 rounded-2xl bg-pink-50/20 border border-pink-100/70 text-xs text-slate-700 whitespace-pre-line leading-relaxed">
                            {parsedCv.sections.projects}
                          </div>
                        ) : (
                          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 text-xs text-slate-500 italic">
                            Chưa ghi nhận mục dự án trong CV này.
                          </div>
                        )}
                      </div>
                    </div>

                    {/* RIGHT: EDUCATION, SKILLS & CERTS (5 cols) */}
                    <div className="lg:col-span-5 space-y-6">
                      {/* EDUCATION */}
                      <div>
                        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2 mb-3 pb-1 border-b border-slate-100">
                          <GraduationCap className="w-4 h-4 text-indigo-600" />
                          Trình độ Học vấn
                        </h3>
                        {parsedCv?.education && (Array.isArray(parsedCv.education) ? parsedCv.education.length > 0 : true) ? (
                          <div className="p-3.5 rounded-2xl bg-indigo-50/30 border border-indigo-100 space-y-1.5">
                            {Array.isArray(parsedCv.education) ? (
                              parsedCv.education.map((edu: any, idx: number) => {
                                if (typeof edu === 'string') {
                                  return (
                                    <div key={idx} className="text-xs text-slate-800 font-medium">
                                      {edu}
                                    </div>
                                  )
                                }
                                return (
                                  <div key={idx} className="space-y-1">
                                    <h4 className="text-xs sm:text-sm font-bold text-slate-900">{edu.school || edu.degree}</h4>
                                    <p className="text-xs text-slate-700">{edu.degree ? `${edu.degree} (${edu.period || ''})` : edu.period}</p>
                                    {edu.gpa && (
                                      <span className="inline-block px-2 py-0.5 rounded-md bg-white border border-indigo-200 text-indigo-800 text-xs font-bold">
                                        GPA: {edu.gpa}
                                      </span>
                                    )}
                                  </div>
                                )
                              })
                            ) : (
                              <p className="text-xs text-slate-700">{String(parsedCv.education)}</p>
                            )}
                          </div>
                        ) : p?.education || p?.major ? (
                          <div className="p-3.5 rounded-2xl bg-indigo-50/30 border border-indigo-100 space-y-1">
                            <h4 className="text-xs sm:text-sm font-bold text-slate-900">{p?.education || 'Đại học'}</h4>
                            <p className="text-xs text-slate-700">Chuyên ngành: {p?.major || 'Chưa cập nhật'}</p>
                            {p?.gpa && (
                              <span className="inline-block px-2 py-0.5 rounded-md bg-white border border-indigo-200 text-indigo-800 text-xs font-bold">
                                GPA: {p.gpa}/4.0
                              </span>
                            )}
                          </div>
                        ) : (
                          <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-100 text-xs text-slate-400 italic">
                            Chưa cập nhật thông tin học vấn.
                          </div>
                        )}
                      </div>

                      {/* SKILLS MATRIX */}
                      <div>
                        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2 mb-3 pb-1 border-b border-slate-100">
                          <Zap className="w-4 h-4 text-pink-600" />
                          Kỹ năng ({p?.skills.length ?? 0})
                        </h3>
                        {p?.skills && p.skills.length > 0 ? (
                          <div className="flex flex-wrap gap-1.5">
                            {p.skills.map((s) => (
                              <span
                                key={s.name}
                                className={`px-2.5 py-1 rounded-xl text-xs font-medium border ${
                                  s.source === 'cv'
                                    ? 'bg-blue-50 text-blue-800 border-blue-200/80'
                                    : 'bg-pink-50 text-pink-800 border-pink-200/80'
                                }`}
                              >
                                {s.name}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <p className="text-xs text-slate-400 italic">Chưa ghi nhận kỹ năng nào.</p>
                        )}
                      </div>

                      {/* SOFT SKILLS (IF PRESENT) */}
                      {parsedCv?.soft_skills && parsedCv.soft_skills.length > 0 && (
                        <div>
                          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2 mb-3 pb-1 border-b border-slate-100">
                            <Layers className="w-4 h-4 text-emerald-600" />
                            Kỹ năng Mềm
                          </h3>
                          <div className="flex flex-wrap gap-1.5">
                            {parsedCv.soft_skills.map((ss) => (
                              <span key={ss} className="px-2.5 py-1 rounded-xl text-xs font-medium bg-emerald-50 text-emerald-800 border border-emerald-200/80">
                                {ss}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* LANGUAGES (IF PRESENT) */}
                      {parsedCv?.languages && parsedCv.languages.length > 0 && (
                        <div>
                          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2 mb-3 pb-1 border-b border-slate-100">
                            <Globe className="w-4 h-4 text-teal-600" />
                            Ngoại ngữ
                          </h3>
                          <ul className="space-y-1.5 text-xs text-slate-700">
                            {parsedCv.languages.map((lang, lidx) => (
                              <li key={lidx} className="p-2 rounded-xl bg-teal-50/40 border border-teal-100 font-medium text-slate-900">
                                {lang}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* CERTIFICATIONS (IF PRESENT) */}
                      {((parsedCv?.certifications && parsedCv.certifications.length > 0) || parsedCv?.sections?.certifications) && (
                        <div>
                          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2 mb-3 pb-1 border-b border-slate-100">
                            <Award className="w-4 h-4 text-amber-600" />
                            Chứng chỉ & Giải thưởng
                          </h3>
                          {parsedCv?.certifications && parsedCv.certifications.length > 0 ? (
                            <ul className="space-y-1.5 text-xs text-slate-700">
                              {parsedCv.certifications.map((cert, cidx) => (
                                <li key={cidx} className="p-2.5 rounded-xl bg-amber-50/30 border border-amber-100 font-medium text-slate-900">
                                  {cert}
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <div className="p-2.5 rounded-xl bg-amber-50/30 border border-amber-100 text-xs text-slate-800 whitespace-pre-line leading-relaxed">
                              {parsedCv?.sections?.certifications}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {/* TAB 2: CV Health Diagnostics (6 Rules & Issues) */}
        {activeTab === 'health' && (
          <div>
            {!hasCv || !health ? (
              <div className="bg-white rounded-3xl border border-rose-200/80 p-8 sm:p-14 text-center shadow-sm space-y-4">
                <div className="w-14 h-14 rounded-2xl bg-pink-50 text-pink-500 flex items-center justify-center mx-auto">
                  <Sparkles className="w-7 h-7" />
                </div>
                <h3 className="text-lg font-bold text-slate-900">Chưa có dữ liệu chẩn đoán sức khỏe CV</h3>
                <p className="text-xs sm:text-sm text-slate-600 max-w-md mx-auto leading-relaxed">
                  Bạn cần tải lên ít nhất một file CV (PDF hoặc DOCX) để hệ thống tiến hành quét nội dung và đo lường 6 quy tắc định lượng.
                </p>
                <div className="pt-2">
                  <label className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-xs sm:text-sm font-semibold rounded-xl cursor-pointer shadow-sm hover:scale-102 transition">
                    <UploadCloud className="w-4 h-4" />
                    <span>Tải lên file CV ngay</span>
                    <input type="file" accept=".pdf,.docx" onChange={upload} disabled={busy} className="hidden" />
                  </label>
                </div>
              </div>
            ) : (
              <div className="grid lg:grid-cols-12 gap-8 items-start">
                {/* Health Score Breakdown Card (7 cols) */}
                <div className="lg:col-span-7 bg-white/90 backdrop-blur-sm rounded-3xl border border-rose-200/80 p-6 sm:p-8 shadow-sm space-y-6">
                  <div className="flex items-baseline justify-between pb-4 border-b border-slate-100">
                    <div>
                      <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-pink-500" />
                        Chẩn đoán Sức khỏe CV
                      </h2>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Đo lường định lượng theo 6 tiêu chuẩn quốc tế minh bạch
                      </p>
                    </div>
                    <div className="text-right">
                      <span className="text-3xl sm:text-4xl font-black bg-gradient-to-r from-blue-600 to-pink-500 bg-clip-text text-transparent">
                        {Math.round(health.score)}
                      </span>
                      <span className="text-xs text-slate-400 font-semibold">/100đ</span>
                    </div>
                  </div>

                  {/* Breakdown Bars */}
                  <div className="space-y-3.5">
                    {Object.entries(health.breakdown).map(([k, v]) => {
                      const maxP = RULE_LABEL[k]?.[1] || 15
                      const pct = Math.min(100, Math.max(0, (v / maxP) * 100))
                      return (
                        <div key={k} className="p-3 rounded-2xl bg-slate-50/70 border border-slate-100">
                          <div className="flex justify-between items-center text-xs mb-1.5">
                            <span className="font-semibold text-slate-800">
                              {RULE_LABEL[k]?.[0] ?? k}
                            </span>
                            <span className="font-bold text-slate-900">
                              {v} / {maxP} điểm
                            </span>
                          </div>
                          <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                            <div
                              className={`h-2 rounded-full transition-all duration-500 ${
                                pct >= 85 ? 'bg-emerald-500' : pct >= 60 ? 'bg-blue-500' : 'bg-rose-500'
                              }`}
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                        </div>
                      )
                    })}
                  </div>

                  {/* Actionable Recommendations */}
                  <div className="pt-2">
                    <h3 className="text-xs font-bold text-rose-800 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                      <AlertTriangle className="w-4 h-4 text-rose-600" />
                      Điểm cần khắc phục & Tối ưu trong CV
                    </h3>
                    {health.issues && health.issues.length > 0 ? (
                      <ul className="space-y-2">
                        {health.issues.map((iss, n) => (
                          <li
                            key={n}
                            className="text-xs text-rose-800 bg-rose-50/70 p-3 rounded-xl border border-rose-200/80 leading-relaxed flex items-start gap-2"
                          >
                            <span className="text-rose-500 font-bold shrink-0">⚠️</span>
                            <span>{iss}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-medium flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                        <span>CV hoàn hảo! Không phát hiện lỗi cấu trúc hay từ sáo rỗng.</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Upload & Re-score Card (5 cols) */}
                <div className="lg:col-span-5 space-y-6">
                  <div className="bg-white/90 backdrop-blur-sm rounded-3xl border border-slate-200/80 p-6 shadow-sm space-y-4">
                    <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
                      <div className="w-8 h-8 rounded-lg bg-pink-50 text-pink-600 flex items-center justify-center">
                        <UploadCloud className="w-4 h-4" />
                      </div>
                      <h3 className="text-sm font-bold text-slate-900">Tải lên bản CV mới</h3>
                    </div>

                    <div className="border-2 border-dashed border-pink-200 hover:border-blue-400 bg-pink-50/20 hover:bg-blue-50/20 transition rounded-2xl p-6 text-center">
                      <UploadCloud className="w-8 h-8 text-pink-500 mx-auto mb-2" />
                      <p className="text-xs font-semibold text-slate-700 mb-1">
                        Chọn file CV định dạng PDF hoặc DOCX
                      </p>
                      <p className="text-[11px] text-slate-400 mb-3">Dung lượng tối đa 5MB</p>
                      <label className="inline-block px-4 py-2 bg-white border border-slate-200 hover:border-pink-300 text-xs font-semibold text-slate-700 rounded-xl cursor-pointer shadow-2xs hover:bg-slate-50 transition">
                        Duyệt file trên máy tính...
                        <input type="file" accept=".pdf,.docx" onChange={upload} disabled={busy} className="hidden" />
                      </label>
                    </div>

                    {p?.latest_cv && (
                      <div className="flex items-center gap-2 p-3 rounded-xl bg-slate-50 border border-slate-100 text-xs text-slate-600">
                        <FileCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                        <span className="truncate flex-1 font-medium">{p.latest_cv.filename}</span>
                      </div>
                    )}
                  </div>

                  {/* Explanatory Guide Card */}
                  <div className="bg-gradient-to-br from-pink-50/50 via-white to-blue-50/50 rounded-3xl border border-rose-100 p-6 shadow-sm space-y-3">
                    <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                      <TrendingUp className="w-4 h-4 text-blue-600" />
                      Bí quyết nâng điểm CV lên 90+
                    </h4>
                    <ul className="space-y-2 text-xs text-slate-600 leading-relaxed">
                      <li>• <strong>Thêm số liệu định lượng</strong>: Thay vì viết &quot;lập trình API&quot;, hãy viết &quot;thiết kế 12 REST API phục vụ 1.000 người dùng&quot;.</li>
                      <li>• <strong>Tránh từ ngữ sáo rỗng</strong>: Loại bỏ &quot;chăm chỉ, nhiệt tình, ham học hỏi&quot; và thay bằng dự án, bằng khen hoặc đồ án thực tế.</li>
                      <li>• <strong>Đầy đủ liên kết</strong>: Bổ sung liên kết GitHub và LinkedIn để tăng độ uy tín với nhà tuyển dụng công nghệ.</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 3: Edit Profile Form */}
        {activeTab === 'edit' && (
          <div className="grid lg:grid-cols-12 gap-8 items-start">
            <form
              onSubmit={save}
              className="lg:col-span-8 bg-white/90 backdrop-blur-sm rounded-3xl border border-rose-200/80 p-6 sm:p-8 shadow-sm space-y-5"
            >
              <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
                <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                  <User className="w-4 h-4" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-slate-900">Chỉnh sửa Thông tin Ứng viên</h2>
                  <p className="text-xs text-slate-500">Cập nhật hồ sơ để AI đề xuất việc làm chính xác nhất</p>
                </div>
              </div>

              <div className="grid sm:grid-cols-2 gap-4">
                <div className="sm:col-span-2">
                  <label className="block text-xs font-semibold text-slate-700 mb-1.5">Họ và tên *</label>
                  <input className={inp} value={form.full_name} onChange={set('full_name')} required />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1.5">Chuyên ngành đào tạo</label>
                  <input className={inp} value={form.major} onChange={set('major')} placeholder="Vd: Công nghệ thông tin, Khoa học máy tính..." />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1.5">Trình độ học vấn</label>
                  <input className={inp} value={form.education} onChange={set('education')} placeholder="Đại học Bách Khoa, Cử nhân..." />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1.5">Kinh nghiệm (năm)</label>
                  <input type="number" step="0.5" className={inp} value={form.exp_years} onChange={set('exp_years')} placeholder="0" />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1.5">Lương mong muốn (triệu VNĐ)</label>
                  <input type="number" step="0.5" className={inp} value={form.expected_salary} onChange={set('expected_salary')} placeholder="Vd: 15" />
                </div>

                <div className="sm:col-span-2">
                  <label className="block text-xs font-semibold text-slate-700 mb-1.5">Địa điểm làm việc ưu tiên</label>
                  <input className={inp} value={form.location} onChange={set('location')} placeholder="Hà Nội, TP.HCM, Đà Nẵng..." />
                </div>

                <div className="sm:col-span-2">
                  <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                    Kỹ năng nhập tay bổ sung (phân cách bằng dấu phẩy)
                  </label>
                  <input className={inp} value={form.skills} onChange={set('skills')} placeholder="Python, Docker, React, Machine Learning, SQL..." />
                  <p className="text-[11px] text-slate-400 mt-1">Các kỹ năng này sẽ kết hợp với kỹ năng bóc tách từ CV để tính Matching Score</p>
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={busy}
                  className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold text-sm rounded-xl shadow-sm transition hover:shadow-md hover:shadow-blue-500/20 disabled:opacity-50"
                >
                  {busy ? 'Đang lưu...' : 'Lưu hồ sơ & Đồng bộ AI Matching'}
                </button>
              </div>
            </form>

            {/* Recognized Skills Summary */}
            <div className="lg:col-span-4 bg-white/90 backdrop-blur-sm rounded-3xl border border-slate-200/80 p-6 shadow-sm space-y-4">
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                <Zap className="w-4 h-4 text-pink-600" />
                Kỹ năng đang hoạt động ({p?.skills.length ?? 0})
              </h3>
              <p className="text-xs text-slate-500">
                Bao gồm kỹ năng bóc tách tự động từ CV và kỹ năng nhập tay của bạn.
              </p>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {p?.skills && p.skills.length > 0 ? (
                  p.skills.map((s) => (
                    <span
                      key={s.name}
                      className={`px-2.5 py-1 rounded-xl text-xs font-medium border ${
                        s.source === 'cv'
                          ? 'bg-blue-50 text-blue-800 border-blue-200/80'
                          : 'bg-pink-50 text-pink-800 border-pink-200/80'
                      }`}
                    >
                      {s.name}
                      <span className="text-[10px] opacity-60 ml-1">· {s.source}</span>
                    </span>
                  ))
                ) : (
                  <p className="text-xs text-slate-400 italic">Chưa có kỹ năng nào. Hãy tải lên CV hoặc nhập tay ở bên cạnh.</p>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
