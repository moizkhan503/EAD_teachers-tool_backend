"""
Terms plan generation service.
"""
import logging
from typing import List, Dict, Any

from fastapi import HTTPException, status

from app.models import CurriculumRequest, RAGResponse, SourceDocument
from app.services.qdrant_service import get_best_matching_collection, get_query_engine

logger = logging.getLogger(__name__)

async def generate_terms_plan(request: CurriculumRequest) -> RAGResponse:
    """
    Generate a terms plan by retrieving and organizing curriculum content.
    
    Args:
        request: Curriculum request containing query parameters
        
    Returns:
        RAGResponse: Response containing the processed terms plan
    """
    try:
        logger.info(f"Generating terms plan for request: {request}")
        
        # Get the best matching collection
        collection_name = get_best_matching_collection(
            curriculum=request.curriculum,
            subject=request.subject
        )
        logger.info(f"Using collection: {collection_name}")
        
        # Create query engine
        query_engine = get_query_engine(
            collection_name=collection_name,
            top_k=request.top_k
        )
        
        # Execute query
        response = query_engine.query(request.query)
        
        # Process sources
        sources = []
        if hasattr(response, 'source_nodes'):
            sources = [
                SourceDocument(
                    doc_id=node.node_id,
                    score=node.score,
                    text=node.text[:200] + "..." if node.text else ""
                )
                for node in response.source_nodes
            ]
        
        # Create response
        return RAGResponse(
            success=True,
            response=str(response),
            sources=sources,
            collection_used=collection_name
        )
        
    except HTTPException as he:
        logger.error(f"HTTP error in generate_terms_plan: {str(he)}")
        raise
    except Exception as e:
        logger.error(f"Error in generate_terms_plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": f"Failed to generate terms plan: {str(e)}"}
        )
