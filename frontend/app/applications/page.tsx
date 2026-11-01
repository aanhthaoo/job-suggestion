'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import Header from '@/components/Header'
import mockJobs from '@/mock/jobs.json'
import { formatDate } from '@/lib/utils'
import { FileText, MapPin, Building } from 'lucide-react'

const APPLICATIONS_KEY = 'applications'

const statusLabels: Record<string, string> = {
  submitted: 'Đã nộp',
  reviewed: 'Đang xem xét',
  interviewing: 'Phỏng vấn',
  accepted: 'Trúng tuyển',
  rejected: 'Không đạt',
}

const statusStyles: Record<string, string> = {
  submitted: 'bg-gray-100 text-gray-800',
  reviewed: 'bg-blue-100 text-blue-800',
  interviewing: 'bg-purple-100 text-purple-800',
  accepted: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
}

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<any[]>([])

  useEffect(() => {
    const load = () => {
      let apps: any[] = []
      try {
        apps = JSON.parse(localStorage.getItem(APPLICATIONS_KEY) || '[]')
      } catch {
        apps = []
      }
      const enriched = apps.map((app) => ({
        ...app,
        job: mockJobs.find((j: any) => j.id === app.job_id),
      }))
      setApplications(enriched)
    }
    load()
    window.addEventListener('applications_changed', load)
    return () => window.removeEventListener('applications_changed', load)
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center gap-3 mb-8">
          <FileText className="w-8 h-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">Hồ sơ ứng tuyển</h1>
        </div>

        {applications.length > 0 ? (
          <div className="space-y-4">
            {applications.map((app) => (
              <div
                key={app.id}
                className="bg-white rounded-lg border border-gray-200 p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
              >
                <div>
                  {app.job ? (
                    <>
                      <Link
                        href={`/jobs/${app.job.id}`}
                        className="text-lg font-semibold text-gray-900 hover:text-blue-600"
                      >
                        {app.job.title}
                      </Link>
                      <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600 mt-1">
                        <span className="flex items-center gap-1">
                          <Building className="w-4 h-4" />
                          {app.job.company_name}
                        </span>
                        <span className="flex items-center gap-1">
                          <MapPin className="w-4 h-4" />
                          {app.job.location}
                        </span>
                        <span>Ứng tuyển {formatDate(app.applied_at)}</span>
                      </div>
                    </>
                  ) : (
                    <span className="text-gray-500">Công việc không còn tồn tại</span>
                  )}
                </div>
                <span
                  className={`self-start sm:self-center px-3 py-1 rounded-full text-sm font-medium ${
                    statusStyles[app.status] || statusStyles.submitted
                  }`}
                >
                  {statusLabels[app.status] || app.status}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-16 bg-white rounded-lg border border-gray-200">
            <p className="text-gray-500 text-lg mb-2">Bạn chưa ứng tuyển công việc nào</p>
            <p className="text-gray-400 text-sm mb-6">
              Tìm công việc phù hợp và nhấn &quot;Ứng tuyển ngay&quot;
            </p>
            <Link
              href="/jobs"
              className="inline-block bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700"
            >
              Tìm việc ngay
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}
