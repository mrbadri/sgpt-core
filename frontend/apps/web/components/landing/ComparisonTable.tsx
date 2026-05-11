import { comparisonData } from "@/lib/landing-data"

const tagLabels: Record<string, string> = {
  math: "ریاضی",
  physics: "فیزیک",
  chemistry: "شیمی",
  english: "زبان",
}

const tagColors: Record<string, string> = {
  math: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
  physics: "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300",
  chemistry: "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300",
  english: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
}

export default function ComparisonTable() {
  return (
    <div className="w-full">
      {/* Column headers */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div className="flex items-center gap-2 justify-center px-4 py-2 rounded-xl bg-danger/10 text-danger font-bold text-sm">
          <span>✗</span>
          <span>هوش مصنوعی عمومی (ChatGPT، Gemini)</span>
        </div>
        <div className="flex items-center gap-2 justify-center px-4 py-2 rounded-xl bg-success/10 text-success font-bold text-sm">
          <span>✓</span>
          <span>StudyGPT — تخصصی کنکور ایران</span>
        </div>
      </div>

      <div className="space-y-3">
        {comparisonData.map((row, i) => (
          <div key={i} className="grid grid-cols-1 md:grid-cols-2 gap-0 md:gap-4 rounded-2xl overflow-hidden border border-border">
            {/* Subject badge — spans both on mobile */}
            <div className="md:hidden flex items-center gap-2 px-4 pt-3 pb-1">
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${tagColors[row.tag]}`}>
                {tagLabels[row.tag]}
              </span>
              <span className="text-sm font-semibold">{row.subject}</span>
            </div>

            {/* General AI cell */}
            <div className="px-4 py-3 bg-danger/5 border-b md:border-b-0 md:border-e border-border">
              <div className="hidden md:flex items-center gap-2 mb-1">
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${tagColors[row.tag]}`}>
                  {tagLabels[row.tag]}
                </span>
                <span className="text-xs font-semibold text-foreground/70">{row.subject}</span>
              </div>
              <p className="text-sm text-danger/90 leading-relaxed">{row.generalAI}</p>
            </div>

            {/* StudyGPT cell */}
            <div className="px-4 py-3 bg-success/5">
              <div className="hidden md:block mb-1 h-5" />
              <p className="text-sm text-success/90 leading-relaxed font-medium">{row.studyGPT}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
