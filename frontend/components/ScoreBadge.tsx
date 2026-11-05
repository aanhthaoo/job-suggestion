import { cn } from '@/lib/utils'
import { Sparkles, CheckCircle2, AlertCircle } from 'lucide-react'

const CONFIG: Record<string, { label: string; cls: string; icon: any }> = {
  cao: {
    label: 'Khớp cao',
    cls: 'bg-gradient-to-r from-emerald-50 to-teal-50 text-emerald-700 border-emerald-200/80 shadow-xs',
    icon: Sparkles
  },
  'trung bình': {
    label: 'Khớp vừa',
    cls: 'bg-gradient-to-r from-blue-50 to-indigo-50 text-blue-700 border-blue-200/80 shadow-xs',
    icon: CheckCircle2
  },
  thấp: {
    label: 'Khớp thấp',
    cls: 'bg-gradient-to-r from-rose-50 to-pink-50 text-rose-700 border-rose-200/80 shadow-xs',
    icon: AlertCircle
  }
}

export default function ScoreBadge({ score, level }: { score?: number | null; level?: string | null }) {
  if (score === undefined || score === null) return null
  const lv = level || (score >= 0.75 ? 'cao' : score >= 0.55 ? 'trung bình' : 'thấp')
  const item = CONFIG[lv] || CONFIG['thấp']
  const Icon = item.icon

  return (
    <span
      title="Matching Score do mô hình AI tính toán tự động"
      className={cn(
        'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border transition-transform hover:scale-105',
        item.cls
      )}
    >
      <Icon className="w-3.5 h-3.5 shrink-0" />
      <span>{Math.round(score * 100)}%</span>
      <span className="text-[10px] opacity-80 font-normal">({item.label})</span>
    </span>
  )
}
