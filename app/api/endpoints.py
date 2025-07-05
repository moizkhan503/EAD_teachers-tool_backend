"""
API endpoints for the curriculum planning service.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Dict, Any

from app.models import (
    CurriculumRequest, 
    RAGResponse, 
    LessonPlanRequest, 
    LessonPlanResponse
)
from app.services.terms_plan import generate_terms_plan
from app.services.lesson_plan_service import generate_lesson_plans as generate_lesson_plans_service

router = APIRouter()

@router.post("/terms_plan", response_model=RAGResponse, summary="Generate terms plan")
async def create_terms_plan(request: CurriculumRequest) -> RAGResponse:
    """
    Generate a terms plan by retrieving and organizing curriculum content.
    
    - **curriculum**: Name of the curriculum (e.g., 'Ontario', 'Common Core')
    - **subject**: Name of the subject (e.g., 'Mathematics', 'Science')
    - **grade**: Grade level (e.g., '5', '10')
    - **query**: The query to search for in the curriculum
    - **top_k**: Number of similar documents to retrieve (1-10, default: 5)
    """
    return await generate_terms_plan(request)

@router.get("/collections", response_model=Dict[str, Any], summary="List collections")
async def list_collections() -> Dict[str, Any]:
    """
    List all available Qdrant collections.
    """
    from app.services.qdrant_service import qdrant_service
    
    try:
        collections = qdrant_service.client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        return {
            "success": True,
            "collections": collection_names,
            "count": len(collection_names)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": str(e)}
        )

@router.post(
    "/lesson_plan", 
    response_model=LessonPlanResponse, 
    status_code=status.HTTP_200_OK,
    summary="Generate lesson plans"
)
async def create_lesson_plan(
    request: LessonPlanRequest,
    background_tasks: BackgroundTasks
) -> LessonPlanResponse:
    """
    Generate detailed lesson plans based on syllabus content and teaching preferences.
    
    - **syllabus_data**: Detailed syllabus content to base the lesson plans on
    - **num_classes**: Number of classes to generate lesson plans for (1-50)
    - **class_duration**: Duration of each class (e.g., "45 minutes", "1 hour")
    - **teaching_style**: Preferred teaching style (lecture, interactive, flipped_classroom, project_based, blended)
    - **homework_preference**: Amount of homework to include (none, minimal, moderate, extensive)
    """
    try:
        return await generate_lesson_plans_service(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": f"Failed to generate lesson plans: {str(e)}"}
        )

@router.get("/health", status_code=status.HTTP_200_OK, summary="Health check")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.
    """
    return {"status": "healthy"}
