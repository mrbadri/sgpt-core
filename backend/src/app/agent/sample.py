from pydantic import BaseModel, Field
from typing import List

class StudentResponse(BaseModel):
    header: str = Field(description="یه عنوان جذاب و کوتاه برای موضوع")
    main_content: str = Field(description="متن اصلی درس با فرمت HTML (فقط تگ b و i)")
    key_points: List[str] = Field(description="لیستی از نکات مهم و کنکوری")
    fun_fact: str = Field(description="یک نکته جالب یا کاربردی برای رفع خستگی")
    next_questions: List[str] = Field(description="۳ سوال کوتاه برای ادامه گفتگو")