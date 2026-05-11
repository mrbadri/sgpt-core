import type { Metadata } from "next"
import Navbar from "@/components/landing/Navbar"
import Hero from "@/components/landing/Hero"
import Pricing from "@/components/landing/Pricing"
import Footer from "@/components/landing/Footer"
import BottomNav from "@/components/landing/BottomNav"

export const metadata: Metadata = {
  title: "StudyGPT — هوش مصنوعی تخصصی کنکور",
  description:
    "با StudyGPT سوالات کنکور را دقیقاً به روش کتاب‌های درسی ایران حل کن. تخصصی‌ترین هوش مصنوعی برای دانش‌آموزان ایرانی.",
}

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-background pb-20 md:pb-0">
      <Navbar />
      <Hero />
      <Pricing />
      <Footer />
      <BottomNav />
    </main>
  )
}
