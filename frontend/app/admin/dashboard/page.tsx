'use client'

import { useState, useEffect } from 'react'
import Header from '@/components/Header'
import { api } from '@/lib/api'
import { Database, Server, Activity, Users, Briefcase, FileText, RefreshCw } from 'lucide-react'
import mockJobs from '@/mock/jobs.json'

// Fallback data so the dashboard is presentable even when the backend is down.
const FALLBACK_STATS = {
  postgres_status: 'disconnected',
  redis_status: 'disconnected',
  celery_status: 'idle',
  total_jobs: mockJobs.length,
  total_users: 3,
  today_applications: 0,
}

const FALLBACK_TASKS = [
  {
    name: 'ingest_greenhouse_jobs',
    status: 'Idle',
    started_at: '-',
    duration: '-',
    result: 'Backend chưa kết nối',
  },
]

export default function AdminDashboard() {
  const [stats, setStats] = useState<any>(null)
  const [tasks, setTasks] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [offline, setOffline] = useState(false)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      const [statsData, tasksData] = await Promise.all([
        api.getAdminStats(),
        api.getTasks(),
      ])
      setStats(statsData)
      setTasks(tasksData)
      setOffline(false)
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
      setStats(FALLBACK_STATS)
      setTasks(FALLBACK_TASKS)
      setOffline(true)
    } finally {
      setLoading(false)
    }
  }

  const handleSyncNow = async () => {
    setSyncing(true)
    try {
      await api.triggerSync()
      setTimeout(loadDashboardData, 2000) // Reload after 2s
    } catch (error) {
      console.error('Failed to trigger sync:', error)
      setOffline(true)
    } finally {
      setSyncing(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="max-w-7xl mx-auto px-4 py-12 text-center">
          <p className="text-gray-600">Đang tải...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
          <button
            onClick={handleSyncNow}
            disabled={syncing}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center disabled:opacity-50"
          >
            <RefreshCw className={`w-5 h-5 mr-2 ${syncing ? 'animate-spin' : ''}`} />
            {syncing ? 'Đang đồng bộ...' : 'Đồng bộ ngay'}
          </button>
        </div>

        {offline && (
          <div className="mb-6 bg-yellow-50 border border-yellow-200 text-yellow-800 rounded-md px-4 py-3 text-sm">
            Không kết nối được backend — đang hiển thị dữ liệu demo. Khởi động backend để xem số liệu thực.
          </div>
        )}

        {/* System Health */}
        <h2 className="text-xl font-semibold text-gray-900 mb-4">System Health</h2>
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <Database className="w-8 h-8 text-green-600" />
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                stats?.postgres_status === 'connected' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {stats?.postgres_status === 'connected' ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900">PostgreSQL</h3>
            <p className="text-sm text-gray-600 mt-1">Database chính</p>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <Server className="w-8 h-8 text-green-600" />
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                stats?.redis_status === 'connected' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {stats?.redis_status === 'connected' ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Redis</h3>
            <p className="text-sm text-gray-600 mt-1">Message broker & cache</p>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <Activity className="w-8 h-8 text-green-600" />
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                stats?.celery_status === 'active' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {stats?.celery_status === 'active' ? 'Active' : 'Idle'}
              </span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Celery Worker</h3>
            <p className="text-sm text-gray-600 mt-1">Background tasks</p>
          </div>
        </div>

        {/* Quick Stats */}
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Thống kê nhanh</h2>
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Tổng số việc làm</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stats?.total_jobs || 0}</p>
              </div>
              <Briefcase className="w-12 h-12 text-blue-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Tổng số users</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stats?.total_users || 0}</p>
              </div>
              <Users className="w-12 h-12 text-purple-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Ứng tuyển hôm nay</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stats?.today_applications || 0}</p>
              </div>
              <FileText className="w-12 h-12 text-orange-600" />
            </div>
          </div>
        </div>

        {/* Recent Tasks */}
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Background Tasks gần đây</h2>
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Task Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Started At
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Duration
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Result
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {tasks.map((task, index) => (
                <tr key={index}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {task.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      task.status === 'Succeeded' 
                        ? 'bg-green-100 text-green-800'
                        : task.status === 'Failed'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {task.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {task.started_at}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {task.duration}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {task.result || '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
