from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ExamQuestion(BaseModel):
    question: str = Field(description="The exam question text")
    options: List[str] = Field(description="Answer choices (exactly 4 options)")
    correct_answer: str = Field(description="The correct option (full text, not just a letter)")
    explanation: str = Field(description="Brief explanation of why this answer is correct")


class AgentResponse(BaseModel):
    response_type: Literal["teaching", "welcome", "exam", "simple"] = Field(
        description=(
            "Choose the response type:\n"
            "• teaching — full lesson with key points\n"
            "• welcome — greeting or response to hello\n"
            "• exam — ONLY when the user explicitly asks to be tested, quizzed, or wants exam questions. "
            "Do NOT use this type for explanations, lessons, or any other request.\n"
            "• simple — short answer to a casual or simple question"
        )
    )
    header: Optional[str] = Field(
        default=None,
        description="Short, engaging title (required for teaching and exam)",
    )
    main_content: str = Field(
        description="Main response body using Bale markdown (*bold*, _italic_, • bullets)"
    )
    key_points: Optional[List[str]] = Field(
        default=None,
        description="Key takeaways (teaching only, 3-5 items)",
    )
    fun_fact: Optional[str] = Field(
        default=None,
        description="Interesting fact (for teaching) or user personality note (for welcome)",
    )
    next_questions: Optional[List[str]] = Field(
        default=None,
        description="3 suggested follow-up questions (for teaching, welcome, simple)",
    )
    exam_questions: Optional[List[ExamQuestion]] = Field(
        default=None,
        description=(
            "Exam questions — populate ONLY when response_type is 'exam' (3-10 multiple-choice questions). "
            "Must be null for all other response types."
        ),
    )


# Backward-compat alias
StudentResponse = AgentResponse
