import Link from 'next/link'
import { MapPin, Wallet, Briefcase, Globe, Gift } from 'lucide-react'
import type { Job } from '@/lib/api'
import { formatSalary } from '@/lib/utils'
import ScoreBadge from './ScoreBadge'

export default function JobCard({ job, reason, score, level }: { job: Job; reason?: string; score?: number | null; level?: string | null }) {
  const s = score ?? job.match_score
  return (
    <Link
      href={`/jobs/${job.id}`}
      className="group block bg-white rounded-2xl border border-slate-200/80 p-5 hover:border-pink-300 hover:shadow-lg hover:shadow-pink-500/5 hover:-translate-y-0.5 transition-all duration-200"
    >
      <div className="flex justify-between items-start gap-3">
        <div className="min-w-0 flex-1">
          <h3 className="font-bold text-slate-900 text-lg group-hover:text-blue-600 transition-colors truncate">
            {job.title}
          </h3>
          <p className="text-sm text-slate-500 font-medium mt-0.5">{job.company_name}</p>
        </div>
        <ScoreBadge score={s} level={level ?? job.match_level} />
      </div>

      <div className="flex flex-wrap items-center gap-2.5 mt-3.5 text-xs">
        <span className="flex items-center text-slate-700 font-medium bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-100">
          <MapPin className="w-3.5 h-3.5 mr-1 text-slate-400" />
          {job.location}
        </span>
        <span className="flex items-center text-blue-700 font-bold bg-blue-50/80 px-2.5 py-1 rounded-lg border border-blue-100">
          <Wallet className="w-3.5 h-3.5 mr-1 text-blue-500" />
          {formatSalary(job.salary_min, job.salary_max)}
        </span>
        {job.contract_type && (
          <span className="flex items-center text-pink-700 font-medium bg-pink-50/80 px-2.5 py-1 rounded-lg border border-pink-100">
            <Briefcase className="w-3.5 h-3.5 mr-1 text-pink-400" />
            {job.contract_type}
          </span>
        )}
        {job.level && (
          <span className="px-2.5 py-1 bg-indigo-50 text-indigo-700 rounded-lg font-medium border border-indigo-100">
            {job.level}
          </span>
        )}
        {job.languages_required && (
          <span className="flex items-center text-teal-700 font-medium bg-teal-50 px-2.5 py-1 rounded-lg border border-teal-100">
            <Globe className="w-3.5 h-3.5 mr-1 text-teal-500" />
            {job.languages_required}
          </span>
        )}
      </div>

      {job.skills_required?.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-3">
          {job.skills_required.slice(0, 5).map((sk) => (
            <span key={sk} className="px-2.5 py-0.5 bg-slate-100/90 text-slate-700 text-[11px] rounded-md font-medium">
              {sk}
            </span>
          ))}
          {job.skills_required.length > 5 && (
            <span className="text-[11px] text-slate-400 self-center font-medium">+{job.skills_required.length - 5}</span>
          )}
        </div>
      )}

      {job.benefits && (
        <div className="mt-3.5 flex items-center text-xs text-rose-800 bg-gradient-to-r from-rose-50/80 via-pink-50/50 to-white px-3 py-1.5 rounded-xl border border-rose-100/80 truncate">
          <Gift className="w-3.5 h-3.5 mr-1.5 shrink-0 text-pink-500" />
          <span className="truncate">{job.benefits.split('\n')[0].replace(/^[•\-\*]\s*/, '')}</span>
        </div>
      )}

      {reason && (
        <p className="mt-3 text-xs text-slate-700 bg-gradient-to-r from-blue-50/70 via-indigo-50/40 to-pink-50/40 rounded-xl px-3 py-2 border border-blue-100/70">
          {reason}
        </p>
      )}
    </Link>
  )
}
