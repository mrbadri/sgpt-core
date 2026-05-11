import { footerLinks } from "@/lib/landing-data"

export default function Footer() {
  return (
    <footer className="border-t border-border bg-muted/20">
      <div className="max-w-6xl mx-auto px-4 py-14">
        {/* Brand intro */}
        <div className="mb-10">
          <div className="flex items-center gap-1 font-black text-2xl mb-3">
            <span className="text-foreground">Study</span>
            <span className="text-brand">GPT</span>
          </div>
          <p className="text-sm text-muted-foreground max-w-sm leading-relaxed">
            هوش مصنوعی تخصصی برای دانش‌آموزان ایرانی — پاسخ‌های دقیق مطابق کتب درسی، آماده برای کنکور.
          </p>
        </div>

        {/* 3-column grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-10">

          {/* Column 1 — Trust Certificates */}
          <div>
            <h3 className="font-bold text-sm mb-4 text-foreground">نمادهای اعتماد</h3>
            <div className="flex gap-3 mb-5">
              {/* Enamad placeholder */}
              <div
                className="w-20 h-20 rounded-xl border-2 border-dashed border-border flex flex-col items-center justify-center gap-1 text-center cursor-pointer hover:border-brand/50 transition-colors"
                title="نماد اعتماد الکترونیکی"
              >
                <span className="text-xl">🏅</span>
                <span className="text-[10px] text-muted-foreground font-medium">اینماد</span>
              </div>
              {/* Samandehi placeholder */}
              <div
                className="w-20 h-20 rounded-xl border-2 border-dashed border-border flex flex-col items-center justify-center gap-1 text-center cursor-pointer hover:border-brand/50 transition-colors"
                title="سامانه ساماندهی"
              >
                <span className="text-xl">📋</span>
                <span className="text-[10px] text-muted-foreground font-medium">ساماندهی</span>
              </div>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              StudyGPT پلتفرم آموزشی دارای مجوز فعالیت از مراجع ذی‌صلاح
            </p>

            {/* Contact info */}
            <div className="mt-5 space-y-1.5 text-xs text-muted-foreground">
              <p>📍 تهران، خیابان ولیعصر — [آدرس دفتر]</p>
              <p>📞 <a href="tel:02100000000" className="hover:text-foreground transition-colors">۰۲۱-۰۰۰-۰۰۰۰</a></p>
              <p>📧 <a href="mailto:support@studygpt.ir" className="hover:text-foreground transition-colors">support@studygpt.ir</a></p>
            </div>
          </div>

          {/* Column 2 — Quick Links */}
          <div>
            <h3 className="font-bold text-sm mb-4 text-foreground">دسترسی سریع</h3>
            <ul className="space-y-2.5">
              {footerLinks.quickLinks.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Column 3 — Legal */}
          <div>
            <h3 className="font-bold text-sm mb-4 text-foreground">قوانین و مقررات</h3>
            <ul className="space-y-2.5 mb-6">
              {footerLinks.legal.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
            <div className="p-3 rounded-xl bg-muted/50 border border-border text-xs text-muted-foreground leading-relaxed">
              <strong className="text-foreground block mb-1">سیاست استرداد</strong>
              در صورت عدم رضایت، تا ۷ روز پس از خرید امکان استرداد وجه وجود دارد.
              برای درخواست، با پشتیبانی تماس بگیرید.
            </div>
          </div>
        </div>
      </div>

      {/* Copyright bar */}
      <div className="border-t border-border py-5 px-4">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-muted-foreground">
          <span>© ۱۴۰۴ StudyGPT — تمامی حقوق محفوظ است.</span>
          <span>ساخته شده با ❤️ برای دانش‌آموزان ایران</span>
        </div>
      </div>
    </footer>
  )
}
