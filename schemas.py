from pydantic import BaseModel, Field, model_validator, field_validator
from typing import Optional
from enum import Enum


class PRDType(str, Enum):
    FEATURE     = "Feature"
    BUG_FIX     = "Bug Fix"
    SPIKE       = "Spike"
    TECH_DEBT   = "Tech Debt"
    ENHANCEMENT = "Enhancement"


class PRDStatus(str, Enum):
    DRAFT    = "Draft"
    IN_REVIEW = "In Review"
    APPROVED = "Approved"


class Priority(str, Enum):
    MUST_HAVE   = "Must Have"
    SHOULD_HAVE = "Should Have"
    NICE_TO_HAVE = "Nice to Have"


class Stakeholder(BaseModel):
    name:  str = Field(..., description="Stakeholder name or role")
    role:  str = Field(..., description="e.g. Product Owner, Dev Lead, QA")
    email: Optional[str] = None


class Goal(BaseModel):
    goal:     str = Field(..., description="What we want to achieve")
    metric:   str = Field(..., description="How we measure it")
    baseline: str = Field(..., description="Current state before this feature (e.g. '30 tickets/week')")
    target:   str = Field(..., description="The quantified success bar (e.g. '< 5/week')")


class Persona(BaseModel):
    name:        str
    description: str
    key_need:    str


class FunctionalRequirement(BaseModel):
    id:          str   = Field(..., description="e.g. FR-01")
    requirement: str
    priority:    Priority


class AcceptanceCriterion(BaseModel):
    criterion: str
    met:       bool = False


_FIBONACCI = {1, 2, 3, 5, 8, 13}


class UserStory(BaseModel):
    id:                  str
    title:               str
    as_a:                str  = Field(..., description="The persona")
    i_want_to:           str  = Field(..., description="The action they want to take")
    so_that:             str  = Field(..., description="The benefit they get")
    acceptance_criteria: list[AcceptanceCriterion]
    priority:            Priority
    story_points:        int  = Field(..., ge=1, le=13)
    labels:              list[str] = []

    @model_validator(mode="after")
    def validate_fibonacci(self) -> "UserStory":
        if self.story_points not in _FIBONACCI:
            raise ValueError(
                f"story_points must be a Fibonacci number (1, 2, 3, 5, 8, 13). "
                f"Got: {self.story_points}"
            )
        return self


class EdgeCase(BaseModel):
    scenario:            str
    expected_behaviour:  str


class NFRCategory(str, Enum):
    PERFORMANCE   = "Performance"
    SECURITY      = "Security"
    SCALABILITY   = "Scalability"
    ACCESSIBILITY = "Accessibility"
    RELIABILITY   = "Reliability"


class NonFunctionalRequirement(BaseModel):
    id:          str          = Field(..., description="e.g. NFR-01")
    category:    NFRCategory
    requirement: str          = Field(..., description="What must be true")
    target:      str          = Field(..., description="Measurable bar, e.g. 'p95 < 500ms'")


class Risk(BaseModel):
    risk:       str = Field(..., description="What could go wrong at the project/technical level")
    impact:     str = Field(..., description="High / Medium / Low — what happens if it materialises")
    mitigation: str = Field(..., description="What we do to prevent or reduce the impact")


class PRDDocument(BaseModel):
    title:                       str
    version:                     str   = "1.0"
    date:                        str
    status:                      PRDStatus = PRDStatus.DRAFT
    prd_type:                    PRDType
    author:                      str   = "AI Requirement Agent"
    stakeholders:                list[Stakeholder]
    problem_statement:           str
    business_value:              str   = Field(..., description="Revenue / cost / risk impact")
    goals:                       list[Goal]
    in_scope:                    list[str]
    out_of_scope:                list[str]
    personas:                    list[Persona]
    functional_requirements:     list[FunctionalRequirement]
    non_functional_requirements: list[NonFunctionalRequirement] = Field(default_factory=list)
    user_stories:                list[UserStory]
    edge_cases:                  list[EdgeCase]
    risks:                       list[Risk]                     = Field(default_factory=list)
    technical_constraints:       list[str]
    dependencies:                list[str]
    open_questions:              list[str]
    assumptions:                 list[str]

    @field_validator("functional_requirements")
    @classmethod
    def min_functional_requirements(cls, v):
        if len(v) < 3:
            raise ValueError("PRD must have at least 3 functional requirements")
        return v

    @field_validator("user_stories")
    @classmethod
    def min_user_stories(cls, v):
        if len(v) < 3:
            raise ValueError("PRD must have at least 3 user stories")
        return v

    @field_validator("edge_cases")
    @classmethod
    def min_edge_cases(cls, v):
        if len(v) < 2:
            raise ValueError("PRD must have at least 2 edge cases")
        return v
