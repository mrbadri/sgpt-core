"use client"

import { motion } from "framer-motion"
import ComparisonTable from "./ComparisonTable"

const fadeUp = {
  hidden: { opacity: 0, y: 32 },
  visible: { opacity: 1, y: 0 },
}

const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.12, delayChildren: 0.1 } },
}

export default function Hero() {
  return (
    <section id="hero" className="relative min-h-screen flex flex-col justify-center pt-24 pb-16 px-4 overflow-hidden">
      {/* Background gradient blobs */}
      <div
        aria-hidden
        className="absolute top-0 start-1/2 -translate-x-1/2 w-[800px] h-[600px] rounded-full opacity-10 dark:opacity-5 blur-3xl pointer-events-none"
        style={{ background: "radial-gradient(ellipse, oklch(0.62 0.22 255), transparent 70%)" }}
      />

      <div className="relative max-w-4xl mx-auto w-full text-center">
        <motion.div
          variants={stagger}
          initial="hidden"
          animate="visible"
          className="flex flex-col items-center gap-6"
        >
          {/* Eyebrow badge */}
          <motion.div variants={fadeUp}>
            <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-brand-muted text-brand text-sm font-medium border border-brand/20">
              <span>✨</span>
              <span>هوش مصنوعی تخصصی کنکور ایران</span>
            </span>
          </motion.div>

          {/* Main headline */}
          <motion.h1
            variants={fadeUp}
            className="text-4xl md:text-6xl lg:text-7xl font-black leading-tight tracking-tight"
          >
            چت‌جی‌پی‌تی کتاب درسی تو رو نخونده،
            <br />
            <span className="text-brand">ولی StudyGPT بلده!</span>
          </motion.h1>

          {/* Sub-headline */}
          <motion.p
            variants={fadeUp}
            className="text-lg md:text-xl text-muted-foreground max-w-2xl leading-relaxed"
          >
            سوالات ریاضی، فیزیک، شیمی و زبان کنکور رو دقیقاً به روش کتاب‌های درسی ایران حل کن
            و آماده امتحان نهایی و کنکور سراسری بشو.
          </motion.p>

          {/* CTA buttons */}
          <motion.div variants={fadeUp} className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto justify-center">
            <motion.a
              href="/register"
              whileHover={{ scale: 1.03, y: -2 }}
              whileTap={{ scale: 0.97 }}
              className="inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl bg-brand text-brand-foreground font-bold text-base shadow-lg shadow-brand/30 hover:bg-brand/90 transition-colors"
            >
              همین الان شروع کن — رایگانه!
            </motion.a>
            <motion.a
              href="#features"
              whileHover={{ scale: 1.02, y: -1 }}
              className="inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl border border-border font-medium text-base hover:bg-muted/50 transition-colors"
            >
              <span>ببین چطور کار می‌کنه</span>
              <span>▶</span>
            </motion.a>
          </motion.div>

          {/* Social proof */}
          <motion.p variants={fadeUp} className="text-sm text-muted-foreground">
            بیش از <span className="font-bold text-foreground">۵,۰۰۰</span> دانش‌آموز در حال استفاده
          </motion.p>
        </motion.div>
      </div>

      {/* Comparison Section */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
        className="relative max-w-5xl mx-auto w-full mt-24"
        id="features"
      >
        <div className="text-center mb-10">
          <h2 className="text-2xl md:text-3xl font-black">چرا StudyGPT؟</h2>
          <p className="text-muted-foreground mt-2 text-sm md:text-base">
            مقایسه پاسخ‌های هوش مصنوعی عمومی در برابر StudyGPT تخصصی
          </p>
        </div>
        <ComparisonTable />
      </motion.div>
    </section>
  )
}
