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
            from difflib import get_close_matches
            
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
            
            # Common typos and variations
            variations = {
                'columbia': 'colambia',
                'maths': 'math',
                'mathematics': 'math',
                'sci': 'science',
                'eng': 'english',
                'lang': 'language',
                'lit': 'literature'
            }
            
            # Generate variations for curriculum and subject
            def get_variations(term):
                terms = {term}
                # Add singular/plural variations
                if term.endswith('s'):
                    terms.add(term[:-1])
                else:
                    terms.add(term + 's')
                # Add common variations
                for k, v in variations.items():
                    if k in term:
                        terms.add(term.replace(k, v))
                    if v in term:
                        terms.add(term.replace(v, k))
                return terms
            
            # Score each collection based on match quality
            def score_collection(collection_name):
                name = collection_name.lower()
                score = 0
                
                # Check for exact matches
                if f"{norm_curriculum}_{norm_subject}" == name:
                    return 100  # Perfect match
                
                # Check for exact matches with variations
                for c in get_variations(norm_curriculum):
                    for s in get_variations(norm_subject):
                        if f"{c}_{s}" == name:
                            return 95  # Variation match
                
                # Check for partial matches
                has_curriculum = any(c in name for c in get_variations(norm_curriculum))
                has_subject = any(s in name for s in get_variations(norm_subject))
                
                if has_curriculum and has_subject:
                    score += 80  # Both parts match
                elif has_curriculum or has_subject:
                    score += 40  # Only one part matches
                
                # Check for close matches using difflib
                curriculum_matches = get_close_matches(norm_curriculum, name.split('_'), n=1, cutoff=0.6)
                subject_matches = get_close_matches(norm_subject, name.split('_'), n=1, cutoff=0.6)
                
                if curriculum_matches and subject_matches:
                    score += 70  # Close match for both
                elif curriculum_matches or subject_matches:
                    score += 35  # Close match for one
                
                return score
            
            # Score all collections
            scored_collections = [
                (name, score_collection(name))
                for name in collection_names
            ]
            
            # Sort by score (highest first)
            scored_collections.sort(key=lambda x: x[1], reverse=True)
            
            logger.info(f"Collection matching scores: {scored_collections}")
            
            # Get the best match if score is above threshold
            if scored_collections and scored_collections[0][1] >= 40:  # Minimum score threshold
                best_match = scored_collections[0][0]
                logger.info(f"Selected collection '{best_match}' with score {scored_collections[0][1]}")
                return best_match
            
            # If no good match found, raise an error
            error_msg = (
                f"No suitable collection found for curriculum '{curriculum}' and subject '{subject}'. "
                f"Available collections: {', '.join(collection_names)}"
            )
            logger.error(error_msg)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "No matching collection found",
                    "available_collections": collection_names,
                    "requested_curriculum": curriculum,
                    "requested_subject": subject,
                    "matching_scores": dict(scored_collections)
                }
            )
                
        except Exception as e:
            logger.error(f"Error finding matching collection: {str(e)}", exc_info=True)
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
