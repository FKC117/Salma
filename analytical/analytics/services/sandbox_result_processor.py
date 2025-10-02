"""
Sandbox Result Processor Service

This service processes raw sandbox execution output and creates structured
SandboxResult records with separated text and images.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from django.db import transaction
from analytics.models import SandboxExecution, SandboxResult, GeneratedImage, User, AnalysisSession

logger = logging.getLogger(__name__)


class SandboxResultProcessor:
    """
    Service for processing sandbox execution output into structured results
    """
    
    def __init__(self):
        self.image_pattern = re.compile(
            r'__SANDBOX_IMAGE_BASE64__(data:image/png;base64,[A-Za-z0-9+/=]+)'
        )
    
    def parse_sandbox_output(self, raw_output: str) -> Dict:
        """
        Extract text and images from sandbox output
        
        Args:
            raw_output: Raw output from sandbox execution
            
        Returns:
            Dictionary with parsed content
        """
        try:
            print("=== SANDBOX RESULT PROCESSOR DEBUG ===")
            print(f"Raw output length: {len(raw_output)}")
            print(f"Raw output preview: {raw_output[:500]}...")
            
            # Extract base64 images
            image_matches = self.image_pattern.findall(raw_output)
            print(f"Image matches found: {len(image_matches)}")
            
            if image_matches:
                print(f"First image match length: {len(image_matches[0])}")
                print(f"First image match preview: {image_matches[0][:100]}...")
            
            # Clean text output (remove image markers)
            clean_text = self.image_pattern.sub('', raw_output).strip()
            
            # Remove extra whitespace and empty lines
            clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text)
            clean_text = clean_text.strip()
            
            result = {
                'text_output': clean_text,
                'images': image_matches,
                'image_count': len(image_matches),
                'has_images': len(image_matches) > 0
            }
            
            print(f"Result: {result}")
            print("=== SANDBOX RESULT PROCESSOR COMPLETE ===")
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing sandbox output: {str(e)}")
            return {
                'text_output': raw_output,
                'images': [],
                'image_count': 0,
                'has_images': False,
                'error': str(e)
            }
    
    def create_sandbox_result(self, execution: SandboxExecution) -> Optional[SandboxResult]:
        """
        Process sandbox execution and create structured result
        
        Args:
            execution: SandboxExecution instance
            
        Returns:
            Created SandboxResult instance or None if failed
        """
        try:
            with transaction.atomic():
                # Parse the output
                parsed = self.parse_sandbox_output(execution.output or '')
                
                # Create SandboxResult
                result = SandboxResult.objects.create(
                    execution=execution,
                    session=execution.session,
                    user=execution.user,
                    text_output=parsed['text_output'],
                    has_images=parsed['has_images'],
                    image_count=parsed['image_count'],
                    processed=True,
                    processing_error=parsed.get('error')
                )
                
                # Create GeneratedImage records for each image
                for i, image_data in enumerate(parsed['images']):
                    try:
                        GeneratedImage.objects.create(
                            sandbox_result=result,
                            source_type='sandbox',
                            image_data=image_data,
                            name=f'Sandbox Chart {i+1}',
                            description=f'Chart generated from sandbox execution {execution.id}',
                            tool_used='matplotlib',
                            parameters_used={'execution_id': execution.id},
                            image_format='png',
                            width=800,  # Default values for sandbox images
                            height=600,
                            dpi=150,
                            file_size_bytes=len(image_data.encode('utf-8')),
                            file_path=f'sandbox/{execution.id}/chart_{i+1}.png',
                            user=execution.user
                        )
                    except Exception as e:
                        logger.error(f"Error creating GeneratedImage {i+1}: {str(e)}")
                        # Continue with other images even if one fails
                
                logger.info(f"Created SandboxResult {result.id} with {result.image_count} images")
                return result
                
        except Exception as e:
            logger.error(f"Error creating SandboxResult for execution {execution.id}: {str(e)}")
            return None
    
    def process_execution(self, execution_id: int) -> Optional[SandboxResult]:
        """
        Process a specific sandbox execution by ID
        
        Args:
            execution_id: ID of the SandboxExecution
            
        Returns:
            Created SandboxResult instance or None if failed
        """
        try:
            execution = SandboxExecution.objects.get(id=execution_id)
            return self.create_sandbox_result(execution)
        except SandboxExecution.DoesNotExist:
            logger.error(f"SandboxExecution {execution_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error processing execution {execution_id}: {str(e)}")
            return None
    
    def get_sandbox_results(self, session_id: int, user_id: int) -> List[Dict]:
        """
        Get sandbox results for a session
        
        Args:
            session_id: Analysis session ID
            user_id: User ID
            
        Returns:
            List of sandbox result dictionaries
        """
        try:
            results = SandboxResult.objects.filter(
                session_id=session_id,
                user_id=user_id
            ).prefetch_related('images').order_by('-created_at')
            
            return [
                {
                    'id': result.id,
                    'execution_id': result.execution.id,
                    'text_output': result.text_output,
                    'has_images': result.has_images,
                    'image_count': result.image_count,
                    'processed': result.processed,
                    'processing_error': result.processing_error,
                    'images': [
                        {
                            'id': img.id,
                            'image_data': img.image_data,
                            'name': img.name,
                            'description': img.description,
                            'image_format': img.image_format,
                            'width': img.width,
                            'height': img.height
                        }
                        for img in result.get_images()
                    ],
                    'created_at': result.created_at.isoformat()
                }
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting sandbox results for session {session_id}: {str(e)}")
            return []
    
    def cleanup_failed_results(self, execution_id: int):
        """
        Clean up any failed processing attempts
        
        Args:
            execution_id: ID of the SandboxExecution
        """
        try:
            SandboxResult.objects.filter(
                execution_id=execution_id,
                processed=False
            ).delete()
        except Exception as e:
            logger.error(f"Error cleaning up failed results for execution {execution_id}: {str(e)}")
