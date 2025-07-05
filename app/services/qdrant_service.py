"""
Qdrant service for vector store operations.
"""
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.config import settings
from app.models import SourceDocument

logger = logging.getLogger(__name__)

class QdrantService:
    """Service for handling Qdrant vector store operations."""
    
    def __init__(self):
        """Initialize Qdrant client with settings."""
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY or None,
            timeout=30.0
        )
        logger.info("Qdrant client initialized")
    
    def get_best_matching_collection(self, curriculum: str, subject: str) -> str:
        """
        Find the best matching collection based on curriculum and subject.
        
        Args:
            curriculum: Name of the curriculum (e.g., 'Ontario', 'Common Core')
            subject: Name of the subject (e.g., 'Mathematics', 'Science')
            
        Returns:
            str: Name of the best matching collection
            
        Raises:
            HTTPException: If no collections are found or no good match is found
        """
        try:
            from fastapi import status
            import fnmatch
            
            # Get all collections
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if not collection_names:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No collections found in Qdrant"
                )
            
            # Normalize inputs
            norm_curriculum = curriculum.lower().strip().replace(" ", "_")
            norm_subject = subject.lower().strip().replace(" ", "_")
            
            logger.info(f"Searching for collection with curriculum: {norm_curriculum}, subject: {norm_subject}")
            logger.info(f"Available collections: {collection_names}")
            
            # Try exact match first
            exact_match = f"{norm_curriculum}_{norm_subject}"
            if exact_match in collection_names:
                logger.info(f"Found exact match: {exact_match}")
                return exact_match
                
            # Try different patterns in order of specificity
            patterns_to_try = [
                # Exact match with different case
                lambda: next((name for name in collection_names 
                            if name.lower() == f"{norm_curriculum}_{norm_subject}"), None),
                # Match both curriculum and subject in any order
                lambda: next((name for name in collection_names 
                            if norm_curriculum in name.lower() and norm_subject in name.lower()), None),
                # Match subject with wildcard for curriculum
                lambda: next((name for name in collection_names 
                            if name.lower().endswith(f"_{norm_subject}")), None),
                # Match curriculum with wildcard for subject
                lambda: next((name for name in collection_names 
                            if name.lower().startswith(f"{norm_curriculum}_")), None),
                # Match just the subject
                lambda: next((name for name in collection_names 
                            if norm_subject in name.lower()), None),
                # Match just the curriculum
                lambda: next((name for name in collection_names 
                            if norm_curriculum in name.lower()), None),
                # Try fuzzy matching for subject
                lambda: next((name for name in collection_names 
                            if any(term in name.lower() for term in norm_subject.split('_'))), None)
            ]
            
            # Try each pattern until we find a match
            for pattern_func in patterns_to_try:
                match = pattern_func()
                if match:
                    logger.info(f"Found matching collection: {match}")
                    return match
            
            # If we get here, no good match was found
            error_msg = (
                f"No matching collection found for curriculum '{curriculum}' and subject '{subject}'. "
                f"Available collections: {', '.join(collection_names)}"
            )
            logger.error(error_msg)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "No matching collection found",
                    "available_collections": collection_names,
                    "requested_curriculum": curriculum,
                    "requested_subject": subject
                }
            )
                
        except Exception as e:
            logger.error(f"Error finding matching collection: {str(e)}")
            raise
    
    def get_query_engine(self, collection_name: str, top_k: int = 5):
        """
        Create a query engine for the specified collection.
        
        Args:
            collection_name: Name of the collection to query
            top_k: Number of results to return
            
        Returns:
            RetrieverQueryEngine: Configured query engine
        """
        try:
            from llama_index.core import VectorStoreIndex, Settings
            from llama_index.vector_stores.qdrant import QdrantVectorStore
            from llama_index.core.retrievers import VectorIndexRetriever
            from llama_index.core.response_synthesizers import get_response_synthesizer
            from llama_index.core.query_engine import RetrieverQueryEngine
            
            # Initialize vector store
            vector_store = QdrantVectorStore(
                client=self.client,
                collection_name=collection_name,
            )
            
            # Load index from Qdrant
            index = VectorStoreIndex.from_vector_store(
                vector_store=vector_store,
                embed_model=Settings.embed_model
            )
            
            # Create retriever and query engine
            retriever = VectorIndexRetriever(
                index=index,
                similarity_top_k=top_k,
            )
            
            response_synthesizer = get_response_synthesizer(
                llm=Settings.llm,
                response_mode="compact",
            )
            
            return RetrieverQueryEngine(
                retriever=retriever,
                response_synthesizer=response_synthesizer
            )
            
        except Exception as e:
            logger.error(f"Error creating query engine: {str(e)}")
            raise

# Create a singleton instance
qdrant_service = QdrantService()

# Export commonly used functions
get_best_matching_collection = qdrant_service.get_best_matching_collection
get_query_engine = qdrant_service.get_query_engine
