'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import type { User } from './api'

/** Reads the logged-in user from localStorage; redirects to login when missing or role not allowed. */
export function useAuth(roles?: User['role'][]) {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    let u: User | null = null
    try {
      u = JSON.parse(localStorage.getItem('user') || 'null')
    } catch {
      u = null
    }
    if (!u || !localStorage.getItem('auth_token')) {
      router.replace('/auth/login')
      return
    }
    if (roles && !roles.includes(u.role)) {
      router.replace('/')
      return
    }
    setUser(u)
    setReady(true)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return { user, ready }
}
