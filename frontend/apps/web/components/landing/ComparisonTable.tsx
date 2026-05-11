"use client"

import { motion } from "framer-motion"
import { comparisonData } from "@/lib/landing-data"

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.5, ease: [0.22, 1, 0.36, 1] },
  }),
}

export default function ComparisonTable() {
  const row = comparisonData[0]

  return (
    <div className="w-full">
      {/* Prompt chip */}
      <div className="flex justify-center mb-6">
        <div className="inline-flex items-center gap-2.5 rounded-2xl border border-border bg-muted/40 px-5 py-2.5 text-sm text-muted-foreground backdrop-blur-sm">
          <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-teal-500/15 text-teal-400 text-xs font-bold">🧬</span>
          <span className="font-medium text-foreground">{row.subject}</span>
          <span className="h-3.5 w-px bg-border" />
          <span className="font-mono text-xs">{row.prompt}</span>
        </div>
      </div>

      {/* Two-panel card */}
      <div className="relative grid grid-cols-1 md:grid-cols-2 rounded-3xl border border-border bg-card overflow-hidden shadow-xl shadow-black/5">

        {/* Divider line — desktop only */}
        <div className="absolute inset-y-0 left-1/2 hidden md:block w-px bg-border" />

        {/* General AI panel */}
        <motion.div
          variants={fadeUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          custom={0}
          className="relative flex flex-col gap-4 p-7 border-b md:border-b-0 border-border"
        >
          {/* Subtle red tint blob */}
          <div
            aria-hidden
            className="absolute top-0 start-0 w-48 h-48 rounded-full blur-3xl opacity-[0.06] pointer-events-none"
            style={{ background: "oklch(0.65 0.22 27)" }}
          />

          <div className="flex items-center gap-2.5">
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-red-500/10 text-red-400 text-sm font-black">✗</span>
            <span className="text-sm font-bold text-foreground/80">{row.generalAI.title}</span>
          </div>

          <ul className="space-y-2.5">
            {row.generalAI.points.map((point, i) => (
              <motion.li
                key={i}
                variants={fadeUp}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                custom={i}
                className="flex items-start gap-2.5"
              >
                <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-red-500/10 text-red-400 text-[10px]">✗</span>
                <span className="text-sm leading-relaxed text-foreground/60">{point}</span>
              </motion.li>
            ))}
          </ul>
        </motion.div>

        {/* StudyGPT panel */}
        <motion.div
          variants={fadeUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          custom={1}
          className="relative flex flex-col gap-4 p-7"
        >
          {/* Brand glow blob */}
          <div
            aria-hidden
            className="absolute top-0 end-0 w-48 h-48 rounded-full blur-3xl opacity-[0.08] pointer-events-none"
            style={{ background: "oklch(0.72 0.18 145)" }}
          />

          <div className="flex items-center gap-2.5">
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-400 text-sm font-black">✓</span>
            <span className="text-sm font-bold text-foreground">{row.studyGPT.title}</span>
          </div>

          <ul className="space-y-2.5">
            {row.studyGPT.points.map((point, i) => (
              <motion.li
                key={i}
                variants={fadeUp}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                custom={i}
                className="flex items-start gap-2.5"
              >
                <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-400 text-[10px]">✓</span>
                <span className="text-sm leading-relaxed text-foreground/90 font-medium">{point}</span>
              </motion.li>
            ))}
          </ul>
        </motion.div>
      </div>
    </div>
  )
}
