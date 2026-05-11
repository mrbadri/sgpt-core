export type ComparisonRow = {
  subject: string
  generalAI: string
  studyGPT: string
  tag: "math" | "physics" | "chemistry" | "english"
}

export const comparisonData: ComparisonRow[] = [
  {
    subject: "مشتق توابع مثلثاتی",
    generalAI: "روش بین‌المللی — نمایش متفاوت با کتاب ریاضی دوازدهم",
    studyGPT: "دقیقاً مطابق کتاب ریاضی ۳ دوازدهم تجربی و ریاضی",
    tag: "math",
  },
  {
    subject: "قوانین نیوتن و دینامیک",
    generalAI: "علامت‌گذاری SI استاندارد بین‌المللی — گیج‌کننده در کنکور",
    studyGPT: "فرمت و علامت‌گذاری دقیق کتاب فیزیک کنکور سراسری",
    tag: "physics",
  },
  {
    subject: "تعادل شیمیایی و ثابت K",
    generalAI: "پاسخ درست ولی نمایش متفاوت از الگوی سوالات کنکور",
    studyGPT: "فرمت دقیق سوالات کنکور سراسری + نکات آزمونی",
    tag: "chemistry",
  },
  {
    subject: "گرامر زبان انگلیسی",
    generalAI: "توضیح به زبان انگلیسی یا اصطلاحات نامأنوس",
    studyGPT: "توضیح کامل فارسی + نکات کلیدی کنکور زبان",
    tag: "english",
  },
]

export type BillingPeriod = "monthly" | "quarterly"

export type PricingTier = {
  id: "basic" | "pro"
  name: string
  description: string
  price: {
    monthly: number
    quarterly: number
  }
  features: string[]
  cta: string
  highlighted: boolean
  badge?: string
}

export const pricingTiers: PricingTier[] = [
  {
    id: "basic",
    name: "پلن عادی",
    description: "برای آشنایی با StudyGPT",
    price: { monthly: 0, quarterly: 0 },
    features: [
      "۱۰ سوال در روز",
      "پشتیبانی ریاضی و فیزیک",
      "توضیحات گام‌به‌گام",
      "دسترسی به وبلاگ آموزشی",
    ],
    cta: "شروع رایگان",
    highlighted: false,
  },
  {
    id: "pro",
    name: "پلن پرو",
    description: "برای آمادگی جدی کنکور",
    price: { monthly: 149000, quarterly: 109000 },
    features: [
      "سوالات نامحدود",
      "تمام دروس کنکور سراسری",
      "تحلیل نقاط ضعف و قوت",
      "آزمون مجازی هوشمند",
      "پشتیبانی اولویت‌دار",
      "دسترسی به آرشیو سوالات",
    ],
    cta: "تهیه پلن پرو",
    highlighted: true,
    badge: "پرفروش‌ترین",
  },
]

export type NavItem = {
  label: string
  href: string
}

export const navItems: NavItem[] = [
  { label: "ویژگی‌ها", href: "#features" },
  { label: "قیمت‌گذاری", href: "#pricing" },
  { label: "وبلاگ", href: "/blog" },
]

export const footerLinks = {
  quickLinks: [
    { label: "خانه", href: "/" },
    { label: "ویژگی‌ها", href: "#features" },
    { label: "قیمت‌گذاری", href: "#pricing" },
    { label: "وبلاگ", href: "/blog" },
    { label: "درباره ما", href: "/about" },
    { label: "تماس با ما", href: "/contact" },
  ],
  legal: [
    { label: "قوانین استفاده", href: "/terms" },
    { label: "حریم خصوصی", href: "/privacy" },
    { label: "سیاست استرداد وجه", href: "/refund" },
  ],
}

export function formatToman(amount: number): string {
  if (amount === 0) return "رایگان"
  return new Intl.NumberFormat("fa-IR").format(amount) + " تومان"
}
