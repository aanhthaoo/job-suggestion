'use client'

import { useState, useEffect } from 'react'
import Header from '@/components/Header'
import JobCard from '@/components/JobCard'
import { Sparkles } from 'lucide-react'
import MOCK_JOBS from '@/mock/jobs.json'

// Default profile; overridden by the user's saved profile (localStorage) when present.
const DEFAULT_PROFILE = {
  skills: ['Python', 'SQL', 'Machine Learning', 'pandas'],
  experience_years: 2,
  location: 'Hà Nội',
}

export default function RecommendationsPage() {
  const [recommendations, setRecommendations] = useState<any[]>([])
  const [profile, setProfile] = useState(DEFAULT_PROFILE)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let stored: any = {}
    try {
      stored = JSON.parse(localStorage.getItem('user_profile') || '{}')
    } catch {
      stored = {}
    }
    const active = {
      skills: stored.skills?.length ? stored.skills : DEFAULT_PROFILE.skills,
      experience_years:
        typeof stored.experience_years === 'number'
          ? stored.experience_years
          : DEFAULT_PROFILE.experience_years,
      location: stored.location || DEFAULT_PROFILE.location,
    }
    setProfile(active)

    // In real app, call API: /api/v1/recommendations?skills=...&experience_years=...
    // For demo, calculate match scores client-side from the mock dataset.
    const userSkills = new Set(active.skills.map((s: string) => s.toLowerCase()))

    const scored = MOCK_JOBS.map((job: any) => {
      const jobSkills = new Set(job.skills_required.map((s: string) => s.toLowerCase()))
      const matched = [...userSkills].filter((s) => jobSkills.has(s))
      const matchScore = matched.length / Math.max(jobSkills.size, 1)

      return {
        ...job,
        match_score: matchScore,
        match_reason: {
          matched_skills: matched,
          missing_skills: [...jobSkills].filter((s: any) => !userSkills.has(s)),
        },
      }
    })

    const sorted = scored
      .filter((j: any) => j.match_score > 0.3)
      .sort((a: any, b: any) => b.match_score - a.match_score)
      .slice(0, 6)

    setRecommendations(sorted)
    setLoading(false)
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="max-w-7xl mx-auto px-4 py-12 text-center">
          <p className="text-gray-600">Đang phân tích hồ sơ và tìm việc phù hợp...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Sparkles className="w-8 h-8 text-purple-600" />
            <h1 className="text-3xl font-bold text-gray-900">Việc làm gợi ý cho bạn</h1>
          </div>
          <p className="text-gray-600">
            Dựa trên kỹ năng: <span className="font-semibold">{profile.skills.join(', ')}</span>
          </p>
        </div>

        {/* User Profile Summary */}
        <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Hồ sơ của bạn</h2>
          <div className="grid md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-600">Kỹ năng</p>
              <div className="flex flex-wrap gap-2 mt-1">
                {profile.skills.map((skill) => (
                  <span key={skill} className="px-2 py-1 bg-white text-purple-700 text-xs rounded-full border border-purple-200">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
            <div>
              <p className="text-sm text-gray-600">Kinh nghiệm</p>
              <p className="font-medium text-gray-900">{profile.experience_years} năm</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Địa điểm ưu tiên</p>
              <p className="font-medium text-gray-900">{profile.location}</p>
            </div>
          </div>
        </div>

        {/* Recommendations */}
        {recommendations.length > 0 ? (
          <>
            <div className="mb-4 text-gray-600">
              Tìm thấy <span className="font-semibold text-gray-900">{recommendations.length}</span> việc làm phù hợp
            </div>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {recommendations.map((job) => (
                <JobCard key={job.id} job={job} />
              ))}
            </div>
          </>
        ) : (
          <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
            <p className="text-gray-500 text-lg mb-2">Chưa có gợi ý phù hợp</p>
            <p className="text-gray-400 text-sm">Thử thêm nhiều kỹ năng vào hồ sơ của bạn</p>
          </div>
        )}

        {/* Explanation */}
        <div className="mt-12 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">Cách hệ thống gợi ý?</h3>
          <ul className="text-sm text-blue-800 space-y-2">
            <li>• <strong>Phân tích kỹ năng:</strong> So sánh kỹ năng trong CV với yêu cầu công việc</li>
            <li>• <strong>Kinh nghiệm:</strong> Đánh giá mức độ phù hợp về số năm kinh nghiệm</li>
            <li>• <strong>Địa điểm:</strong> Ưu tiên các công việc ở địa điểm bạn mong muốn</li>
            <li>• <strong>Trọng số:</strong> Kỹ năng (40%) + Kinh nghiệm (35%) + Địa điểm (25%)</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
