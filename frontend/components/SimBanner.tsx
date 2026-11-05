import { Info } from 'lucide-react'

export default function SimBanner({ children }: { children?: React.ReactNode }) {
  return (
    <div
      role="note"
      className="mb-6 border border-rose-200/80 bg-gradient-to-r from-rose-50/80 via-pink-50/50 to-blue-50/60 text-slate-800 text-xs sm:text-sm rounded-2xl p-4 shadow-xs flex items-start gap-3"
    >
      <div className="p-1 rounded-full bg-rose-100 text-rose-600 shrink-0 mt-0.5">
        <Info className="w-4 h-4" />
      </div>
      <div className="leading-relaxed">
        <strong className="text-rose-900 font-semibold">Dữ liệu minh họa hệ thống:</strong>{' '}
        <span className="text-slate-700">
          {children ??
            'Ứng viên, đơn ứng tuyển, kết quả qua vòng và công ty là dữ liệu mô phỏng để minh họa tính năng; toàn bộ tin tuyển dụng, kỹ năng yêu cầu và mức lương được trích xuất từ dữ liệu thị trường thực tế VietJobs.'}
        </span>
      </div>
    </div>
  )
}
