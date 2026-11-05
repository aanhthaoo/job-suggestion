// API client. All scores come from the backend; the UI never computes matching itself.
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export interface Job {
  id: number
  title: string
  company_id?: number
  company_name?: string
  category?: string
  location?: string
  level?: string
  exp_years_min?: number
  education?: string
  salary_min?: number | null
  salary_max?: number | null
  description: string
  requirements?: string
  benefits?: string | null
  contract_type?: string | null
  working_hours?: string | null
  soft_skills?: string[] | null
  languages_required?: string | null
  skills_required: string[]
  posted_at?: string
  source?: string
  match_score?: number | null
  match_level?: string | null
}

export interface User {
  id: string
  email: string
  full_name: string
  role: 'candidate' | 'employer' | 'admin'
  company_id?: number | null
}

export interface MatchExplain {
  job_id: number
  score: number
  level: string
  components: Record<string, number>
  matched_skills: string[]
  missing_skills: string[]
  explanation: string
  model_version: string
}

export interface Recommendation {
  job: Job
  score: number
  level: string
  matched_skills: string[]
  missing_skills: string[]
  reason: string
}

export interface Health {
  score: number
  breakdown: Record<string, number>
  issues: string[]
}

export interface ParsedCvData {
  full_name?: string
  title?: string
  contacts?: {
    email?: string | null
    phone?: string | null
    linkedin?: string | null
    github?: string | null
    address?: string | null
  }
  summary?: string
  education?: Array<
    | string
    | {
        degree?: string
        school?: string
        period?: string
        gpa?: string
        honors?: string
      }
  >
  experience?: Array<
    | string
    | {
        position?: string
        company?: string
        period?: string
        location?: string
        responsibilities?: string[]
      }
  >
  projects?: Array<{
    name: string
    role?: string
    tech_stack?: string
    description?: string
  }>
  skills?: string[]
  soft_skills?: string[]
  languages?: string[]
  certifications?: string[]
  experience_years?: number
  gpa?: number | null
  sections?: Record<string, string>
}

export interface Profile {
  id: number
  full_name: string
  email?: string
  major?: string
  gpa?: number
  exp_years?: number
  education?: string
  location?: string
  expected_salary?: number
  skills: { name: string; source: string }[]
  latest_cv?: {
    id: number
    filename: string
    health_score: number
    health_issues_json: Health
    parsed_json?: ParsedCvData | null
    raw_text?: string
    created_at: string
  } | null
}

export interface Application {
  id: number
  job_id: number
  title: string
  company_name?: string
  location?: string
  status: string
  match_score?: number | null
  source: string
  applied_at: string
}

export interface CvSuggestion {
  content: { summary: string; add_keywords: string[]; rewrite_bullets: string[]; priority_fixes: string[] }
  source: 'gemini' | 'fallback'
  cached?: boolean
}

class ApiClient {
  private token: string | null = null

  constructor(private baseUrl: string) {
    if (typeof window !== 'undefined') this.token = localStorage.getItem('auth_token')
  }

  setToken(token: string) {
    this.token = token
    localStorage.setItem('auth_token', token)
  }

