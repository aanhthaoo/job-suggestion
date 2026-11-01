// API client configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export interface Job {
  id: string
  title: string
  company_id: string
  company_name?: string
  description: string
  requirements: string
  skills_required: string[]
  location: string
  salary_min?: number
  salary_max?: number
  currency: string
  experience_years: number
  job_type: 'fulltime' | 'parttime' | 'internship'
  work_mode: 'onsite' | 'remote' | 'hybrid'
  status: 'active' | 'closed' | 'draft'
  posted_at: string
  match_score?: number
  match_reason?: any
}

export interface User {
  id: string
  email: string
  full_name: string
  phone?: string
  role: 'candidate' | 'hr' | 'admin'
  created_at: string
}

export interface CV {
  id: string
  user_id: string
  file_path: string
  file_name: string
  parsed_data?: {
    skills: string[]
    experience_years: number
    education: string[]
  }
  created_at: string
}

export interface Application {
  id: string
  job_id: string
  user_id: string
  cv_id: string
  cover_letter?: string
  status: 'submitted' | 'reviewed' | 'interviewing' | 'accepted' | 'rejected'
  applied_at: string
  job?: Job
}

class ApiClient {
  private baseUrl: string
  private token: string | null = null

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
    // Try to get token from localStorage on client side
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token')
    }
  }

  setToken(token: string) {
    this.token = token
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token)
    }
  }

  clearToken() {
    this.token = null
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token')
    }
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    }

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }))
      throw new Error(error.detail || 'API request failed')
    }

    return response.json()
  }

  // Auth endpoints
  async login(email: string, password: string) {
    const data = await this.request<{ access_token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    this.setToken(data.access_token)
    return data
  }

  async register(data: { email: string; password: string; full_name: string; phone?: string }) {
    return this.request<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getCurrentUser() {
    return this.request<User>('/users/me')
  }

  // Jobs endpoints
  async getJobs(params?: {
    search?: string
    location?: string
    job_type?: string
    work_mode?: string
    min_salary?: number
    max_salary?: number
    page?: number
    limit?: number
  }) {
    const query = new URLSearchParams()
    if (params?.search) query.set('search', params.search)
    if (params?.location) query.set('location', params.location)
    if (params?.job_type) query.set('job_type', params.job_type)
    if (params?.work_mode) query.set('work_mode', params.work_mode)
    if (params?.min_salary) query.set('min_salary', String(params.min_salary))
    if (params?.max_salary) query.set('max_salary', String(params.max_salary))
    if (params?.page) query.set('page', String(params.page))
    if (params?.limit) query.set('limit', String(params.limit))

    const queryString = query.toString()
    return this.request<{ items: Job[]; total: number; page: number; limit: number }>(
      `/jobs${queryString ? `?${queryString}` : ''}`
    )
  }

  async getJob(id: string) {
    return this.request<Job>(`/jobs/${id}`)
  }

  // Applications endpoints
  async getApplications() {
    return this.request<Application[]>('/applications')
  }

  async applyToJob(data: { job_id: string; cv_id: string; cover_letter?: string }) {
    return this.request<Application>('/applications', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Saved jobs endpoints
  async getSavedJobs() {
    return this.request<Job[]>('/saved-jobs')
  }

  async saveJob(job_id: string) {
    return this.request<{ id: string }>('/saved-jobs', {
      method: 'POST',
      body: JSON.stringify({ job_id }),
    })
  }

  async unsaveJob(job_id: string) {
    return this.request<void>(`/saved-jobs/${job_id}`, {
      method: 'DELETE',
    })
  }

  // CV endpoints
  async uploadCV(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await fetch(`${this.baseUrl}/users/me/cv/upload`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${this.token}`,
      },
      body: formData,
    })

    if (!response.ok) {
      throw new Error('Upload failed')
    }

    return response.json()
  }

  async getCVs() {
    return this.request<CV[]>('/users/me/cvs')
  }

  // Admin endpoints
  async getAdminStats() {
    return this.request<{
      postgres_status: string
      redis_status: string
      celery_status: string
      total_jobs: number
      total_users: number
      today_applications: number
    }>('/admin/stats')
  }

  async getTasks() {
    return this.request<any[]>('/admin/tasks')
  }

  async triggerSync(sourceId?: string) {
    return this.request<{ task_id: string }>('/admin/tasks/sync-now', {
      method: 'POST',
      body: JSON.stringify({ source_id: sourceId }),
    })
  }
}

export const api = new ApiClient(API_BASE_URL)
