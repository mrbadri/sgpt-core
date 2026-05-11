"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { pricingTiers, type BillingPeriod } from "@/lib/landing-data"
import PricingCard from "./PricingCard"

export default function Pricing() {
  const [period, setPeriod] = useState<BillingPeriod>("monthly")
  const [termsAccepted, setTermsAccepted] = useState(false)

  return (
    <section id="pricing" className="py-24 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl md:text-4xl font-black">قیمت‌گذاری</h2>
          <p className="text-muted-foreground mt-3 text-base">
            برنامه‌ای متناسب با نیاز خود انتخاب کن
          </p>
        </motion.div>

        {/* Billing toggle */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="flex items-center justify-center gap-4 mb-10"
        >
          <button
            onClick={() => setPeriod("monthly")}
            className={`text-sm font-medium transition-colors ${
              period === "monthly" ? "text-foreground" : "text-muted-foreground"
            }`}
          >
            ماهانه
          </button>

          {/* Toggle */}
          <button
            role="switch"
            aria-checked={period === "quarterly"}
            onClick={() => setPeriod(period === "monthly" ? "quarterly" : "monthly")}
            className={`relative w-12 h-6 rounded-full transition-colors duration-200 ${
              period === "quarterly" ? "bg-brand" : "bg-muted"
            }`}
          >
            <span
              className={`absolute top-1 w-4 h-4 rounded-full bg-white shadow-sm transition-all duration-200 ${
                period === "quarterly" ? "end-1" : "start-1"
              }`}
            />
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setPeriod("quarterly")}
              className={`text-sm font-medium transition-colors ${
                period === "quarterly" ? "text-foreground" : "text-muted-foreground"
              }`}
            >
              ۳ ماهه
            </button>
            <span className="text-xs font-bold text-success bg-success/10 px-2 py-0.5 rounded-full">
              ۲۷٪ تخفیف
            </span>
          </div>
        </motion.div>

        {/* Pricing cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl mx-auto">
          {pricingTiers.map((tier) => (
            <PricingCard
              key={tier.id}
              tier={tier}
              period={period}
              termsAccepted={termsAccepted}
            />
          ))}
        </div>

        {/* Terms checkbox */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.3 }}
          className="mt-8 flex justify-center"
        >
          <label className="flex items-start gap-3 max-w-md cursor-pointer group">
            <div className="relative mt-0.5 shrink-0">
              <input
                type="checkbox"
                checked={termsAccepted}
                onChange={(e) => setTermsAccepted(e.target.checked)}
                className="peer sr-only"
              />
              <div className="w-5 h-5 rounded border-2 border-border peer-checked:bg-brand peer-checked:border-brand transition-colors flex items-center justify-center">
                {termsAccepted && (
                  <svg className="w-3 h-3 text-white" viewBox="0 0 12 12" fill="none">
                    <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                )}
              </div>
            </div>
            <span className="text-sm text-muted-foreground leading-relaxed">
              با{" "}
              <a href="/terms" className="text-brand hover:underline font-medium">
                قوانین و مقررات استفاده
              </a>{" "}
              و{" "}
              <a href="/refund" className="text-brand hover:underline font-medium">
                سیاست استرداد وجه
              </a>{" "}
              مطالعه کرده و موافقم.
            </span>
          </label>
        </motion.div>

        {!termsAccepted && (
          <p className="text-center text-xs text-muted-foreground mt-3">
            برای فعال شدن دکمه خرید، تیک موافقت با قوانین را بزنید.
          </p>
        )}
      </div>
    </section>
  )
}
