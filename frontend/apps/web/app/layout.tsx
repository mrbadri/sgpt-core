import type { Metadata } from "next"
import { Vazirmatn } from "next/font/google"

import "@workspace/ui/globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { cn } from "@workspace/ui/lib/utils"

const vazir = Vazirmatn({
  subsets: ["arabic"],
  variable: "--font-persian",
  weight: ["400", "500", "700", "900"],
  display: "swap",
})

export const metadata: Metadata = {
  title: {
    default: "StudyGPT — هوش مصنوعی آموزشی برای کنکور و دبیرستان",
    template: "%s | StudyGPT",
  },
  description:
    "با StudyGPT سوالات کنکور، ریاضی، فیزیک و شیمی را به‌صورت هوشمند و دقیقاً مطابق کتاب‌های درسی ایران حل کن. هوش مصنوعی تخصصی برای دانش‌آموزان ایرانی.",
  metadataBase: new URL("https://studygpt.ir"),
  openGraph: {
    locale: "fa_IR",
    type: "website",
    siteName: "StudyGPT",
  },
  alternates: {
    canonical: "/",
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html
      lang="fa"
      dir="rtl"
      suppressHydrationWarning
      className={cn("font-sans antialiased", vazir.variable)}
    >
      <body suppressHydrationWarning>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  )
}
