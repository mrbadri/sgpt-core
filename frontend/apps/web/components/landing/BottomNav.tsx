"use client"

import { usePathname } from "next/navigation"
import { motion } from "framer-motion"
import { BookOpen, CreditCard, Newspaper } from "lucide-react"

const navItems = [
  { href: "#hero", icon: BookOpen, label: "مطالعه" },
  { href: "#pricing", icon: CreditCard, label: "اشتراک" },
  { href: "/blog", icon: Newspaper, label: "وبلاگ" },
]

export default function BottomNav() {
  const pathname = usePathname()

  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-40 border-t glass border-border md:hidden"
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
    >
      <div className="flex h-16 items-stretch justify-around">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive =
            pathname === item.href ||
            (item.href !== "/" && pathname.startsWith(item.href))
          return (
            <motion.a
              key={item.href}
              href={item.href}
              whileTap={{ scale: 0.82 }}
              style={{ touchAction: "manipulation" }}
              className={`flex flex-1 flex-col items-center justify-center gap-1 text-xs font-medium transition-colors ${
                isActive ? "text-brand" : "text-muted-foreground"
              }`}
            >
              <Icon className="h-5 w-5" />
              <span>{item.label}</span>
            </motion.a>
          )
        })}
      </div>
    </nav>
  )
}
