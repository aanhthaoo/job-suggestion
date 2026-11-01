'use client'

import { useEffect, useState } from 'react'
import Header from '@/components/Header'
import { User, Save, X } from 'lucide-react'

const PROFILE_KEY = 'user_profile'

interface Profile {
  full_name: string
  email: string
  phone: string
  location: string
  experience_years: number
  skills: string[]
}

const defaultProfile: Profile = {
  full_name: '',
  email: '',
  phone: '',
  location: 'Hà Nội',
  experience_years: 2,
  skills: ['Python', 'SQL', 'Machine Learning', 'pandas'],
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<Profile>(defaultProfile)
  const [skillInput, setSkillInput] = useState('')
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    let stored: Partial<Profile> = {}
    try {
      stored = JSON.parse(localStorage.getItem(PROFILE_KEY) || '{}')
    } catch {
      stored = {}
    }
    let user: any = {}
    try {
      user = JSON.parse(localStorage.getItem('user') || '{}')
    } catch {
      user = {}
    }
    setProfile({
      ...defaultProfile,
      full_name: user.full_name || stored.full_name || '',
      email: user.email || stored.email || '',
      ...stored,
    })
  }, [])

  const persist = (next: Profile) => {
    setProfile(next)
    localStorage.setItem(PROFILE_KEY, JSON.stringify(next))
    setSaved(true)
    setTimeout(() => setSaved(false), 1500)
  }

  const addSkill = () => {
    const value = skillInput.trim()
    if (!value || profile.skills.includes(value)) {
      setSkillInput('')
      return
    }
    persist({ ...profile, skills: [...profile.skills, value] })
    setSkillInput('')
  }

  const removeSkill = (skill: string) => {
    persist({ ...profile, skills: profile.skills.filter((s) => s !== skill) })
  }

  const update = (field: keyof Profile, value: string | number) => {
    setProfile((p) => ({ ...p, [field]: value }))
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center gap-3 mb-8">
          <User className="w-8 h-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">Hồ sơ của bạn</h1>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-8 space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Họ tên</label>
              <input
                type="text"
                value={profile.full_name}
                onChange={(e) => update('full_name', e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                placeholder="Nguyễn Văn A"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={profile.email}
                onChange={(e) => update('email', e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                placeholder="ban@email.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Số điện thoại</label>
              <input
                type="text"
                value={profile.phone}
                onChange={(e) => update('phone', e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                placeholder="09xx xxx xxx"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Địa điểm</label>
              <input
                type="text"
                value={profile.location}
                onChange={(e) => update('location', e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                placeholder="Hà Nội"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Số năm kinh nghiệm
              </label>
              <input
                type="number"
                min={0}
                value={profile.experience_years}
                onChange={(e) => update('experience_years', Number(e.target.value))}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Kỹ năng</label>
            <div className="flex flex-wrap gap-2 mb-3">
              {profile.skills.map((skill) => (
                <span
                  key={skill}
                  className="flex items-center gap-1 px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm"
                >
                  {skill}
                  <button onClick={() => removeSkill(skill)} aria-label={`Xóa ${skill}`}>
                    <X className="w-3.5 h-3.5" />
                  </button>
                </span>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={skillInput}
                onChange={(e) => setSkillInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addSkill()}
                className="flex-1 border border-gray-300 rounded-md px-3 py-2"
                placeholder="Thêm kỹ năng (vd: Docker)"
              />
              <button
                onClick={addSkill}
                className="px-4 py-2 border border-blue-600 text-blue-600 rounded-md hover:bg-blue-50"
              >
                Thêm
              </button>
            </div>
          </div>

          <div className="flex items-center gap-4 pt-2">
            <button
              onClick={() => persist(profile)}
              className="flex items-center gap-2 bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700"
            >
              <Save className="w-4 h-4" />
              Lưu hồ sơ
            </button>
            {saved && <span className="text-green-600 text-sm">Đã lưu ✓</span>}
          </div>
        </div>

        <p className="text-sm text-gray-500 mt-6">
          Hồ sơ này được dùng để tính điểm phù hợp ở trang{' '}
          <span className="font-medium text-gray-700">Gợi ý</span>.
        </p>
      </div>
    </div>
  )
}
