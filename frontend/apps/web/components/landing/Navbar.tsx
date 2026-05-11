"use client"

import { useEffect, useState } from "react"
import Image from "next/image"
import { motion } from "framer-motion"
import { Menu, X } from "lucide-react"
import { AnimatedThemeToggler } from "@workspace/ui/components/animated-theme-toggler"
import { navItems } from "@/lib/landing-data"

export default function Navbar() {
  const [isDark, setIsDark] = useState(false)
  const [isScrolled, setIsScrolled] = useState(false)

  useEffect(() => {
    const update = () =>
      setIsDark(document.documentElement.classList.contains("dark"))
    update()
    const observer = new MutationObserver(update)
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class"],
    })
    return () => observer.disconnect()
  }, [])
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    const onScroll = () => setIsScrolled(window.scrollY > 20)
    window.addEventListener("scroll", onScroll, { passive: true })
    return () => window.removeEventListener("scroll", onScroll)
  }, [])

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-300 ${
        isScrolled ? "glass shadow-sm" : "bg-transparent"
      }`}
    >
      <nav className="mx-auto grid h-16 max-w-6xl grid-cols-3 items-center px-4">
        {/* Logo — start column */}
        <a href="/" className="flex items-center select-none justify-self-start">
          <Image
            src={
              isDark ? "/logo/sgpt-logo-dark.svg" : "/logo/sgpt-logo-light.svg"
            }
            alt="StudyGPT"
            width={40}
            height={32}
            priority
          />
        </a>

        {/* Desktop links — center column */}
        <div className="hidden items-center justify-center gap-6 md:flex">
          {navItems.map((item) => (
            <motion.a
              key={item.href}
              href={item.href}
              whileHover={{ y: -2 }}
              transition={{ duration: 0.15 }}
              className="text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              {item.label}
            </motion.a>
          ))}
        </div>

        {/* Mobile: empty center placeholder */}
        <div className="md:hidden" />

        {/* Actions — end column */}
        <div className="flex items-center justify-end gap-2">
          <AnimatedThemeToggler className="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted/50 hover:text-foreground [&_svg]:h-4 [&_svg]:w-4" />
          <motion.a
            href="/login"
            whileHover={{ y: -1 }}
            className="hidden rounded-lg px-4 py-2 text-sm font-medium text-muted-foreground transition-all hover:bg-muted/50 hover:text-foreground md:block"
          >
            ورود به پنل
          </motion.a>
          <motion.a
            href="/register"
            whileHover={{ scale: 1.03, y: -1 }}
            whileTap={{ scale: 0.97 }}
            className="hidden rounded-lg bg-brand px-4 py-2 text-sm font-bold text-brand-foreground shadow-md shadow-brand/25 transition-colors hover:bg-brand/90 md:block"
          >
            شروع کار
          </motion.a>

          {/* Mobile hamburger */}
          <button
            className="rounded-lg p-2 transition-colors hover:bg-muted/50 md:hidden"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="منو"
          >
            {menuOpen ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
          </button>
        </div>
      </nav>

      {/* Mobile menu */}
      {menuOpen && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          className="space-y-3 border-t glass border-border px-4 py-4 md:hidden"
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
          <div className="flex flex-col gap-2 border-t border-border pt-2">
            <a
              href="/login"
              className="rounded-xl border border-border py-2.5 text-center text-sm font-medium"
            >
              ورود به پنل
            </a>
            <a
              href="/register"
              className="rounded-xl bg-brand py-2.5 text-center text-sm font-bold text-brand-foreground"
            >
              شروع کار — رایگانه!
            </a>
          </div>
        </motion.div>
      )}
    </header>
  )
}
