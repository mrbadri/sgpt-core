from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ExamQuestion(BaseModel):
    question: str = Field(description="متن سوال")
    options: List[str] = Field(description="گزینه‌ها (حداقل ۴ گزینه)")
    correct_answer: str = Field(description="گزینه صحیح (متن کامل، نه فقط حرف)")
    explanation: str = Field(description="توضیح کوتاه چرا این گزینه درست است")


class AgentResponse(BaseModel):
    response_type: Literal["teaching", "welcome", "exam", "simple"] = Field(
        description=(
            "نوع پاسخ را انتخاب کن:\n"
            "• teaching — توضیح درسی کامل با نکات کلیدی\n"
            "• welcome — خوش‌آمدگویی یا پاسخ به سلام\n"
            "• exam — ساخت آزمون چندگزینه‌ای\n"
            "• simple — پاسخ کوتاه به سوال ساده یا گفتگوی معمولی"
        )
    )
    header: Optional[str] = Field(
        default=None,
        description="عنوان کوتاه و جذاب (برای teaching و exam لازم است)",
    )
    main_content: str = Field(
        description="متن اصلی پاسخ با فرمت Bale markdown (*bold*, _italic_, • bullets)"
    )
    key_points: Optional[List[str]] = Field(
        default=None,
        description="نکات کلیدی (فقط برای teaching، ۳-۵ مورد)",
    )
    fun_fact: Optional[str] = Field(
        default=None,
        description="نکته جالب (برای teaching) یا تحلیل شخصیت کاربر (برای welcome)",
    )
    next_questions: Optional[List[str]] = Field(
        default=None,
        description="۳ سوال پیشنهادی برای ادامه گفتگو (برای teaching، welcome، simple)",
    )
    exam_questions: Optional[List[ExamQuestion]] = Field(
        default=None,
        description="سوالات آزمون (فقط برای exam، ۳-۱۰ سوال چندگزینه‌ای)",
    )


# Backward-compat alias
StudentResponse = AgentResponse
