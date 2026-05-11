"use client"

import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { Menu, X } from "lucide-react"
import { navItems } from "@/lib/landing-data"

export default function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    const onScroll = () => setIsScrolled(window.scrollY > 20)
    window.addEventListener("scroll", onScroll, { passive: true })
    return () => window.removeEventListener("scroll", onScroll)
  }, [])

  return (
    <header
      className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ${
        isScrolled ? "glass shadow-sm" : "bg-transparent"
      }`}
    >
      <nav className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo */}
        <a href="/" className="flex items-center gap-1 font-black text-xl select-none">
          <span className="text-foreground">Study</span>
          <span className="text-brand">GPT</span>
        </a>

        {/* Desktop links */}
        <div className="hidden md:flex items-center gap-6">
          {navItems.map((item) => (
            <motion.a
              key={item.href}
              href={item.href}
              whileHover={{ y: -2 }}
              transition={{ duration: 0.15 }}
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              {item.label}
            </motion.a>
          ))}
        </div>

        {/* CTA buttons */}
        <div className="hidden md:flex items-center gap-2">
          <motion.a
            href="/login"
            whileHover={{ y: -1 }}
            className="px-4 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all"
          >
            ورود به پنل
          </motion.a>
          <motion.a
            href="/register"
            whileHover={{ scale: 1.03, y: -1 }}
            whileTap={{ scale: 0.97 }}
            className="px-4 py-2 rounded-lg text-sm font-bold bg-brand text-brand-foreground hover:bg-brand/90 transition-colors shadow-md shadow-brand/25"
          >
            شروع کار
          </motion.a>
        </div>

        {/* Mobile menu button */}
        <button
          className="md:hidden p-2 rounded-lg hover:bg-muted/50 transition-colors"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="منو"
        >
          {menuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </nav>

      {/* Mobile menu */}
      {menuOpen && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          className="md:hidden glass border-t border-border px-4 py-4 space-y-3"
        >
          {navItems.map((item) => (
            <a
              key={item.href}
              href={item.href}
              onClick={() => setMenuOpen(false)}
              className="block py-2 text-sm font-medium text-foreground/80 hover:text-foreground"
            >
              {item.label}
            </a>
          ))}
          <div className="flex flex-col gap-2 pt-2 border-t border-border">
            <a href="/login" className="py-2.5 text-center rounded-xl border border-border text-sm font-medium">
              ورود به پنل
            </a>
            <a href="/register" className="py-2.5 text-center rounded-xl bg-brand text-brand-foreground text-sm font-bold">
              شروع کار — رایگانه!
            </a>
          </div>
        </motion.div>
      )}
    </header>
  )
}
