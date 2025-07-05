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
            curriculum: Name of the curriculum
            subject: Name of the subject
            
        Returns:
            str: Name of the best matching collection
            
        Raises:
            HTTPException: If no collections are found
        """
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if not collection_names:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No collections found in Qdrant"
                )
            
            norm_curriculum = curriculum.lower().replace(" ", "_")
            norm_subject = subject.lower().replace(" ", "_")
            
            search_patterns = [
                f"{norm_curriculum}_{norm_subject}",
                f"%_{norm_subject}",
                f"{norm_curriculum}_%",
                norm_subject,
                f"%{norm_subject}%"
            ]
            
            for pattern in search_patterns:
                if pattern in collection_names:
                    return pattern
                
                if "%" in pattern:
                    import fnmatch
                    matches = [name for name in collection_names 
                             if fnmatch.fnmatch(name, pattern)]
                    if matches:
                        for match in matches:
                            if norm_curriculum in match and norm_subject in match:
                                return match
                        return matches[0]
            
            for name in collection_names:
                if norm_curriculum in name:
                    return name
            
            if collection_names:
                return collection_names[0]
                
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
