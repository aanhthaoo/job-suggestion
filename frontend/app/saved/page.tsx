'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import Header from '@/components/Header'
import JobCard from '@/components/JobCard'
import mockJobs from '@/mock/jobs.json'
import { Bookmark } from 'lucide-react'

const SAVED_KEY = 'saved_jobs'

export default function SavedJobsPage() {
  const [savedJobs, setSavedJobs] = useState<any[]>([])

  useEffect(() => {
    const load = () => {
      let ids: string[] = []
      try {
        ids = JSON.parse(localStorage.getItem(SAVED_KEY) || '[]')
      } catch {
        ids = []
      }
      setSavedJobs(mockJobs.filter((j: any) => ids.includes(j.id)))
    }
    load()
    window.addEventListener('saved_jobs_changed', load)
    return () => window.removeEventListener('saved_jobs_changed', load)
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center gap-3 mb-8">
          <Bookmark className="w-8 h-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">Việc làm đã lưu</h1>
        </div>

        {savedJobs.length > 0 ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {savedJobs.map((job) => (
              <JobCard key={job.id} job={job} />
            ))}
          </div>
        ) : (
          <div className="text-center py-16 bg-white rounded-lg border border-gray-200">
            <p className="text-gray-500 text-lg mb-2">Chưa có việc làm nào được lưu</p>
            <p className="text-gray-400 text-sm mb-6">
              Nhấn nút &quot;Lưu&quot; ở mỗi công việc để theo dõi tại đây
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
