"use client"

import { motion } from "framer-motion"
import { Check } from "lucide-react"
import type { PricingTier, BillingPeriod } from "@/lib/landing-data"
import { formatToman } from "@/lib/landing-data"

type Props = {
  tier: PricingTier
  period: BillingPeriod
  termsAccepted: boolean
}

export default function PricingCard({ tier, period, termsAccepted }: Props) {
  const price = period === "monthly" ? tier.price.monthly : tier.price.quarterly
  const isHighlighted = tier.highlighted

  const cardContent = (
    <div className={`relative flex flex-col h-full rounded-2xl p-6 ${
      isHighlighted
        ? "bg-brand text-brand-foreground shadow-2xl shadow-brand/30"
        : "bg-card border border-border"
    }`}>
      {tier.badge && (
        <span className="absolute -top-3 start-1/2 -translate-x-1/2 bg-amber-400 text-amber-900 text-xs font-bold px-3 py-1 rounded-full whitespace-nowrap">
          {tier.badge}
        </span>
      )}

      <div className="mb-6">
        <h3 className={`text-lg font-bold ${isHighlighted ? "text-brand-foreground" : "text-foreground"}`}>
          {tier.name}
        </h3>
        <p className={`text-sm mt-1 ${isHighlighted ? "text-brand-foreground/70" : "text-muted-foreground"}`}>
          {tier.description}
        </p>
      </div>

      <div className="mb-6">
        <div className="flex items-baseline gap-1">
          <span className={`text-4xl font-black ${isHighlighted ? "text-brand-foreground" : "text-foreground"}`}>
            {price === 0 ? "رایگان" : new Intl.NumberFormat("fa-IR").format(price)}
          </span>
          {price > 0 && (
            <span className={`text-sm ${isHighlighted ? "text-brand-foreground/70" : "text-muted-foreground"}`}>
              تومان / ماه
            </span>
          )}
        </div>
        {period === "quarterly" && price > 0 && (
          <p className={`text-xs mt-1 ${isHighlighted ? "text-brand-foreground/60" : "text-muted-foreground"}`}>
            پرداخت {formatToman(price * 3)} برای ۳ ماه
          </p>
        )}
      </div>

      <ul className="space-y-3 mb-8 flex-1">
        {tier.features.map((feature, i) => (
          <li key={i} className="flex items-start gap-2 text-sm">
            <Check
              className={`w-4 h-4 mt-0.5 shrink-0 ${isHighlighted ? "text-brand-foreground" : "text-success"}`}
            />
            <span className={isHighlighted ? "text-brand-foreground/90" : "text-foreground/80"}>
              {feature}
            </span>
          </li>
        ))}
      </ul>

      <button
        disabled={!termsAccepted && price > 0}
        className={`w-full py-3 rounded-xl font-bold text-sm transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed ${
          isHighlighted
            ? "bg-white text-brand hover:bg-brand-foreground/90"
            : "bg-brand text-brand-foreground hover:bg-brand/90"
        }`}
      >
        {tier.cta}
      </button>
    </div>
  )

  if (isHighlighted) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1], delay: 0.1 }}
        whileHover={{ scale: 1.02, y: -4 }}
        className="relative"
      >
        {cardContent}
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
    >
      {cardContent}
    </motion.div>
  )
}
