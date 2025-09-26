"""
LLM Processor with Google AI Integration

This service handles all LLM operations including text generation, analysis,
context management, and token tracking using Google AI API.
"""

import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
import google.generativeai as genai
import tiktoken
from io import BytesIO
import base64

from analytics.models import (
    User, ChatMessage, AnalysisResult, AgentRun, AgentStep,
    AuditTrail, GeneratedImage
)
from django.db import models
from analytics.services.audit_trail_manager import AuditTrailManager
from analytics.services.rag_service import RAGService

logger = logging.getLogger(__name__)


class LLMProcessor:
    """
    Service for LLM operations with Google AI integration and comprehensive token tracking
    """
    
    def __init__(self):
        self.audit_manager = AuditTrailManager()
        self.rag_service = RAGService()
        self.api_key = settings.GOOGLE_AI_API_KEY
        self.model_name = settings.GOOGLE_AI_MODEL
        self.generation_config = settings.GOOGLE_AI_GENERATION_CONFIG
        self.safety_settings = settings.GOOGLE_AI_SAFETY_SETTINGS
        
        # Token costs (per 1K tokens)
        self.input_token_cost = getattr(settings, 'TOKEN_COST_PER_INPUT', 0.0005)
        self.output_token_cost = getattr(settings, 'TOKEN_COST_PER_OUTPUT', 0.0015)
        
        # Context management
        self.max_context_messages = 10
        self.context_cache_timeout = 3600  # 1 hour
        
        # Initialize Google AI
        self._initialize_google_ai()
    
    def _initialize_google_ai(self):
        """Initialize Google AI client"""
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            logger.info(f"Google AI initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Google AI: {str(e)}")
            raise ValueError(f"Failed to initialize Google AI: {str(e)}")
    
    def generate_text(self, prompt: str, user: User, context_messages: Optional[List[Dict]] = None,
                     analysis_result: Optional[AnalysisResult] = None, 
                     include_images: bool = False, rag_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate text using Google AI with context and token tracking
        
        Args:
            prompt: Input prompt for text generation
            user: User making the request
            context_messages: Previous conversation context
            analysis_result: Associated analysis result
            include_images: Whether to include images in the generation
            rag_context: Optional RAG context for enhanced responses
            
        Returns:
            Dict containing generated text, token usage, and metadata
        """
        correlation_id = f"llm_{int(timezone.now().timestamp())}"
        start_time = time.time()
        
        try:
            # Prepare context with RAG integration
            full_prompt = self._prepare_prompt_with_context(prompt, context_messages, analysis_result, rag_context)
            
            # Calculate input tokens
            input_tokens = self._count_tokens(full_prompt)
            
            # Check user token limits
            if not self._check_token_limits(user, input_tokens):
                raise ValueError("User has exceeded token limits")
            
            # Generate response
            response = self.model.generate_content(full_prompt)
            
            # Extract response text
            generated_text = response.text if response.text else ""
            
            # Calculate output tokens
            output_tokens = self._count_tokens(generated_text)
            
            # Calculate costs
            input_cost = (input_tokens / 1000) * self.input_token_cost
            output_cost = (output_tokens / 1000) * self.output_token_cost
            total_cost = input_cost + output_cost
            
            # Update user token usage
            self._update_user_token_usage(user, input_tokens, output_tokens, total_cost)
            
            # Create chat message record
            chat_message = self._create_chat_message(
                user, generated_text, 'ai', input_tokens, output_tokens,
                analysis_result, correlation_id
            )
            
            # Log audit trail
            self.audit_manager.log_user_action(
                user_id=user.id,
                action_type='llm_generation',
                resource_type='chat_message',
                resource_id=chat_message.id,
                resource_name="AI Text Generation",
                action_description=f"Generated {output_tokens} tokens of text",
                success=True,
                correlation_id=correlation_id,
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
            
            logger.info(f"Generated text for user {user.id}: {output_tokens} tokens")
            
            return {
                'text': generated_text,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens,
                'input_cost': input_cost,
                'output_cost': output_cost,
                'total_cost': total_cost,
                'execution_time': time.time() - start_time,
                'message_id': chat_message.id,
                'correlation_id': correlation_id
            }
            
        except Exception as e:
            logger.error(f"Text generation failed: {str(e)}", exc_info=True)
            
            # Log audit trail for failure
            self.audit_manager.log_user_action(
                user_id=user.id,
                action_type='llm_generation',
                resource_type='chat_message',
                resource_name="AI Text Generation",
                action_description=f"Text generation failed: {str(e)}",
                success=False,
                error_message=str(e),
                correlation_id=correlation_id
            )
            
            raise ValueError(f"Text generation failed: {str(e)}")
    
    def analyze_data(self, data: Dict[str, Any], analysis_type: str, user: User,
                    context: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze data using LLM with specialized prompts
        
        Args:
            data: Data to analyze (tables, charts, etc.)
            analysis_type: Type of analysis to perform
            user: User requesting analysis
            context: Additional context for analysis
            
        Returns:
            Dict containing analysis results and insights
        """
        try:
            # Prepare analysis prompt based on data type
            prompt = self._prepare_analysis_prompt(data, analysis_type, context)
            
            # Generate analysis
            result = self.generate_text(prompt, user)
            
            # Parse analysis results
            analysis_results = self._parse_analysis_results(result['text'], analysis_type)
            
            return {
                'analysis_type': analysis_type,
                'insights': analysis_results.get('insights', []),
                'recommendations': analysis_results.get('recommendations', []),
                'summary': analysis_results.get('summary', ''),
                'confidence': analysis_results.get('confidence', 0.8),
                'token_usage': {
                    'input_tokens': result['input_tokens'],
                    'output_tokens': result['output_tokens'],
                    'total_cost': result['total_cost']
                },
                'execution_time': result['execution_time']
            }
            
        except Exception as e:
            logger.error(f"Data analysis failed: {str(e)}")
            raise ValueError(f"Data analysis failed: {str(e)}")
    
    def generate_analysis_plan(self, dataset_info: Dict[str, Any], goal: str, 
                              user: User, rag_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate an analysis plan for autonomous AI agent
        
        Args:
            dataset_info: Information about the dataset
            goal: Analysis goal or question
            user: User requesting the plan
            rag_context: Optional RAG context for enhanced planning
            
        Returns:
            Dict containing the analysis plan
        """
        try:
            prompt = f"""
            Generate a comprehensive analysis plan for the following dataset and goal:
            
            Dataset Information:
            - Name: {dataset_info.get('name', 'Unknown')}
            - Rows: {dataset_info.get('row_count', 0)}
            - Columns: {dataset_info.get('column_count', 0)}
            - Column Types: {dataset_info.get('column_types', {})}
            
            Analysis Goal: {goal}
            
            {f"Relevant Context from Previous Analysis:\n{rag_context}\n" if rag_context else ""}
            
            Please provide a structured analysis plan with:
            1. Data exploration steps
            2. Statistical analysis recommendations
            3. Visualization suggestions
            4. Hypothesis testing opportunities
            5. Expected insights and outcomes
            
            Format the response as a JSON object with the following structure:
            {{
                "plan_name": "Analysis Plan Name",
                "steps": [
                    {{
                        "step_number": 1,
                        "tool_name": "descriptive_statistics",
                        "description": "Step description",
                        "parameters": {{"columns": ["col1", "col2"]}},
                        "expected_output": "Expected output description"
                    }}
                ],
                "estimated_duration": "Estimated time in minutes",
                "complexity": "low|medium|high",
                "confidence": 0.0-1.0
            }}
            """
            
            result = self.generate_text(prompt, user)
            
            # Parse JSON response
            try:
                plan_data = json.loads(result['text'])
                return plan_data
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    'plan_name': 'Generated Analysis Plan',
                    'steps': [{'step_number': 1, 'tool_name': 'descriptive_statistics', 'description': 'Basic data exploration'}],
                    'estimated_duration': '30 minutes',
                    'complexity': 'medium',
                    'confidence': 0.7
                }
                
        except Exception as e:
            logger.error(f"Analysis plan generation failed: {str(e)}")
            raise ValueError(f"Analysis plan generation failed: {str(e)}")
    
    def process_batch_requests(self, requests: List[Dict[str, Any]], user: User) -> List[Dict[str, Any]]:
        """
        Process multiple LLM requests in batch for efficiency
        
        Args:
            requests: List of request dictionaries
            user: User making the requests
            
        Returns:
            List of response dictionaries
        """
        try:
            results = []
            total_input_tokens = 0
            total_output_tokens = 0
            total_cost = 0
            
            for request in requests:
                try:
                    result = self.generate_text(
                        request['prompt'],
                        user,
                        request.get('context_messages'),
                        request.get('analysis_result')
                    )
                    results.append({
                        'success': True,
                        'result': result,
                        'request_id': request.get('id')
                    })
                    
                    total_input_tokens += result['input_tokens']
                    total_output_tokens += result['output_tokens']
                    total_cost += result['total_cost']
                    
                except Exception as e:
                    results.append({
                        'success': False,
                        'error': str(e),
                        'request_id': request.get('id')
                    })
            
            # Log batch processing
            self.audit_manager.log_user_action(
                user_id=user.id,
                action_type='llm_batch_processing',
                resource_type='chat_message',
                action_description=f"Processed {len(requests)} batch requests",
                success=True,
                data_changed=True
            )
            
            logger.info(f"Processed {len(requests)} batch requests for user {user.id}")
            
            return {
                'results': results,
                'summary': {
                    'total_requests': len(requests),
                    'successful_requests': len([r for r in results if r['success']]),
                    'total_input_tokens': total_input_tokens,
                    'total_output_tokens': total_output_tokens,
                    'total_cost': total_cost
                }
            }
            
        except Exception as e:
            logger.error(f"Batch processing failed: {str(e)}")
            raise ValueError(f"Batch processing failed: {str(e)}")
    
    def get_context_messages(self, session_id: int, user: User, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent context messages for a session"""
        try:
            # Try to get from cache first
            cache_key = f"context_{session_id}_{user.id}"
            cached_context = cache.get(cache_key)
            
            if cached_context:
                return cached_context
            
            # Get from database
            messages = ChatMessage.objects.filter(
                user=user,
                session_id=session_id
            ).order_by('-created_at')[:limit]
            
            context = []
            for message in reversed(messages):  # Reverse to get chronological order
                context.append({
                    'role': 'user' if message.message_type == 'user' else 'assistant',
                    'content': message.content,
                    'timestamp': message.created_at.isoformat(),
                    'token_count': message.token_count
                })
            
            # Cache context
            cache.set(cache_key, context, self.context_cache_timeout)
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to get context messages: {str(e)}")
            return []
    
    def clear_context_cache(self, session_id: int, user: User) -> None:
        """Clear context cache for a session"""
        try:
            cache_key = f"context_{session_id}_{user.id}"
            cache.delete(cache_key)
        except Exception as e:
            logger.warning(f"Failed to clear context cache: {str(e)}")
    
    def _prepare_prompt_with_context(self, prompt: str, context_messages: Optional[List[Dict]], 
                                   analysis_result: Optional[AnalysisResult], rag_context: Optional[str] = None) -> str:
        """Prepare prompt with context and analysis results"""
        full_prompt = prompt
        
        # Add context messages
        if context_messages:
            context_text = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in context_messages[-self.max_context_messages:]
            ])
            full_prompt = f"Previous conversation:\n{context_text}\n\nCurrent request: {prompt}"
        
        # Add analysis result context
        if analysis_result:
            result_context = f"\n\nAnalysis Result Context:\n"
            result_context += f"Tool: {analysis_result.tool_used.name}\n"
            result_context += f"Output Type: {analysis_result.output_type}\n"
            
            if analysis_result.result_data:
                if analysis_result.output_type == 'table':
                    data = analysis_result.result_data.get('data', [])
                    if data:
                        result_context += f"Data: {json.dumps(data[:5], indent=2)}...\n"  # First 5 rows
                elif analysis_result.output_type == 'text':
                    text = analysis_result.result_data.get('text', '')
                    result_context += f"Text: {text[:500]}...\n"  # First 500 chars
            
            full_prompt += result_context
        
        # Add RAG context
        if rag_context:
            full_prompt += f"\n\nRelevant Context from Knowledge Base:\n{rag_context}"
        
        return full_prompt
    
    def _prepare_analysis_prompt(self, data: Dict[str, Any], analysis_type: str, 
                               context: Optional[str]) -> str:
        """Prepare specialized analysis prompt based on data type"""
        base_prompt = f"Analyze the following data for {analysis_type}:\n\n"
        
        if data.get('type') == 'table':
            table_data = data.get('data', [])
            if table_data:
                # Convert table to readable format
                headers = table_data[0] if table_data else []
                rows = table_data[1:6] if len(table_data) > 1 else []  # First 5 rows
                
                table_text = "Headers: " + ", ".join(headers) + "\n"
                table_text += "Sample data:\n"
                for row in rows:
                    table_text += ", ".join(str(cell) for cell in row) + "\n"
                
                base_prompt += f"Table Data:\n{table_text}\n"
        
        elif data.get('type') == 'chart':
            chart_info = data.get('chart_data', {})
            base_prompt += f"Chart Information:\n"
            base_prompt += f"Type: {chart_info.get('type', 'Unknown')}\n"
            base_prompt += f"Title: {chart_info.get('title', 'No title')}\n"
            base_prompt += f"Data Points: {chart_info.get('data_points', 0)}\n"
        
        if context:
            base_prompt += f"\nAdditional Context: {context}\n"
        
        base_prompt += f"\nPlease provide insights, patterns, and recommendations for this {analysis_type} analysis."
        
        return base_prompt
    
    def _parse_analysis_results(self, text: str, analysis_type: str) -> Dict[str, Any]:
        """Parse analysis results from LLM response"""
        try:
            # Try to extract structured information
            insights = []
            recommendations = []
            summary = text
            
            # Look for bullet points or numbered lists
            lines = text.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if any(keyword in line.lower() for keyword in ['insight', 'finding', 'pattern']):
                    current_section = 'insights'
                elif any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should']):
                    current_section = 'recommendations'
                elif line.startswith(('•', '-', '*', '1.', '2.', '3.')):
                    if current_section == 'insights':
                        insights.append(line.lstrip('•-*123456789. '))
                    elif current_section == 'recommendations':
                        recommendations.append(line.lstrip('•-*123456789. '))
            
            return {
                'insights': insights,
                'recommendations': recommendations,
                'summary': summary,
                'confidence': 0.8  # Default confidence
            }
            
        except Exception as e:
            logger.warning(f"Failed to parse analysis results: {str(e)}")
            return {
                'insights': [],
                'recommendations': [],
                'summary': text,
                'confidence': 0.5
            }
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception as e:
            logger.warning(f"Failed to count tokens: {str(e)}")
            # Fallback: rough estimation (1 token ≈ 4 characters)
            return len(text) // 4
    
    def _check_token_limits(self, user: User, input_tokens: int) -> bool:
        """Check if user has exceeded token limits"""
        try:
            # Get current month usage
            current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Calculate monthly usage
            monthly_usage = ChatMessage.objects.filter(
                user=user,
                created_at__gte=current_month
            ).aggregate(
                total_tokens=models.Sum('token_count')
            )['total_tokens'] or 0
            
            # Add current request
            total_usage = monthly_usage + input_tokens
            
            # Check against limit
            max_tokens = user.max_tokens_per_month
            if total_usage > max_tokens:
                logger.warning(f"User {user.id} exceeded token limit: {total_usage}/{max_tokens}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to check token limits: {str(e)}")
            return True  # Allow request if check fails
    
    def _update_user_token_usage(self, user: User, input_tokens: int, 
                                output_tokens: int, total_cost: float) -> None:
        """Update user token usage and costs"""
        try:
            with transaction.atomic():
                user.token_usage_current_month += input_tokens + output_tokens
                user.save(update_fields=['token_usage_current_month'])
                
        except Exception as e:
            logger.error(f"Failed to update user token usage: {str(e)}")
    
    def _create_chat_message(self, user: User, content: str, message_type: str,
                           input_tokens: int, output_tokens: int,
                           analysis_result: Optional[AnalysisResult],
                           correlation_id: str) -> ChatMessage:
        """Create chat message record"""
        return ChatMessage.objects.create(
            content=content,
            message_type=message_type,
            llm_model=self.model_name,
            token_count=input_tokens + output_tokens,
            analysis_result=analysis_result,
            user=user,
            metadata={
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'correlation_id': correlation_id,
                'generation_time': timezone.now().isoformat()
            }
        )
    
    def get_user_token_usage(self, user: User) -> Dict[str, Any]:
        """Get comprehensive token usage information for a user"""
        try:
            current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Get monthly usage
            monthly_messages = ChatMessage.objects.filter(
                user=user,
                created_at__gte=current_month
            )
            
            total_tokens = sum(msg.token_count or 0 for msg in monthly_messages)
            total_cost = total_tokens * (self.input_token_cost + self.output_token_cost) / 2000  # Rough estimate
            
            return {
                'current_month_usage': total_tokens,
                'monthly_limit': user.max_tokens_per_month,
                'usage_percentage': (total_tokens / user.max_tokens_per_month) * 100,
                'estimated_cost': total_cost,
                'messages_count': monthly_messages.count(),
                'average_tokens_per_message': total_tokens / monthly_messages.count() if monthly_messages.count() > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get user token usage: {str(e)}")
            return {}
    
    def reset_monthly_usage(self, user: User) -> bool:
        """Reset user's monthly token usage (admin function)"""
        try:
            user.token_usage_current_month = 0
            user.save(update_fields=['token_usage_current_month'])
            
            logger.info(f"Reset token usage for user {user.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset monthly usage: {str(e)}")
            return False
    
    def _get_rag_context_for_prompt(self, prompt: str, user: User, 
                                   analysis_result: Optional[AnalysisResult] = None) -> str:
        """
        Retrieve relevant RAG context for text generation
        
        Args:
            prompt: User prompt
            user: User making the request
            analysis_result: Associated analysis result
            
        Returns:
            Formatted RAG context string
        """
        try:
            context_parts = []
            
            # Search for relevant context based on prompt
            search_queries = [
                prompt[:100],  # First 100 chars of prompt
                f"analysis {prompt[:50]}",
                f"data {prompt[:50]}",
                f"statistics {prompt[:50]}"
            ]
            
            # Add analysis result context if available
            if analysis_result:
                dataset = analysis_result.session.primary_dataset
                search_queries.extend([
                    f"dataset {dataset.name}",
                    f"analysis result {analysis_result.tool_used.name}",
                    f"{analysis_result.tool_used.name} {dataset.name}"
                ])
            
            for query in search_queries:
                if not query.strip():
                    continue
                    
                # Search for global notes
                global_results = self.rag_service.search_vectors(
                    query=query,
                    user=user,
                    dataset=None,
                    top_k=2,
                    similarity_threshold=0.6
                )
                
                # Search for dataset-scoped notes if analysis result available
                if analysis_result:
                    dataset = analysis_result.session.primary_dataset
                    dataset_results = self.rag_service.search_vectors(
                        query=query,
                        user=user,
                        dataset=dataset,
                        top_k=3,
                        similarity_threshold=0.6
                    )
                else:
                    dataset_results = []
                
                # Combine and format results
                for result in global_results + dataset_results:
                    context_parts.append(f"""
                    Knowledge Context:
                    Title: {result.get('title', 'Unknown')}
                    Content: {result.get('text', '')[:300]}...
                    Confidence: {result.get('confidence_score', 0)}
                    """)
            
            # Combine all context
            full_context = "\n".join(context_parts[:5])  # Limit to 5 context items
            
            logger.info(f"Retrieved RAG context for prompt: {len(context_parts)} items")
            return full_context
            
        except Exception as e:
            logger.error(f"Failed to retrieve RAG context for prompt: {str(e)}")
            return ""
    
    def generate_text_with_rag(self, prompt: str, user: User, 
                             context_messages: Optional[List[Dict]] = None,
                             analysis_result: Optional[AnalysisResult] = None, 
                             include_images: bool = False) -> Dict[str, Any]:
        """
        Generate text with automatic RAG context retrieval
        
        Args:
            prompt: Input prompt for text generation
            user: User making the request
            context_messages: Previous conversation context
            analysis_result: Associated analysis result
            include_images: Whether to include images in the generation
            
        Returns:
            Dict containing generated text, token usage, and metadata
        """
        try:
            # Automatically retrieve RAG context
            rag_context = self._get_rag_context_for_prompt(prompt, user, analysis_result)
            
            # Generate text with RAG context
            return self.generate_text(
                prompt=prompt,
                user=user,
                context_messages=context_messages,
                analysis_result=analysis_result,
                include_images=include_images,
                rag_context=rag_context
            )
            
        except Exception as e:
            logger.error(f"RAG-enhanced text generation failed: {str(e)}")
            # Fallback to regular text generation
            return self.generate_text(
                prompt=prompt,
                user=user,
                context_messages=context_messages,
                analysis_result=analysis_result,
                include_images=include_images
            )
