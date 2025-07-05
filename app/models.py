"""
Pydantic models for request/response validation.
"""
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, HttpUrl

class CurriculumRequest(BaseModel):
    """Request model for curriculum queries."""
    curriculum: str = Field(..., description="Curriculum name (e.g., 'Ontario')")
    subject: str = Field(..., description="Subject name (e.g., 'Mathematics')")
    grade: str = Field(..., description="Grade level (e.g., '5')")
    query: str = Field(..., description="Query string for the curriculum content.")
    top_k: int = Field(5, ge=1, le=10, description="Number of similar documents to retrieve.")

class SourceDocument(BaseModel):
    """Model for source document information."""
    doc_id: str
    score: float
    text: str

class RAGResponse(BaseModel):
    """Response model for RAG queries."""
    success: bool
    response: str
    sources: List[SourceDocument]
    collection_used: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "response": "The curriculum covers...",
                "sources": [
                    {
                        "doc_id": "123",
                        "score": 0.85,
                        "text": "Sample document text..."
                    }
                ],
                "collection_used": "ontario_english"
            }
        }

class LessonPlanRequest(BaseModel):
    """Request model for generating lesson plans."""
    syllabus_data: str = Field(
        ...,
        description="Detailed syllabus content to base the lesson plans on"
    )
    num_classes: int = Field(
        ...,
        gt=0,
        le=50,
        description="Number of classes to generate lesson plans for"
    )
    class_duration: str = Field(
        ...,
        description="Duration of each class (e.g., '45 minutes', '1 hour')"
    )
    teaching_style: Literal[
        "lecture", 
        "interactive", 
        "flipped_classroom", 
        "project_based",
        "blended"
    ] = Field(
        default="interactive",
        description="Preferred teaching style for the lesson plans"
    )
    homework_preference: Literal[
        "none",
        "minimal", 
        "moderate", 
        "extensive"
    ] = Field(
        default="moderate",
        description="Amount of homework to include"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "syllabus_data": "Introduction to basic algebra including variables, expressions, and simple equations...",
                "num_classes": 5,
                "class_duration": "45 minutes",
                "teaching_style": "interactive",
                "homework_preference": "moderate"
            }
        }

class LessonPlanUnit(BaseModel):
    """Model for a single unit in a lesson plan."""
    title: str = Field(..., description="Title of the unit")
    objectives: List[str] = Field(..., description="Learning objectives")
    activities: List[str] = Field(..., description="Classroom activities")
    resources: List[str] = Field(..., description="Required teaching resources")
    homework: Optional[str] = Field(None, description="Homework assignment if any")
    duration: str = Field(..., description="Estimated duration")

class LessonPlanResponse(BaseModel):
    """Response model for lesson plan generation."""
    success: bool
    lesson_plans: List[LessonPlanUnit]
    total_duration: str
    teaching_style: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "teaching_style": "interactive",
                "total_duration": "3 hours 45 minutes",
                "lesson_plans": [
                    {
                        "title": "Introduction to Variables",
                        "objectives": [
                            "Understand what variables are",
                            "Learn to write simple algebraic expressions"
                        ],
                        "activities": [
                            "Warm-up: Real-world examples of variables",
                            "Group activity: Create expressions from word problems"
                        ],
                        "resources": [
                            "Whiteboard and markers",
                            "Printed worksheets"
                        ],
                        "homework": "Complete worksheet on writing expressions",
                        "duration": "45 minutes"
                    }
                ]
            }
        }