  clearToken() {
    this.token = null
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user')
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    if (typeof window !== 'undefined' && !this.token) this.token = localStorage.getItem('auth_token')
    const headers: Record<string, string> = { ...(options.headers as Record<string, string>) }
    if (!(options.body instanceof FormData)) headers['Content-Type'] = 'application/json'
    if (this.token) headers['Authorization'] = `Bearer ${this.token}`
    const res = await fetch(`${this.baseUrl}${endpoint}`, { ...options, headers })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Request failed' }))
      throw new Error(typeof err.detail === 'string' ? err.detail : 'API request failed')
    }
    return res.json()
  }

  private qs(params: Record<string, string | number | undefined | null>) {
    const q = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => v !== undefined && v !== null && v !== '' && q.set(k, String(v)))
    const s = q.toString()
    return s ? `?${s}` : ''
  }

  // auth
  async login(email: string, password: string) {
    const data = await this.request<{ access_token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    this.setToken(data.access_token)
    return data
  }
  register(data: { email: string; password: string; full_name: string; phone?: string }) {
    return this.request<User>('/auth/register', { method: 'POST', body: JSON.stringify(data) })
  }
  getCurrentUser() {
    return this.request<User>('/users/me')
  }

  // jobs
  getJobs(p: { search?: string; category?: string; location?: string; level?: string; page?: number; limit?: number }) {
    return this.request<{ items: Job[]; total: number; page: number; limit: number }>(`/jobs${this.qs(p)}`)
  }
  getJob(id: number | string) {
    return this.request<Job>(`/jobs/${id}`)
  }

  // candidate
  getProfile() {
    return this.request<Profile>('/candidate/profile')
  }
  updateProfile(data: Partial<Omit<Profile, 'id' | 'skills' | 'latest_cv'>> & { skills?: string[] }) {
    return this.request<Profile>('/candidate/profile', { method: 'PUT', body: JSON.stringify(data) })
  }
  uploadCV(file: File) {
    const fd = new FormData()
    fd.append('file', file)
    return this.request<{ cv_id: number; parsed: { skills: string[]; experience_years: number; gpa?: number; education: string[] }; health: Health; matches_updated: number }>(
      '/cv/upload',
      { method: 'POST', body: fd }
    )
  }
  loadDemoPreset(preset: 'realistic' | 'perfect' | 'needs_work' = 'realistic') {
    return this.request<{ cv_id: number; filename: string; parsed: ParsedCvData; health: Health; matches_updated: number }>(
      `/cv/demo-preset?preset=${preset}`,
      { method: 'POST' }
    )
  }
  getRecommendations(k = 20) {
    return this.request<{ model_version: string; recommendations: Recommendation[] }>(`/recommendations?k=${k}`)
  }
  getMatch(jobId: number | string) {
    return this.request<MatchExplain>(`/jobs/${jobId}/match`)
  }
  suggestCV(jobId: number | string) {
    return this.request<CvSuggestion>(`/cv/suggest?job_id=${jobId}`, { method: 'POST' })
  }
  getSalary(jobId: number | string) {
    return this.request<{ unit: string; segment: { n: number; p25: number; p50: number; p75: number }; model_prediction: number | null; estimate: number }>(
      `/salary/estimate?job_id=${jobId}`
    )
  }

  // applications
  getApplications() {
    return this.request<Application[]>('/applications')
  }
  apply(job_id: number, source: 'recommend' | 'search') {
    return this.request<{ id: number; status: string; match_score: number | null }>('/applications', {
      method: 'POST',
      body: JSON.stringify({ job_id, source }),
    })
  }
  updateApplication(id: number, status: string) {
    return this.request<{ id: number; status: string }>(`/applications/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    })
  }

  // employer
  getEmployerJobs() {
    return this.request<(Job & { n_applications: number })[]>('/employer/jobs')
  }
  createEmployerJob(data: Record<string, unknown>) {
    return this.request<{ id: number }>('/employer/jobs', { method: 'POST', body: JSON.stringify(data) })
  }
  getJobCandidates(jobId: number | string, missing_skill?: string) {
    return this.request<{
      job: { id: number; title: string }
      candidates: {
        application_id: number
        candidate_id: number
        full_name: string
        status: string
        exp_years: number
        score: number
        level: string
        matched_skills: string[]
        missing_skills: string[]
        explanation: string
      }[]
    }>(`/employer/jobs/${jobId}/candidates${this.qs({ missing_skill })}`)
  }
  getKpi() {
    return this.request<{
      company: string
      n_active_jobs: number
      funnel: { applied: number; screening: number; interview: number; offer: number; avg_match: string | null; avg_days_to_response: string | null }
      top_missing_skills: { skill: string; n_missing: number }[]
    }>('/employer/kpi')
  }

  // admin / market
  getAdminStats() {
    return this.request<{
      seed_mode: string
      counts: Record<string, number>
      job_sources: Record<string, number>
      applications_by_origin: Record<string, number>
      candidates_by_origin: { sim: number; real: number }
      note: string
    }>('/admin/stats')
  }
  getMarketStats() {
    return this.request<{
      skill_supply_demand: { skill: string; n_candidates: number; n_jobs: number }[]
      salary_by_category: { category: string; p50: number; n: number }[]
      salary_by_level: { level: string; p50: number; n: number }[]
    }>('/market/stats')
  }
}

export const api = new ApiClient(API_BASE_URL)
