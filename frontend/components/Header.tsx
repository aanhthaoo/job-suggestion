'use client'

import Link from 'next/link'
import { useState, useEffect } from 'react'
import { LogOut, Menu, X, Sparkles, User, Briefcase, ShieldCheck } from 'lucide-react'

type Role = 'candidate' | 'employer' | 'admin'

const LINKS: Record<Role | 'guest', { href: string; label: string }[]> = {
  guest: [{ href: '/jobs', label: 'Tìm việc làm' }],
  candidate: [
    { href: '/jobs', label: 'Tìm việc làm' },
    { href: '/recommendations', label: 'Gợi ý AI' },
    { href: '/applications', label: 'Đơn ứng tuyển' },
    { href: '/profile', label: 'Hồ sơ & CV' },
  ],
  employer: [
    { href: '/employer/jobs', label: 'Tin tuyển dụng' },
    { href: '/employer/candidates', label: 'Xếp hạng ứng viên' },
    { href: '/employer/dashboard', label: 'KPI Dashboard' },
  ],
  admin: [
    { href: '/jobs', label: 'Tìm việc làm' },
    { href: '/admin/dashboard', label: 'Quản trị & BI' },
  ],
}

const ROLE_BADGE: Record<Role, { label: string; cls: string; icon: any }> = {
  candidate: { label: 'Ứng viên', cls: 'bg-rose-50 text-rose-700 border-rose-200', icon: User },
  employer: { label: 'Nhà tuyển dụng', cls: 'bg-blue-50 text-blue-700 border-blue-200', icon: Briefcase },
  admin: { label: 'Quản trị viên', cls: 'bg-purple-50 text-purple-700 border-purple-200', icon: ShieldCheck },
}

export default function Header() {
  const [role, setRole] = useState<Role | null>(null)
  const [userEmail, setUserEmail] = useState<string>('')
  const [open, setOpen] = useState(false)

  useEffect(() => {
    try {
      const u = JSON.parse(localStorage.getItem('user') || 'null')
      if (u && localStorage.getItem('auth_token')) {
        setRole(u.role)
        setUserEmail(u.full_name || u.email || '')
      }
    } catch {
      // malformed user payload: treat as guest
    }
  }, [])

  const logout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user')
    window.location.href = '/'
  }

  const nav = LINKS[role ?? 'guest']
  const badge = role ? ROLE_BADGE[role] : null
  const RoleIcon = badge ? badge.icon : null

  return (
    <header className="bg-white/85 backdrop-blur-md border-b border-rose-100/70 sticky top-0 z-50 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo with Blue & Pink gradient */}
          <Link href="/" className="flex items-center gap-2 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-pink-500 flex items-center justify-center text-white shadow-sm shadow-blue-500/20 group-hover:scale-105 transition-transform duration-200">
              <Sparkles className="w-5 h-5" />
            </div>
            <div className="flex flex-col">
              <span className="text-xl font-extrabold bg-gradient-to-r from-blue-700 via-indigo-600 to-pink-600 bg-clip-text text-transparent tracking-tight">
                JobPortal
              </span>
              <span className="text-[10px] font-medium text-slate-500 -mt-1 tracking-wider uppercase">
                AI & BI Recruitment
              </span>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center space-x-1 lg:space-x-2">
            {nav.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className="px-3 py-2 text-sm font-medium text-slate-700 hover:text-blue-600 hover:bg-blue-50/60 rounded-lg transition-colors"
              >
                {l.label}
              </Link>
            ))}
          </nav>

          {/* User actions */}
          <div className="hidden md:flex items-center space-x-3">
            {role && badge && (
              <div className="flex items-center gap-2 mr-2">
                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${badge.cls}`}>
                  {RoleIcon && <RoleIcon className="w-3.5 h-3.5" />}
                  {badge.label}
                </span>
                {userEmail && (
                  <span className="text-xs text-slate-600 font-medium max-w-[120px] truncate" title={userEmail}>
                    {userEmail}
                  </span>
                )}
              </div>
            )}

            {role ? (
              <button
                onClick={logout}
                className="inline-flex items-center text-sm font-medium text-slate-600 hover:text-rose-600 hover:bg-rose-50 px-3 py-2 rounded-lg transition-colors"
              >
                <LogOut className="w-4 h-4 mr-1.5" />
                Đăng xuất
              </button>
            ) : (
              <>
                <Link
                  href="/auth/login"
                  className="text-sm font-semibold text-slate-700 hover:text-blue-600 px-3.5 py-2 rounded-lg hover:bg-slate-100/70 transition"
                >
                  Đăng nhập
                </Link>
                <Link
                  href="/auth/register"
                  className="text-sm font-semibold text-white px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-pink-500 hover:from-blue-700 hover:to-pink-600 shadow-sm shadow-blue-500/25 transition-all hover:shadow-md hover:shadow-pink-500/20"
                >
                  Đăng ký
                </Link>
              </>
            )}
          </div>

          {/* Mobile menu button */}
          <button
            className="md:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100"
            onClick={() => setOpen(!open)}
            aria-label="Toggle menu"
          >
            {open ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile dropdown menu */}
        {open && (
          <div className="md:hidden py-4 border-t border-rose-100 flex flex-col space-y-2">
            {role && badge && (
              <div className="px-3 py-2 mb-1 flex items-center justify-between bg-slate-50 rounded-lg">
                <span className="text-xs text-slate-600 truncate">{userEmail}</span>
                <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border ${badge.cls}`}>
                  {badge.label}
                </span>
              </div>
            )}
            {nav.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className="px-3 py-2 text-sm font-medium text-slate-700 hover:bg-blue-50 hover:text-blue-600 rounded-lg"
                onClick={() => setOpen(false)}
              >
                {l.label}
              </Link>
            ))}
            <div className="pt-2 border-t border-slate-100">
              {role ? (
                <button
                  onClick={logout}
                  className="w-full text-left px-3 py-2 text-sm font-medium text-rose-600 hover:bg-rose-50 rounded-lg"
                >
                  Đăng xuất
                </button>
              ) : (
                <div className="flex flex-col gap-2 pt-1">
                  <Link
                    href="/auth/login"
                    className="text-center px-3 py-2 text-sm font-medium text-slate-700 border border-slate-200 rounded-xl"
                    onClick={() => setOpen(false)}
                  >
                    Đăng nhập
                  </Link>
                  <Link
                    href="/auth/register"
                    className="text-center px-3 py-2 text-sm font-semibold text-white bg-gradient-to-r from-blue-600 to-pink-500 rounded-xl shadow-xs"
                    onClick={() => setOpen(false)}
                  >
                    Đăng ký ngay
                  </Link>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </header>
  )
}
