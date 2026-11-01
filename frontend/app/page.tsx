'use client'

import { useState } from 'react'
import Link from 'next/link'
import Header from '@/components/Header'
import JobCard from '@/components/JobCard'
import mockJobs from '@/mock/jobs.json'
import { Search, MapPin, Briefcase } from 'lucide-react'

export default function Home() {
  const [searchQuery, setSearchQuery] = useState('')
  const [location, setLocation] = useState('')

  // Use mock data for demo
  const featuredJobs = mockJobs.slice(0, 6)

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      {/* Hero Section */}
      <section className="bg-gradient-to-r from-blue-600 to-blue-800 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-bold mb-4">
              Tìm Việc Làm Phù Hợp Với Bạn
            </h1>
            <p className="text-xl text-blue-100">
              Hệ thống tìm kiếm việc làm thông minh cho sinh viên mới tốt nghiệp
            </p>
          </div>

          {/* Search Box */}
          <div className="bg-white rounded-lg shadow-lg p-6 max-w-4xl mx-auto">
            <div className="grid md:grid-cols-3 gap-4">
              <div className="md:col-span-2 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Tìm theo từ khóa (Python, Developer, Data...)"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                />
              </div>
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Địa điểm"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                />
              </div>
            </div>
            <div className="mt-4 flex justify-center">
              <Link
                href={`/jobs?search=${encodeURIComponent(searchQuery)}&location=${encodeURIComponent(location)}`}
                className="bg-blue-600 text-white px-8 py-3 rounded-md hover:bg-blue-700 transition-colors font-medium"
              >
                Tìm kiếm
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold text-blue-600 mb-2">48,092</div>
              <div className="text-gray-600">Việc làm trong database</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-blue-600 mb-2">500+</div>
              <div className="text-gray-600">Công ty đối tác</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-blue-600 mb-2">10,000+</div>
              <div className="text-gray-600">Ứng viên đã tìm được việc</div>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Jobs */}
      <section className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-8">Việc làm nổi bật</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {featuredJobs.map((job: any) => (
              <JobCard key={job.id} job={job} />
            ))}
          </div>
          <div className="mt-8 text-center">
            <Link
              href="/jobs"
              className="inline-block bg-white border-2 border-blue-600 text-blue-600 px-8 py-3 rounded-md hover:bg-blue-50 transition-colors font-medium"
            >
              Xem tất cả việc làm
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
            Tính năng thông minh
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <Briefcase className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Tự động khớp CV</h3>
              <p className="text-gray-600">
                Hệ thống tự động phân tích CV và chấm điểm độ phù hợp với từng công việc
              </p>
            </div>
            <div className="text-center">
              <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <Search className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Gợi ý cá nhân hóa</h3>
              <p className="text-gray-600">
                Đề xuất việc làm phù hợp dựa trên kỹ năng và kinh nghiệm của bạn
              </p>
            </div>
            <div className="text-center">
              <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <MapPin className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Phân tích thị trường</h3>
              <p className="text-gray-600">
                Thông tin chi tiết về xu hướng lương, kỹ năng hot theo ngành nghề
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-blue-600 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold mb-4">Sẵn sàng tìm việc mơ ước?</h2>
          <p className="text-xl mb-8 text-blue-100">
            Tạo tài khoản ngay để bắt đầu hành trình sự nghiệp của bạn
          </p>
          <Link
            href="/auth/register"
            className="inline-block bg-white text-blue-600 px-8 py-3 rounded-md hover:bg-blue-50 transition-colors font-medium"
          >
            Đăng ký miễn phí
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <h3 className="text-xl font-bold mb-4">JobPortal</h3>
              <p className="text-gray-400">
                Hệ thống tìm kiếm việc làm thông minh cho sinh viên
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Dành cho ứng viên</h4>
              <ul className="space-y-2 text-gray-400">
                <li><Link href="/jobs" className="hover:text-white">Tìm việc làm</Link></li>
                <li><Link href="/profile" className="hover:text-white">Quản lý hồ sơ</Link></li>
                <li><Link href="/applications" className="hover:text-white">Theo dõi ứng tuyển</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Dành cho nhà tuyển dụng</h4>
              <ul className="space-y-2 text-gray-400">
                <li><Link href="#" className="hover:text-white">Đăng tin tuyển dụng</Link></li>
                <li><Link href="#" className="hover:text-white">Tìm ứng viên</Link></li>
                <li><Link href="#" className="hover:text-white">Quản lý ứng tuyển</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Liên hệ</h4>
              <ul className="space-y-2 text-gray-400">
                <li>Email: support@jobportal.vn</li>
                <li>Phone: +84 123 456 789</li>
                <li>Address: Hà Nội, Việt Nam</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2026 JobPortal. Đồ án môn Business Intelligence - Đại học Thủy Lợi</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
