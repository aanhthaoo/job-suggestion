'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import Header from '@/components/Header'
import { api, type Job } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { formatSalary } from '@/lib/utils'

type Row = Job & { n_applications: number }
const EMPTY = {
  title: '',
  category: 'Công nghệ thông tin',
  location: 'Hà Nội',
  level: 'Junior',
  contract_type: 'Toàn thời gian',
  working_hours: 'Thứ 2 - Thứ 6 (08:00 - 17:30)',
  languages_required: '',
  exp_years_min: '0',
  salary_min: '',
  salary_max: '',
  skills: '',
  soft_skills: '',
  benefits: '',
  description: '',
  requirements: '',
}

export default function EmployerJobs() {
  const { ready } = useAuth(['employer'])
  const [rows, setRows] = useState<Row[]>([])
  const [f, setF] = useState(EMPTY)
  const [msg, setMsg] = useState('')
  const [busy, setBusy] = useState(false)

  const load = () => api.getEmployerJobs().then(setRows).catch((e) => setMsg(e.message))
  useEffect(() => { if (ready) load() }, [ready])

  const create = async (e: React.FormEvent) => {
    e.preventDefault()
    setMsg('')
    setBusy(true)
    try {
      await api.createEmployerJob({
        title: f.title,
        category: f.category,
        location: f.location,
        level: f.level,
        contract_type: f.contract_type,
        working_hours: f.working_hours || null,
        languages_required: f.languages_required || null,
        description: f.description,
        requirements: f.requirements || null,
        benefits: f.benefits || null,
        exp_years_min: Number(f.exp_years_min) || 0,
        salary_min: f.salary_min ? Number(f.salary_min) : null,
        salary_max: f.salary_max ? Number(f.salary_max) : null,
        skills: f.skills.split(',').map((s) => s.trim()).filter(Boolean),
        soft_skills: f.soft_skills.split(',').map((s) => s.trim()).filter(Boolean),
      })
      setF(EMPTY)
      setMsg('Đã đăng tin tuyển dụng thành công!')
      load()
    } catch (err) {
      setMsg((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const inp = 'w-full px-3 py-2 border border-gray-300 rounded-md text-sm'
  const set = (k: keyof typeof EMPTY) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => setF({ ...f, [k]: e.target.value })

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-6xl mx-auto px-4 py-8 grid md:grid-cols-5 gap-6">
        <section className="md:col-span-3">
          <h1 className="text-2xl font-bold mb-4 text-gray-900">Tin tuyển dụng của công ty ({rows.length})</h1>
          <div className="space-y-3">
            {rows.map((j) => (
              <div key={j.id} className="bg-white border rounded-xl p-4 flex justify-between items-center shadow-sm hover:border-blue-300 transition">
                <div>
                  <Link href={`/jobs/${j.id}`} className="font-semibold text-gray-900 hover:text-blue-600 block">{j.title}</Link>
                  <p className="text-xs text-gray-500 mt-1">
                    {j.location} · {j.contract_type || 'Toàn thời gian'} · {j.level} · {formatSalary(j.salary_min, j.salary_max)}
                  </p>
                </div>
                <Link href={`/employer/candidates?job=${j.id}`} className="text-xs font-medium text-blue-600 hover:underline bg-blue-50 px-2.5 py-1.5 rounded-md whitespace-nowrap">
                  {j.n_applications} ứng viên →
                </Link>
              </div>
            ))}
            {rows.length === 0 && <p className="text-sm text-gray-500">Công ty chưa có tin tuyển dụng nào.</p>}
          </div>
        </section>

        <form onSubmit={create} className="md:col-span-2 bg-white border rounded-xl p-5 space-y-3 h-fit shadow-sm">
          <h2 className="font-bold text-gray-900 text-lg">Đăng tin mới (Đầy đủ thông tin)</h2>
          
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Chức danh / Tiêu đề *</label>
            <input className={inp} placeholder="Vd: Senior Backend Engineer" value={f.title} onChange={set('title')} required />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Ngành nghề *</label>
              <input className={inp} placeholder="Vd: Công nghệ thông tin" value={f.category} onChange={set('category')} required />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Địa điểm *</label>
              <input className={inp} placeholder="Vd: Hà Nội" value={f.location} onChange={set('location')} required />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Cấp bậc</label>
              <select className={inp} value={f.level} onChange={set('level')}>
                <option value="Intern">Intern</option>
                <option value="Junior">Junior</option>
                <option value="Mid">Mid</option>
                <option value="Senior">Senior</option>
                <option value="Manager">Manager</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Hình thức làm việc</label>
              <select className={inp} value={f.contract_type} onChange={set('contract_type')}>
                <option value="Toàn thời gian">Toàn thời gian</option>
                <option value="Bán thời gian">Bán thời gian</option>
                <option value="Thực tập">Thực tập</option>
                <option value="Thời vụ">Thời vụ</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Kinh nghiệm (năm)</label>
              <input className={inp} type="number" step="0.5" placeholder="0" value={f.exp_years_min} onChange={set('exp_years_min')} />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Ngoại ngữ yêu cầu</label>
              <input className={inp} placeholder="Vd: Tiếng Anh, Tiếng Nhật" value={f.languages_required} onChange={set('languages_required')} />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Lương từ (triệu)</label>
              <input className={inp} type="number" step="0.5" placeholder="Vd: 15" value={f.salary_min} onChange={set('salary_min')} />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Lương đến (triệu)</label>
              <input className={inp} type="number" step="0.5" placeholder="Vd: 30" value={f.salary_max} onChange={set('salary_max')} />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Thời gian làm việc</label>
            <input className={inp} placeholder="Vd: Thứ 2 - Thứ 6 (08:00 - 17:30)" value={f.working_hours} onChange={set('working_hours')} />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Kỹ năng kỹ thuật yêu cầu (phân cách bằng dấu phẩy)</label>
            <input className={inp} placeholder="Vd: Python, Docker, PostgreSQL" value={f.skills} onChange={set('skills')} />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Kỹ năng mềm (phân cách bằng dấu phẩy)</label>
            <input className={inp} placeholder="Vd: Làm việc nhóm, Giao tiếp, Giải quyết vấn đề" value={f.soft_skills} onChange={set('soft_skills')} />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Quyền lợi & Đãi ngộ (mỗi dòng một quyền lợi)</label>
            <textarea className={inp} rows={3} placeholder="• Lương tháng 13&#10;• Thưởng KPI hàng quý&#10;• Bảo hiểm sức khỏe PVI" value={f.benefits} onChange={set('benefits')} />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Mô tả công việc *</label>
            <textarea className={inp} rows={3} placeholder="Chi tiết nhiệm vụ công việc..." value={f.description} onChange={set('description')} required />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Yêu cầu ứng viên</label>
            <textarea className={inp} rows={3} placeholder="Yêu cầu năng lực, phẩm chất..." value={f.requirements} onChange={set('requirements')} />
          </div>

          <button
            type="submit"
            disabled={busy}
            className="w-full bg-blue-600 text-white font-medium py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 transition"
          >
            {busy ? 'Đang lưu...' : 'Đăng tin tuyển dụng'}
          </button>
          {msg && <p className="text-xs text-green-700 bg-green-50 p-2 rounded border border-green-200">{msg}</p>}
        </form>
      </main>
    </div>
  )
}
