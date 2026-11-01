'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Header from '@/components/Header'
import mockJobs from '@/mock/jobs.json'
import { MapPin, Briefcase, DollarSign, Clock, Building, BookmarkCheck } from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'

const SAVED_KEY = 'saved_jobs'
const APPLICATIONS_KEY = 'applications'

function readSaved(): string[] {
  if (typeof window === 'undefined') return []
  try {
    return JSON.parse(localStorage.getItem(SAVED_KEY) || '[]')
  } catch {
    return []
  }
}

function readApplications(): any[] {
  if (typeof window === 'undefined') return []
  try {
    return JSON.parse(localStorage.getItem(APPLICATIONS_KEY) || '[]')
  } catch {
    return []
  }
}

export default function JobDetailPage() {
  const params = useParams()
  const job = mockJobs.find((j) => j.id === params.id)
  const [saved, setSaved] = useState(false)
  const [applied, setApplied] = useState(false)

  useEffect(() => {
    if (!job) return
    setSaved(readSaved().includes(job.id))
    setApplied(readApplications().some((a) => a.job_id === job.id))
  }, [job])

  if (!job) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="max-w-4xl mx-auto px-4 py-12 text-center">
          <h1 className="text-2xl font-bold text-gray-900">Không tìm thấy công việc</h1>
        </div>
      </div>
    )
  }

  const handleSave = () => {
    const current = readSaved()
    const next = saved ? current.filter((id) => id !== job.id) : [...current, job.id]
    localStorage.setItem(SAVED_KEY, JSON.stringify(next))
    setSaved(!saved)
    window.dispatchEvent(new Event('saved_jobs_changed'))
  }

  const handleApply = () => {
    if (applied) return
    const apps = readApplications()
    apps.unshift({
      id: `app_${Date.now()}`,
      job_id: job.id,
      status: 'submitted',
      applied_at: new Date().toISOString(),
    })
    localStorage.setItem(APPLICATIONS_KEY, JSON.stringify(apps))
    setApplied(true)
    window.dispatchEvent(new Event('applications_changed'))
  }

  const jobTypeLabels: Record<string, string> = {
    fulltime: 'Full-time',
    parttime: 'Part-time',
    internship: 'Internship',
  }

  const workModeLabels: Record<string, string> = {
    onsite: 'On-site',
    remote: 'Remote',
    hybrid: 'Hybrid',
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Job Header */}
        <div className="bg-white rounded-lg border border-gray-200 p-8 mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{job.title}</h1>
          <div className="flex items-center text-gray-600 mb-4">
            <Building className="w-5 h-5 mr-2" />
            <span className="text-lg">{job.company_name}</span>
          </div>

          <div className="grid md:grid-cols-2 gap-4 mb-6">
            <div className="flex items-center text-gray-600">
              <MapPin className="w-5 h-5 mr-2" />
              {job.location}
            </div>
            <div className="flex items-center text-gray-600">
              <Briefcase className="w-5 h-5 mr-2" />
              {jobTypeLabels[job.job_type]} • {workModeLabels[job.work_mode]}
            </div>
            {(job.salary_min || job.salary_max) && (
              <div className="flex items-center text-gray-600">
                <DollarSign className="w-5 h-5 mr-2" />
                {job.salary_min && job.salary_max
                  ? `${formatCurrency(job.salary_min)} - ${formatCurrency(job.salary_max)}`
                  : job.salary_min
                  ? `Từ ${formatCurrency(job.salary_min)}`
                  : `Đến ${formatCurrency(job.salary_max)}`}
              </div>
            )}
            <div className="flex items-center text-gray-600">
              <Clock className="w-5 h-5 mr-2" />
              Đăng {formatDate(job.posted_at)}
            </div>
          </div>

          {/* Match score sẽ hiển thị khi có backend thực sự */}

          <div className="flex gap-4">
            <button
              onClick={handleApply}
              disabled={applied}
              className={`flex-1 py-3 px-6 rounded-md font-medium ${
                applied
                  ? 'bg-green-100 text-green-800 cursor-default'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {applied ? 'Đã ứng tuyển ✓' : 'Ứng tuyển ngay'}
            </button>
            <button
              onClick={handleSave}
              className={`flex items-center gap-2 px-6 py-3 border rounded-md ${
                saved
                  ? 'border-blue-600 text-blue-600 bg-blue-50'
                  : 'border-gray-300 hover:bg-gray-50'
              }`}
            >
              {saved && <BookmarkCheck className="w-5 h-5" />}
              {saved ? 'Đã lưu' : 'Lưu việc'}
            </button>
          </div>
        </div>

        {/* Job Description */}
        <div className="bg-white rounded-lg border border-gray-200 p-8 mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Mô tả công việc</h2>
          <div className="prose max-w-none text-gray-700 whitespace-pre-line">
            {job.description}
          </div>
        </div>

        {/* Requirements */}
        <div className="bg-white rounded-lg border border-gray-200 p-8 mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Yêu cầu công việc</h2>
          <div className="prose max-w-none text-gray-700 whitespace-pre-line">
            {job.requirements}
          </div>
        </div>

        {/* Skills */}
        {job.skills_required && job.skills_required.length > 0 && (
          <div className="bg-white rounded-lg border border-gray-200 p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Kỹ năng yêu cầu</h2>
            <div className="flex flex-wrap gap-2">
              {job.skills_required.map((skill) => (
                <span
                  key={skill}
                  className="px-4 py-2 bg-blue-50 text-blue-700 rounded-full text-sm font-medium"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
