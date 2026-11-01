'use client'

import { useEffect, useState } from 'react'
import { Job } from '@/lib/api'
import { formatCurrency, formatDate } from '@/lib/utils'
import { MapPin, Briefcase, DollarSign, Clock, Bookmark, BookmarkCheck } from 'lucide-react'
import Link from 'next/link'

interface JobCardProps {
  job: Job
}

const SAVED_KEY = 'saved_jobs'

function readSaved(): string[] {
  if (typeof window === 'undefined') return []
  try {
    return JSON.parse(localStorage.getItem(SAVED_KEY) || '[]')
  } catch {
    return []
  }
}

export default function JobCard({ job }: JobCardProps) {
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    setSaved(readSaved().includes(job.id))
  }, [job.id])

  const toggleSave = () => {
    const current = readSaved()
    const next = saved ? current.filter((id) => id !== job.id) : [...current, job.id]
    localStorage.setItem(SAVED_KEY, JSON.stringify(next))
    setSaved(!saved)
    window.dispatchEvent(new Event('saved_jobs_changed'))
  }

  const jobTypeLabels = {
    fulltime: 'Full-time',
    parttime: 'Part-time',
    internship: 'Internship',
  }

  const workModeLabels = {
    onsite: 'On-site',
    remote: 'Remote',
    hybrid: 'Hybrid',
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-3">
        <div>
          <Link href={`/jobs/${job.id}`} className="text-xl font-semibold text-gray-900 hover:text-blue-600">
            {job.title}
          </Link>
          <p className="text-gray-600 mt-1">{job.company_name}</p>
        </div>
        {job.match_score && (
          <span
            className={`px-3 py-1 rounded-full text-sm font-medium ${
              job.match_score >= 0.7
                ? 'bg-green-100 text-green-800'
                : job.match_score >= 0.55
                ? 'bg-blue-100 text-blue-800'
                : 'bg-gray-100 text-gray-800'
            }`}
          >
            {Math.round(job.match_score * 100)}% Match
          </span>
        )}
      </div>

      <div className="space-y-2 mb-4">
        <div className="flex items-center text-gray-600 text-sm">
          <MapPin className="w-4 h-4 mr-2" />
          {job.location}
        </div>
        <div className="flex items-center text-gray-600 text-sm">
          <Briefcase className="w-4 h-4 mr-2" />
          {jobTypeLabels[job.job_type]} • {workModeLabels[job.work_mode]}
        </div>
        {(job.salary_min || job.salary_max) && (
          <div className="flex items-center text-gray-600 text-sm">
            <DollarSign className="w-4 h-4 mr-2" />
            {job.salary_min && job.salary_max
              ? `${formatCurrency(job.salary_min)} - ${formatCurrency(job.salary_max)}`
              : job.salary_min
              ? `Từ ${formatCurrency(job.salary_min)}`
              : job.salary_max
              ? `Đến ${formatCurrency(job.salary_max)}`
              : 'Thương lượng'}
          </div>
        )}
        <div className="flex items-center text-gray-600 text-sm">
          <Clock className="w-4 h-4 mr-2" />
          Đăng {formatDate(job.posted_at)}
        </div>
      </div>

      {job.skills_required && job.skills_required.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {job.skills_required.slice(0, 5).map((skill) => (
            <span
              key={skill}
              className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-md"
            >
              {skill}
            </span>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        <Link
          href={`/jobs/${job.id}`}
          className="flex-1 bg-blue-600 text-white text-center py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
        >
          Xem chi tiết
        </Link>
        <button
          onClick={toggleSave}
          aria-label={saved ? 'Bỏ lưu việc làm' : 'Lưu việc làm'}
          className={`flex items-center gap-1 px-4 py-2 border rounded-md transition-colors ${
            saved
              ? 'border-blue-600 text-blue-600 bg-blue-50'
              : 'border-gray-300 hover:bg-gray-50'
          }`}
        >
          {saved ? <BookmarkCheck className="w-4 h-4" /> : <Bookmark className="w-4 h-4" />}
          <span className="text-sm">{saved ? 'Đã lưu' : 'Lưu'}</span>
        </button>
      </div>
    </div>
  )
}
