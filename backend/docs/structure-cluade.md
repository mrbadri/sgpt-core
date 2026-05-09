backend/
├── .cursor/                        # قوانین Cursor برای این پروژه
├── .vscode/                        # تنظیمات VS Code/Cursor
├── .langgraph_api/                 # کش LangGraph CLI (محلی، در git نیست)
│
├── docs/                           # مستندات فنی
│   ├── architecture.md             # دیاگرام و توضیح کلی سیستم
│   ├── api.md                      # مستندات endpoint ها
│   └── deployment.md              # راهنمای deploy
│
├── examples/                       # مثال‌های کوچک برای agent/گراف
├── notebooks/                      # Jupyter برای آزمایش
│
├── scripts/                        # اسکریپت‌های کمکی (یک‌بار اجرا یا ابزار تیم)
│   ├── seed_db.py                  # داده اولیه برای محیط توسعه
│   ├── create_admin.py             # ساخت کاربر ادمین
│   └── demo_agent.py              # تست سریع agent در CLI
│
├── tests/
│   ├── conftest.py                 # fixture های مشترک pytest
│   ├── unit/                       # تست واحد — بدون I/O واقعی، mock همه چیز
│   │   └── app/                   # آینه ساختار src/app/
│   │       ├── agent/
│   │       ├── services/
│   │       └── api/
│   ├── integration/                # تست با دیتابیس/سرویس واقعی (test DB)
│   ├── e2e/                        # تست کامل از webhook تا پاسخ
│   └── factories/                  # factory_boy برای ساخت آبجکت تست
│
├── src/
│   │
│   ├── app/                        # هسته FastAPI
│   │   ├── main.py                 # نقطه ورود — ساخت app، mount روترها، middleware
│   │   ├── settings.py             # BaseSettings با dotenv (.env)
│   │   ├── dependencies.py         # FastAPI Depends مشترک (auth, db session)
│   │   │
│   │   ├── api/                    # لایه HTTP — فقط روتر، بدون منطق تجاری
│   │   │   └── v1/                # نسخه‌بندی از همین اول
│   │   │       ├── __init__.py
│   │   │       ├── router.py       # جمع‌آوری همه روترهای v1
│   │   │       ├── chat.py         # POST /chat — برای وب‌اپ
│   │   │       ├── webhook.py      # POST /webhook/bale — برای ربات بله
│   │   │       └── health.py      # GET /health — برای مانیتورینگ
│   │   │
│   │   ├── services/               # منطق تجاری — پل بین API/Bot و Agent
│   │   │   ├── chat_service.py     # مدیریت مکالمه، صدا زدن agent
│   │   │   ├── session_service.py  # ساخت و مدیریت session کاربر
│   │   │   └── user_service.py    # منطق مربوط به کاربر
│   │   │
│   │   ├── agent/                  # Agent LangGraph — منطق هوش مصنوعی
│   │   │   ├── graph.py            # تعریف StateGraph اصلی
│   │   │   ├── state.py            # TypedDict استیت agent
│   │   │   ├── nodes/              # هر نود جداگانه
│   │   │   │   ├── retriever.py
│   │   │   │   ├── llm.py
│   │   │   │   └── tool_call.py
│   │   │   ├── tools/              # ابزارهای agent
│   │   │   │   ├── web_search.py
│   │   │   │   └── graphiti_query.py
│   │   │   └── prompts/           # تمپلیت‌های prompt — جدا از کد
│   │   │       ├── system.txt
│   │   │       └── few_shot.txt
│   │   │
│   │   ├── db/                     # دیتابیس — Session و Migration
│   │   │   ├── session.py          # AsyncSession factory، get_session
│   │   │   ├── base.py             # SQLModel base class
│   │   │   └── migrations/        # فایل‌های Alembic
│   │   │       ├── env.py
│   │   │       └── versions/
│   │   │
│   │   ├── models/                 # مدل‌های دیتابیس و Schema های API
│   │   │   ├── user.py             # User table
│   │   │   ├── session.py          # ChatSession table
│   │   │   ├── message.py          # Message table
│   │   │   └── schemas/           # Pydantic request/response — جدا از table
│   │   │       ├── chat.py
│   │   │       └── user.py
│   │   │
│   │   ├── knowledge_graph/        # Graphiti / FalkorDB
│   │   │   ├── client.py           # اتصال به FalkorDB/Graphiti
│   │   │   ├── queries.py          # query های آماده
│   │   │   └── ingestion.py       # اضافه کردن داده به گراف
│   │   │
│   │   ├── errors/                 # هندلر خطا
│   │   │   ├── handlers.py         # exception_handler های register شده در app
│   │   │   └── exceptions.py      # Custom exception class ها
│   │   │
│   │   └── observability/         # لاگ، تله‌متری، مانیتورینگ
│   │       ├── logging.py          # تنظیم structlog/loguru
│   │       ├── tracing.py          # OpenTelemetry setup
│   │       └── langfuse.py        # تریس LLM calls
│   │
│   ├── integrations/               # اتصال به سرویس‌های بیرونی
│   │   └── bale/                  # ربات بله
│   │       ├── client.py           # BaleBot client، send_message
│   │       ├── handler.py          # پردازش update های دریافتی
│   │       ├── keyboards.py        # inline keyboard های آماده
│   │       └── models.py          # Pydantic model های webhook بله
│   │
│   └── common/                    # کد مشترک بین همه ماژول‌ها
│       ├── utils.py                # توابع کمکی خالص (بدون side effect)
│       ├── constants.py            # ثابت‌های پروژه
│       └── types.py               # Type alias های مشترک
│
├── pyproject.toml                  # وابستگی‌ها، اسکریپت‌ها، تنظیمات ابزار
├── uv.lock                         # قفل نسخه‌ها
├── langgraph.json                  # پیکربندی LangGraph dev server
├── pyrightconfig.json              # تایپ‌چک Pyright
├── .env                            # متغیرهای محیط (در git نیست)
└── .env.example                   # نمونه env برای تیم (در git هست)