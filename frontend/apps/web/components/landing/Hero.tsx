"use client"

import { motion } from "framer-motion"
import { AnimatedGridPattern } from "@workspace/ui/components/animated-grid-pattern"
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
    <section
      id="hero"
      className="relative flex min-h-screen flex-col justify-center overflow-hidden px-4 pt-24 pb-16"
    >
      {/* Animated grid background */}
      <AnimatedGridPattern
        numSquares={30}
        maxOpacity={0.08}
        duration={3}
        repeatDelay={1}
        className="[mask-image:radial-gradient(ellipse_80%_60%_at_50%_0%,black_40%,transparent_100%)] fill-foreground/[0.04] stroke-foreground/[0.06] md:[mask-image:radial-gradient(ellipse_60%_80%_at_50%_0%,black_50%,transparent_100%)]"
      />

      {/* Background gradient blobs */}
      <div
        aria-hidden
        className="pointer-events-none absolute start-1/2 top-0 h-[600px] w-[800px] -translate-x-1/2 rounded-full opacity-10 blur-3xl dark:opacity-5"
        style={{
          background:
            "radial-gradient(ellipse, oklch(0.62 0.22 255), transparent 70%)",
        }}
      />

      <div className="relative mx-auto w-full max-w-4xl text-center">
        <motion.div
          variants={stagger}
          initial="hidden"
          animate="visible"
          className="flex flex-col items-center gap-6"
        >
          {/* Eyebrow badge */}
          <motion.div variants={fadeUp}>
            <span className="inline-flex items-center gap-2 rounded-full border border-brand/20 bg-brand-muted px-4 py-1.5 text-sm font-medium text-brand">
              <span>✨</span>
              <span>هوش مصنوعی تخصصی کنکور ایران</span>
            </span>
          </motion.div>

          {/* Main headline */}
          <motion.h1
            variants={fadeUp}
            className="text-4xl leading-tight font-black tracking-tight md:text-6xl lg:text-7xl"
          >
            چت‌جی‌پی‌تی کتاب درسی تو رو نخونده،
            <br />
            <span className="text-brand">ولی StudyGPT بلده!</span>
          </motion.h1>

          {/* Sub-headline */}
          <motion.p
            variants={fadeUp}
            className="max-w-2xl text-lg leading-relaxed text-muted-foreground md:text-xl"
          >
            سوالات زیست، ریاضی، فیزیک، شیمی و زبان کنکور رو{" "}
            <span className="font-semibold text-foreground">
              دقیقاً مطابق کتاب درسی ایران
            </span>{" "}
            حل کن و آماده کنکور سراسری بشو.
          </motion.p>

          {/* CTA buttons */}
          <motion.div
            variants={fadeUp}
            className="flex w-full flex-col justify-center gap-3 sm:w-auto sm:flex-row"
          >
            <motion.a
              href="/register"
              whileHover={{ scale: 1.03, y: -2 }}
              whileTap={{ scale: 0.97 }}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-brand px-8 py-3.5 text-base font-bold text-brand-foreground shadow-lg shadow-brand/30 transition-colors hover:bg-brand/90"
            >
              همین الان شروع کن — رایگانه!
            </motion.a>
            <motion.a
              href="#features"
              whileHover={{ scale: 1.02, y: -1 }}
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-border px-8 py-3.5 text-base font-medium transition-colors hover:bg-muted/50"
            >
              <span>ببین چطور کار می‌کنه</span>
              <span>▶</span>
            </motion.a>
          </motion.div>
        </motion.div>
      </div>

      {/* Comparison Section */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
        className="relative mx-auto mt-32 w-full max-w-5xl"
        id="features"
      >
        {/* Section glow */}
        <div
          aria-hidden
          className="pointer-events-none absolute -top-24 left-1/2 h-[280px] w-[500px] -translate-x-1/2 rounded-full opacity-[0.08] blur-3xl"
          style={{
            background:
              "radial-gradient(ellipse, oklch(0.70 0.16 185), oklch(0.62 0.22 255), transparent 70%)",
          }}
        />

        {/* Header */}
        <div className="relative mb-12 text-center">
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-teal-500/25 bg-teal-500/8 px-4 py-1.5 text-xs font-semibold tracking-wide text-teal-400">
            <span className="text-sm">🧬</span>
            زیست‌شناسی کنکور تجربی
          </div>
          <h2 className="text-3xl font-black tracking-tight md:text-4xl">
            یه سوال، دو جواب —{" "}
            <span className="relative inline-block">
              <span className="relative z-10 text-brand">خودت قضاوت کن</span>
              <span
                aria-hidden
                className="absolute inset-x-0 bottom-0.5 -z-0 h-3 rounded-sm opacity-20"
                style={{ background: "oklch(0.62 0.22 255)" }}
              />
            </span>
          </h2>
          <p className="mx-auto mt-3 max-w-lg text-sm leading-relaxed text-muted-foreground md:text-base">
            همان سوال زیست، یک‌بار با هوش مصنوعی عمومی، یک‌بار با StudyGPT —{" "}
            <span className="font-semibold text-foreground">تفاوت رو ببین</span>
          </p>
        </div>

        <ComparisonTable />
      </motion.div>
    </section>
  )
}
