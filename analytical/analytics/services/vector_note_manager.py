"""
Vector Note Manager for Embedding Generation and Content Management

This service handles content preprocessing, embedding generation using sentence-transformers,
and PII masking for the RAG system.
"""

import re
import logging
import hashlib
import json
from typing import Dict, List, Any, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from sentence_transformers import SentenceTransformer
import numpy as np

from analytics.models import VectorNote, User, Dataset, AnalysisResult
from analytics.services.rag_service import RAGService
from analytics.services.audit_trail_manager import AuditTrailManager

logger = logging.getLogger(__name__)


class VectorNoteManager:
    """
    Service for managing vector note creation, embedding generation, and content processing
    """
    
    def __init__(self):
        self.audit_manager = AuditTrailManager()
        self.rag_service = RAGService()
        self.embedding_model = self._load_embedding_model()
        self.embedding_dimension = 384  # all-MiniLM-L6-v2 dimension
        
        # PII patterns for masking
        self.pii_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
            'ssn': r'\b\d{3}-?\d{2}-?\d{4}\b',
            'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            'ip_address': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        }
    
    def _load_embedding_model(self) -> SentenceTransformer:
        """Load the sentence-transformers model"""
        try:
            model_name = getattr(settings, 'RAG_EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
            model = SentenceTransformer(model_name)
            logger.info(f"Loaded embedding model: {model_name}")
            return model
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            raise ValueError(f"Failed to load embedding model: {str(e)}")
    
    def create_vector_note(self, title: str, text: str, scope: str, 
                          content_type: str, user: User, dataset: Optional[Dataset] = None,
                          metadata: Optional[Dict[str, Any]] = None,
                          confidence_score: float = 1.0) -> Optional[VectorNote]:
        """
        Create a new vector note with embedding generation
        
        Args:
            title: Title of the content
            text: Main content text
            scope: 'dataset' or 'global'
            content_type: Type of content
            user: User creating the note
            dataset: Dataset for dataset-scoped notes
            metadata: Additional metadata
            confidence_score: Confidence score for the content
            
        Returns:
            VectorNote instance or None if failed
        """
        try:
            # Validate inputs
            if not self._validate_inputs(title, text, scope, content_type, user, dataset):
                return None
            
            # Preprocess content
            processed_text = self._preprocess_content(text)
            
            # Generate embedding
            embedding = self._generate_embedding(processed_text)
            if not embedding:
                logger.error("Failed to generate embedding")
                return None
            
            # Create VectorNote
            vector_note = VectorNote.objects.create(
                title=title,
                text=processed_text,
                scope=scope,
                dataset=dataset,
                user=user,
                content_type=content_type,
                embedding=embedding,
                embedding_model=self.embedding_model.get_sentence_embedding_dimension(),
                embedding_dimension=len(embedding),
                metadata_json=metadata or {},
                confidence_score=confidence_score,
                is_pii_masked=self._has_pii_masking(text, processed_text),
                sanitized=True
            )
            
            # Store in Redis
            if not self.rag_service.store_vector(vector_note, embedding):
                logger.error(f"Failed to store vector in Redis for VectorNote {vector_note.id}")
                vector_note.delete()
                return None
            
            # Log audit trail
            self.audit_manager.log_action(
                user_id=user.id,
                action_type='create',
                action_category='rag',
                resource_type='vector_note',
                resource_id=vector_note.id,
                resource_name=title,
                action_description=f'Vector note created for {content_type}',
                success=True,
                data_changed=True
            )
            
            logger.info(f"Created VectorNote {vector_note.id} with embedding")
            return vector_note
            
        except Exception as e:
            logger.error(f"Failed to create vector note: {str(e)}")
            return None
    
    def index_dataset_metadata(self, dataset: Dataset, user: User) -> bool:
        """
        Index dataset metadata for RAG
        
        Args:
            dataset: Dataset to index
            user: User who owns the dataset
            
        Returns:
            bool: True if successful
        """
        try:
            # Generate dataset summary
            summary = self._generate_dataset_summary(dataset)
            
            # Create vector note for dataset metadata
            vector_note = self.create_vector_note(
                title=f"Dataset: {dataset.name}",
                text=summary,
                scope='dataset',
                content_type='dataset_metadata',
                user=user,
                dataset=dataset,
                metadata={
                    'dataset_id': dataset.id,
                    'row_count': dataset.row_count,
                    'column_count': dataset.column_count,
                    'file_size': dataset.file_size_bytes,
                    'data_types': dataset.data_types,
                    'quality_score': dataset.data_quality_score
                }
            )
            
            if vector_note:
                logger.info(f"Indexed dataset metadata for {dataset.name}")
                return True
            else:
                logger.error(f"Failed to index dataset metadata for {dataset.name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to index dataset metadata: {str(e)}")
            return False
    
    def index_analysis_result(self, analysis_result: AnalysisResult, user: User) -> bool:
        """
        Index analysis result for RAG
        
        Args:
            analysis_result: Analysis result to index
            user: User who owns the result
            
        Returns:
            bool: True if successful
        """
        try:
            # Generate analysis summary
            summary = self._generate_analysis_summary(analysis_result)
            
            # Create vector note for analysis result
            vector_note = self.create_vector_note(
                title=f"Analysis: {analysis_result.name}",
                text=summary,
                scope='dataset',
                content_type='analysis_result',
                user=user,
                dataset=analysis_result.dataset,
                metadata={
                    'analysis_id': analysis_result.id,
                    'tool_used': analysis_result.tool_used.name,
                    'execution_time': analysis_result.execution_time_ms,
                    'confidence_score': analysis_result.confidence_score,
                    'output_type': analysis_result.output_type
                },
                confidence_score=analysis_result.confidence_score
            )
            
            if vector_note:
                logger.info(f"Indexed analysis result for {analysis_result.name}")
                return True
            else:
                logger.error(f"Failed to index analysis result for {analysis_result.name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to index analysis result: {str(e)}")
            return False
    
    def index_tool_documentation(self, tool_name: str, description: str, 
                                parameters: Dict[str, Any], examples: List[str]) -> bool:
        """
        Index tool documentation for global RAG knowledge
        
        Args:
            tool_name: Name of the tool
            description: Tool description
            parameters: Tool parameters schema
            examples: Usage examples
            
        Returns:
            bool: True if successful
        """
        try:
            # Create a system user for global content
            system_user = self._get_or_create_system_user()
            
            # Generate documentation text
            doc_text = self._generate_tool_documentation_text(
                tool_name, description, parameters, examples
            )
            
            # Create vector note for tool documentation
            vector_note = self.create_vector_note(
                title=f"Tool: {tool_name}",
                text=doc_text,
                scope='global',
                content_type='tool_documentation',
                user=system_user,
                metadata={
                    'tool_name': tool_name,
                    'parameters': parameters,
                    'examples': examples
                }
            )
            
            if vector_note:
                logger.info(f"Indexed tool documentation for {tool_name}")
                return True
            else:
                logger.error(f"Failed to index tool documentation for {tool_name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to index tool documentation: {str(e)}")
            return False
    
    def search_similar_content(self, query: str, scope: str, 
                              dataset_id: Optional[int] = None, user_id: Optional[int] = None,
                              top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar content using text query
        
        Args:
            query: Search query text
            scope: Search scope ('dataset' or 'global')
            dataset_id: Dataset ID for dataset-scoped search
            user_id: User ID for multi-tenancy
            top_k: Number of results to return
            
        Returns:
            List of similar content with metadata
        """
        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []
            
            # Search using RAG service
            results = self.rag_service.search_vectors(
                query_embedding=query_embedding,
                scope=scope,
                dataset_id=dataset_id,
                user_id=user_id,
                top_k=top_k
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'id': result['data']['id'],
                    'title': result['data']['title'],
                    'text': result['data']['text'],
                    'similarity': result['similarity'],
                    'content_type': result['data']['content_type'],
                    'confidence_score': result['data']['confidence_score'],
                    'created_at': result['data']['created_at'],
                    'metadata': result['data']['metadata']
                })
            
            logger.info(f"Found {len(formatted_results)} similar content items")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []
    
    def _validate_inputs(self, title: str, text: str, scope: str, 
                        content_type: str, user: User, dataset: Optional[Dataset]) -> bool:
        """Validate input parameters"""
        if not title or not text:
            logger.error("Title and text are required")
            return False
        
        if scope not in ['dataset', 'global']:
            logger.error(f"Invalid scope: {scope}")
            return False
        
        if scope == 'dataset' and not dataset:
            logger.error("Dataset is required for dataset scope")
            return False
        
        if scope == 'global' and dataset:
            logger.error("Dataset should not be provided for global scope")
            return False
        
        return True
    
    def _preprocess_content(self, text: str) -> str:
        """Preprocess content for embedding generation with PII masking"""
        # Apply PII masking first
        text = self._mask_pii_content(text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters that might interfere with embedding
        text = re.sub(r'[^\w\s.,!?;:-]', '', text)
        
        # Truncate if too long (sentence-transformers has limits)
        max_length = 512  # Conservative limit
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        return text
    
    def _mask_pii_content(self, text: str) -> str:
        """
        Mask PII (Personally Identifiable Information) in content
        
        Args:
            text: Input text to mask
            
        Returns:
            Text with PII masked
        """
        masked_text = text
        
        # Mask email addresses
        masked_text = re.sub(
            self.pii_patterns['email'], 
            '[EMAIL_MASKED]', 
            masked_text, 
            flags=re.IGNORECASE
        )
        
        # Mask phone numbers
        masked_text = re.sub(
            self.pii_patterns['phone'], 
            '[PHONE_MASKED]', 
            masked_text
        )
        
        # Mask SSNs
        masked_text = re.sub(
            self.pii_patterns['ssn'], 
            '[SSN_MASKED]', 
            masked_text
        )
        
        # Mask credit card numbers
        masked_text = re.sub(
            self.pii_patterns['credit_card'], 
            '[CARD_MASKED]', 
            masked_text
        )
        
        # Mask IP addresses
        masked_text = re.sub(
            self.pii_patterns['ip_address'], 
            '[IP_MASKED]', 
            masked_text
        )
        
        # Additional PII patterns
        additional_patterns = {
            'name_pattern': r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Simple name pattern
            'date_pattern': r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # Date pattern
            'address_pattern': r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)\b',  # Address pattern
        }
        
        # Mask additional patterns
        masked_text = re.sub(additional_patterns['name_pattern'], '[NAME_MASKED]', masked_text)
        masked_text = re.sub(additional_patterns['date_pattern'], '[DATE_MASKED]', masked_text)
        masked_text = re.sub(additional_patterns['address_pattern'], '[ADDRESS_MASKED]', masked_text)
        
        return masked_text
    
    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text"""
        try:
            if not text.strip():
                return None
            
            # Generate embedding
            embedding = self.embedding_model.encode(text, convert_to_tensor=False)
            
            # Convert to list of floats
            embedding_list = embedding.tolist()
            
            # Validate dimension
            if len(embedding_list) != self.embedding_dimension:
                logger.error(f"Unexpected embedding dimension: {len(embedding_list)}")
                return None
            
            return embedding_list
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            return None
    
    def _has_pii_masking(self, original_text: str, processed_text: str) -> bool:
        """Check if PII has been masked in the content"""
        # Simple check - if text length changed significantly, PII might have been masked
        return len(original_text) != len(processed_text)
    
    def _generate_dataset_summary(self, dataset: Dataset) -> str:
        """Generate summary text for dataset metadata"""
        summary_parts = [
            f"Dataset: {dataset.name}",
            f"Description: {dataset.description or 'No description'}",
            f"Rows: {dataset.row_count}, Columns: {dataset.column_count}",
            f"File size: {dataset.file_size_bytes} bytes",
            f"Quality score: {dataset.data_quality_score}",
            f"Data types: {', '.join(dataset.data_types.keys()) if dataset.data_types else 'Unknown'}"
        ]
        
        # Add column information
        if hasattr(dataset, 'columns'):
            column_info = []
            for col in dataset.columns.all()[:10]:  # Limit to first 10 columns
                column_info.append(f"{col.name} ({col.confirmed_type})")
            if column_info:
                summary_parts.append(f"Columns: {', '.join(column_info)}")
        
        return " | ".join(summary_parts)
    
    def _generate_analysis_summary(self, analysis_result: AnalysisResult) -> str:
        """Generate summary text for analysis result"""
        summary_parts = [
            f"Analysis: {analysis_result.name}",
            f"Tool: {analysis_result.tool_used.name}",
            f"Description: {analysis_result.description or 'No description'}",
            f"Execution time: {analysis_result.execution_time_ms}ms",
            f"Confidence: {analysis_result.confidence_score}",
            f"Output type: {analysis_result.output_type}"
        ]
        
        # Add result data summary
        if analysis_result.result_data:
            result_summary = str(analysis_result.result_data)[:200]  # Truncate
            summary_parts.append(f"Results: {result_summary}...")
        
        return " | ".join(summary_parts)
    
    def _generate_tool_documentation_text(self, tool_name: str, description: str,
                                         parameters: Dict[str, Any], examples: List[str]) -> str:
        """Generate documentation text for tool"""
        doc_parts = [
            f"Tool: {tool_name}",
            f"Description: {description}",
            f"Parameters: {json.dumps(parameters, indent=2)}"
        ]
        
        if examples:
            doc_parts.append(f"Examples: {' | '.join(examples)}")
        
        return " | ".join(doc_parts)
    
    def _get_or_create_system_user(self) -> User:
        """Get or create system user for global content"""
        try:
            user, created = User.objects.get_or_create(
                username='system',
                defaults={
                    'email': 'system@analytical.local',
                    'first_name': 'System',
                    'last_name': 'User',
                    'is_staff': False,
                    'is_active': True
                }
            )
            return user
        except Exception as e:
            logger.error(f"Failed to get/create system user: {str(e)}")
            # Fallback to first admin user
            return User.objects.filter(is_superuser=True).first()
