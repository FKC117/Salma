"""
RAG Service for Redis Vector Database Operations

This service handles vector storage, retrieval, and semantic search using Redis
as the vector database with 'analytical:rag:' key prefix.
"""

import json
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
import redis
from redis.exceptions import RedisError

from analytical.analytics.models import VectorNote, User, Dataset
from django.db import models
from django.db.models import F
from analytics.services.audit_trail_manager import AuditTrailManager

logger = logging.getLogger(__name__)


class RAGService:
    """
    Service for Redis-based vector database operations for RAG system
    """
    
    def __init__(self):
        self.audit_manager = AuditTrailManager()
        self.redis_client = self._get_redis_client()
        self.key_prefix = 'analytical:rag:'
        self.vector_prefix = f"{self.key_prefix}vector:"
        self.index_prefix = f"{self.key_prefix}index:"
        
        # Vector search configuration
        self.default_top_k = 5
        self.similarity_threshold = 0.7
        self.max_vector_dimension = 384  # all-MiniLM-L6-v2 dimension
    
    def _get_redis_client(self) -> redis.Redis:
        """Get Redis client connection"""
        try:
            # Use the same Redis connection as Django cache
            redis_url = getattr(settings, 'CACHES', {}).get('default', {}).get('LOCATION', 'redis://127.0.0.1:6379/1')
            if redis_url.startswith('redis://'):
                return redis.from_url(redis_url, decode_responses=False)
            else:
                # Fallback to default Redis connection
                return redis.Redis(host='127.0.0.1', port=6379, db=1, decode_responses=False)
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise ValueError(f"Redis connection failed: {str(e)}")
    
    def store_vector(self, vector_note: VectorNote, embedding: List[float]) -> bool:
        """
        Store vector embedding in Redis
        
        Args:
            vector_note: VectorNote model instance
            embedding: Vector embedding as list of floats
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate embedding
            if not self._validate_embedding(embedding):
                logger.error(f"Invalid embedding for VectorNote {vector_note.id}")
                return False
            
            # Create Redis key
            redis_key = vector_note.get_redis_key()
            
            # Prepare data for storage
            vector_data = {
                'id': vector_note.id,
                'title': vector_note.title,
                'text': vector_note.text,
                'scope': vector_note.scope,
                'dataset_id': vector_note.dataset_id,
                'user_id': vector_note.user_id,
                'content_type': vector_note.content_type,
                'embedding': embedding,
                'metadata': vector_note.metadata_json,
                'confidence_score': vector_note.confidence_score,
                'created_at': vector_note.created_at.isoformat(),
            }
            
            # Store in Redis
            self.redis_client.hset(redis_key, mapping={
                'data': json.dumps(vector_data),
                'embedding': json.dumps(embedding),
                'dimension': str(len(embedding))
            })
            
            # Set expiration (optional - 30 days)
            self.redis_client.expire(redis_key, 30 * 24 * 60 * 60)
            
            # Add to scope index
            self._add_to_scope_index(vector_note)
            
            logger.info(f"Stored vector for VectorNote {vector_note.id} in Redis")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store vector for VectorNote {vector_note.id}: {str(e)}")
            return False
    
    def search_vectors(self, query_embedding: List[float], scope: str, 
                      dataset_id: Optional[int] = None, user_id: Optional[int] = None,
                      top_k: int = None, similarity_threshold: float = None) -> List[Dict[str, Any]]:
        """
        Search for similar vectors using cosine similarity
        
        Args:
            query_embedding: Query vector embedding
            scope: Search scope ('dataset' or 'global')
            dataset_id: Dataset ID for dataset-scoped search
            user_id: User ID for multi-tenancy
            top_k: Number of top results to return
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            List of similar vector results with metadata
        """
        try:
            top_k = top_k or self.default_top_k
            similarity_threshold = similarity_threshold or self.similarity_threshold
            
            # Validate query embedding
            if not self._validate_embedding(query_embedding):
                logger.error("Invalid query embedding")
                return []
            
            # Get candidate vectors based on scope
            candidate_keys = self._get_candidate_keys(scope, dataset_id, user_id)
            
            if not candidate_keys:
                logger.info(f"No candidate vectors found for scope={scope}, dataset_id={dataset_id}")
                return []
            
            # Calculate similarities
            similarities = []
            for key in candidate_keys:
                try:
                    # Get vector data from Redis
                    vector_data = self.redis_client.hget(key, 'data')
                    embedding_data = self.redis_client.hget(key, 'embedding')
                    
                    if not vector_data or not embedding_data:
                        continue
                    
                    # Parse data
                    data = json.loads(vector_data)
                    candidate_embedding = json.loads(embedding_data)
                    
                    # Calculate cosine similarity
                    similarity = self._cosine_similarity(query_embedding, candidate_embedding)
                    
                    if similarity >= similarity_threshold:
                        similarities.append({
                            'similarity': similarity,
                            'data': data,
                            'redis_key': key
                        })
                        
                except Exception as e:
                    logger.warning(f"Error processing vector {key}: {str(e)}")
                    continue
            
            # Sort by similarity and return top-k
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            results = similarities[:top_k]
            
            # Update usage counts
            self._update_usage_counts([r['data']['id'] for r in results])
            
            logger.info(f"Found {len(results)} similar vectors for query")
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {str(e)}")
            return []
    
    def delete_vector(self, vector_note_id: int) -> bool:
        """
        Delete vector from Redis
        
        Args:
            vector_note_id: ID of VectorNote to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get VectorNote from database
            try:
                vector_note = VectorNote.objects.get(id=vector_note_id)
            except VectorNote.DoesNotExist:
                logger.warning(f"VectorNote {vector_note_id} not found in database")
                return False
            
            # Delete from Redis
            redis_key = vector_note.get_redis_key()
            self.redis_client.delete(redis_key)
            
            # Remove from scope index
            self._remove_from_scope_index(vector_note)
            
            logger.info(f"Deleted vector for VectorNote {vector_note_id} from Redis")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete vector {vector_note_id}: {str(e)}")
            return False
    
    def clear_scope(self, scope: str, dataset_id: Optional[int] = None, 
                   user_id: Optional[int] = None) -> int:
        """
        Clear all vectors for a specific scope
        
        Args:
            scope: Scope to clear ('dataset' or 'global')
            dataset_id: Dataset ID for dataset-scoped clearing
            user_id: User ID for multi-tenancy
            
        Returns:
            int: Number of vectors cleared
        """
        try:
            # Get keys to delete
            candidate_keys = self._get_candidate_keys(scope, dataset_id, user_id)
            
            if not candidate_keys:
                return 0
            
            # Delete keys
            deleted_count = 0
            for key in candidate_keys:
                if self.redis_client.delete(key):
                    deleted_count += 1
            
            # Clear scope index
            self._clear_scope_index(scope, dataset_id, user_id)
            
            logger.info(f"Cleared {deleted_count} vectors for scope={scope}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to clear scope {scope}: {str(e)}")
            return 0
    
    def get_vector_stats(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get statistics about stored vectors
        
        Args:
            user_id: User ID for user-specific stats (optional)
            
        Returns:
            Dict with vector statistics
        """
        try:
            stats = {
                'total_vectors': 0,
                'dataset_vectors': 0,
                'global_vectors': 0,
                'by_content_type': {},
                'by_user': {},
                'memory_usage': 0
            }
            
            # Get all vector keys
            pattern = f"{self.vector_prefix}*"
            all_keys = self.redis_client.keys(pattern)
            
            for key in all_keys:
                try:
                    vector_data = self.redis_client.hget(key, 'data')
                    if not vector_data:
                        continue
                    
                    data = json.loads(vector_data)
                    
                    # Filter by user if specified
                    if user_id and data.get('user_id') != user_id:
                        continue
                    
                    stats['total_vectors'] += 1
                    
                    # Count by scope
                    if data.get('scope') == 'dataset':
                        stats['dataset_vectors'] += 1
                    elif data.get('scope') == 'global':
                        stats['global_vectors'] += 1
                    
                    # Count by content type
                    content_type = data.get('content_type', 'unknown')
                    stats['by_content_type'][content_type] = stats['by_content_type'].get(content_type, 0) + 1
                    
                    # Count by user
                    user_id_key = data.get('user_id', 'unknown')
                    stats['by_user'][user_id_key] = stats['by_user'].get(user_id_key, 0) + 1
                    
                except Exception as e:
                    logger.warning(f"Error processing vector {key}: {str(e)}")
                    continue
            
            # Calculate memory usage (approximate)
            stats['memory_usage'] = len(all_keys) * 1024  # Rough estimate
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get vector stats: {str(e)}")
            return {}
    
    def _validate_embedding(self, embedding: List[float]) -> bool:
        """Validate embedding vector"""
        if not isinstance(embedding, list):
            return False
        if len(embedding) == 0:
            return False
        if len(embedding) > self.max_vector_dimension:
            return False
        if not all(isinstance(x, (int, float)) for x in embedding):
            return False
        return True
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            # Convert to numpy arrays
            a = np.array(vec1, dtype=np.float32)
            b = np.array(vec2, dtype=np.float32)
            
            # Calculate cosine similarity
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            return float(dot_product / (norm_a * norm_b))
            
        except Exception as e:
            logger.warning(f"Error calculating cosine similarity: {str(e)}")
            return 0.0
    
    def _get_candidate_keys(self, scope: str, dataset_id: Optional[int] = None, 
                           user_id: Optional[int] = None) -> List[str]:
        """Get candidate vector keys based on scope and filters"""
        try:
            # Get scope index key
            if scope == 'dataset' and dataset_id:
                index_key = f"{self.index_prefix}dataset:{dataset_id}"
            elif scope == 'global':
                index_key = f"{self.index_prefix}global"
            else:
                return []
            
            # Get keys from index
            keys = self.redis_client.smembers(index_key)
            candidate_keys = []
            
            for key in keys:
                try:
                    # Get vector data to check user_id filter
                    if user_id:
                        vector_data = self.redis_client.hget(key, 'data')
                        if vector_data:
                            data = json.loads(vector_data)
                            if data.get('user_id') == user_id:
                                candidate_keys.append(key)
                    else:
                        candidate_keys.append(key)
                        
                except Exception as e:
                    logger.warning(f"Error processing candidate key {key}: {str(e)}")
                    continue
            
            return candidate_keys
            
        except Exception as e:
            logger.error(f"Failed to get candidate keys: {str(e)}")
            return []
    
    def _add_to_scope_index(self, vector_note: VectorNote) -> None:
        """Add vector to scope index"""
        try:
            redis_key = vector_note.get_redis_key()
            
            if vector_note.scope == 'dataset' and vector_note.dataset_id:
                index_key = f"{self.index_prefix}dataset:{vector_note.dataset_id}"
            elif vector_note.scope == 'global':
                index_key = f"{self.index_prefix}global"
            else:
                return
            
            # Add to index
            self.redis_client.sadd(index_key, redis_key)
            
        except Exception as e:
            logger.warning(f"Failed to add to scope index: {str(e)}")
    
    def _remove_from_scope_index(self, vector_note: VectorNote) -> None:
        """Remove vector from scope index"""
        try:
            redis_key = vector_note.get_redis_key()
            
            if vector_note.scope == 'dataset' and vector_note.dataset_id:
                index_key = f"{self.index_prefix}dataset:{vector_note.dataset_id}"
            elif vector_note.scope == 'global':
                index_key = f"{self.index_prefix}global"
            else:
                return
            
            # Remove from index
            self.redis_client.srem(index_key, redis_key)
            
        except Exception as e:
            logger.warning(f"Failed to remove from scope index: {str(e)}")
    
    def _clear_scope_index(self, scope: str, dataset_id: Optional[int] = None, 
                          user_id: Optional[int] = None) -> None:
        """Clear scope index"""
        try:
            if scope == 'dataset' and dataset_id:
                index_key = f"{self.index_prefix}dataset:{dataset_id}"
            elif scope == 'global':
                index_key = f"{self.index_prefix}global"
            else:
                return
            
            self.redis_client.delete(index_key)
            
        except Exception as e:
            logger.warning(f"Failed to clear scope index: {str(e)}")
    
    def _update_usage_counts(self, vector_note_ids: List[int]) -> None:
        """Update usage counts for retrieved vectors"""
        try:
            with transaction.atomic():
                VectorNote.objects.filter(id__in=vector_note_ids).update(
                    usage_count=F('usage_count') + 1,
                    last_accessed=timezone.now()
                )
        except Exception as e:
            logger.warning(f"Failed to update usage counts: {str(e)}")
