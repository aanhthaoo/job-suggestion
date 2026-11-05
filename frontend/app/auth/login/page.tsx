'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'
import { Sparkles, User, Briefcase, ShieldCheck, ArrowRight, Lock, Mail } from 'lucide-react'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const data = await api.login(email, password)
      localStorage.setItem('user', JSON.stringify(data.user))
      router.push(data.user.role === 'employer' ? '/employer/dashboard' : data.user.role === 'admin' ? '/admin/dashboard' : '/recommendations')
    } catch (err: any) {
      setError(err.message || 'Đăng nhập thất bại')
    } finally {
      setLoading(false)
    }
  }

  const fillDemo = (e: string, p: string) => {
    setEmail(e)
    setPassword(p)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-rose-50/90 via-pink-50/30 to-blue-50/60 flex items-center justify-center px-4 py-12 relative overflow-hidden">
      {/* Decorative Glows */}
      <div className="absolute top-10 left-10 w-72 h-72 bg-pink-400/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-72 h-72 bg-blue-400/10 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-md w-full relative z-10">
        {/* Header Branding */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2 mb-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-pink-500 flex items-center justify-center text-white shadow-md shadow-blue-500/20 group-hover:scale-105 transition">
              <Sparkles className="w-5 h-5" />
            </div>
            <span className="text-2xl font-extrabold bg-gradient-to-r from-blue-700 via-indigo-600 to-pink-600 bg-clip-text text-transparent tracking-tight">
              JobPortal
            </span>
          </Link>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Đăng nhập tài khoản</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">Chào mừng bạn quay trở lại với hệ thống tuyển dụng AI</p>
        </div>

        {/* Login Card */}
        <div className="bg-white/95 backdrop-blur-md rounded-3xl border border-rose-200/80 p-8 shadow-xl shadow-blue-500/5">
          {error && (
            <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded-xl text-xs mb-5 font-medium">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">Địa chỉ Email</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 bg-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-300 focus:border-blue-400 transition"
                  placeholder="your@email.com"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">Mật khẩu</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 bg-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-300 focus:border-blue-400 transition"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold py-2.5 px-4 rounded-xl shadow-sm transition hover:shadow-md hover:shadow-blue-500/20 disabled:opacity-50 text-xs sm:text-sm flex items-center justify-center gap-2"
            >
              <span>{loading ? 'Đang xác thực...' : 'Đăng nhập'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Quick Demo Fill Buttons */}
          <div className="mt-6 pt-5 border-t border-slate-100">
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2.5">
              Chọn nhanh tài khoản Demo (1-Click):
            </p>
            <div className="flex flex-col gap-1.5">
              <button
                type="button"
                onClick={() => fillDemo('candidate@demo.com', 'demo123')}
                className="text-left p-2 rounded-xl bg-rose-50/60 hover:bg-rose-100/70 border border-rose-100 transition flex items-center justify-between group"
              >
                <div className="flex items-center gap-2">
                  <User className="w-3.5 h-3.5 text-rose-600" />
                  <span className="text-xs font-semibold text-slate-800">Ứng viên: candidate@demo.com</span>
                </div>
                <span className="text-[11px] font-mono font-medium text-rose-600">demo123</span>
              </button>

              <button
                type="button"
                onClick={() => fillDemo('employer@demo.com', 'demo123')}
                className="text-left p-2 rounded-xl bg-blue-50/60 hover:bg-blue-100/70 border border-blue-100 transition flex items-center justify-between group"
              >
                <div className="flex items-center gap-2">
                  <Briefcase className="w-3.5 h-3.5 text-blue-600" />
                  <span className="text-xs font-semibold text-slate-800">Nhà tuyển dụng: employer@demo.com</span>
                </div>
                <span className="text-[11px] font-mono font-medium text-blue-600">demo123</span>
              </button>

              <button
                type="button"
                onClick={() => fillDemo('admin@demo.com', 'demo123')}
                className="text-left p-2 rounded-xl bg-purple-50/60 hover:bg-purple-100/70 border border-purple-100 transition flex items-center justify-between group"
              >
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-3.5 h-3.5 text-purple-600" />
                  <span className="text-xs font-semibold text-slate-800">Quản trị viên: admin@demo.com</span>
                </div>
                <span className="text-[11px] font-mono font-medium text-purple-600">demo123</span>
              </button>
            </div>
          </div>

          <div className="mt-6 text-center text-xs text-slate-500">
            Chưa có tài khoản?{' '}
            <Link href="/auth/register" className="font-semibold text-blue-600 hover:text-blue-700 hover:underline">
              Đăng ký ngay
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
