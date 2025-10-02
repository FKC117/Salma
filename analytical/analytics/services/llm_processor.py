"""
LLM Processor with Google AI Integration (Production) and Ollama (Development)

This service handles all LLM operations including text generation, analysis,
context management, and token tracking using Google AI API for production
and Ollama for local development.
"""

import json
import logging
import time
import requests
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from django.contrib.auth import get_user_model
from io import BytesIO
import base64

from analytics.models import (
    ChatMessage, AnalysisResult, AgentRun, AgentStep,
    AuditTrail, GeneratedImage, AnalysisSession
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from analytics.models import User
from django.db import models
from analytics.services.audit_trail_manager import AuditTrailManager
from analytics.services.rag_service import RAGService

logger = logging.getLogger(__name__)
User = get_user_model()


class LLMProcessor:
    """
    Service for LLM operations with Google AI integration (production) and Ollama (development)
    """
    
    def __init__(self, model_name: Optional[str] = None):
        self.audit_manager = AuditTrailManager()
        self.rag_service = RAGService()
        
        # Store the selected model name for later use
        self.selected_model = model_name  # Don't default here, we'll determine it below
        
        # Ollama configuration (for development)
        self.ollama_url = getattr(settings, 'OLLAMA_URL', 'http://localhost:11434')
        self.ollama_model = getattr(settings, 'OLLAMA_MODEL', 'deepseek-r1:8b')
        self.use_ollama = getattr(settings, 'USE_OLLAMA', True)  # Set to False for production
        
        # Google AI configuration (for production)
        self.google_api_key = getattr(settings, 'GOOGLE_AI_API_KEY', '')
        self.google_model_name = getattr(settings, 'GOOGLE_AI_MODEL', 'gemini-flash-latest')
        
        # Ollama generation config
        self.generation_config = getattr(settings, 'OLLAMA_GENERATION_CONFIG', {
            'temperature': 0.7,
            'top_p': 0.9,
            'max_tokens': 4000
        })
        
        # Google AI generation config
        self.google_generation_config = getattr(settings, 'GOOGLE_AI_GENERATION_CONFIG', {
            'temperature': 0.7,
            'top_p': 0.8,
            'top_k': 40,
            'max_output_tokens': 8192,
        })
        
        # Token costs (per 1K tokens)
        self.input_token_cost = getattr(settings, 'TOKEN_COST_PER_INPUT', 0.0005)
        self.output_token_cost = getattr(settings, 'TOKEN_COST_PER_OUTPUT', 0.0015)
        
        # Context management
        self.max_context_messages = 10
        self.context_cache_timeout = 3600  # 1 hour
        
        # Initialize the appropriate model based on settings and environment
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the appropriate AI model based on settings and availability"""
        # Determine which model to use
        if self.selected_model:
            target_model = self.selected_model
        elif not self.use_ollama and self.google_api_key:
            target_model = 'gemini'
        else:
            target_model = 'ollama'
        
        # Try to initialize the target model
        if target_model == 'gemini' and self.google_api_key:
            if self._initialize_google_ai():
                self.model_name = 'gemini'
                return
            else:
                logger.warning("Failed to initialize Google AI, trying fallback options")
        
        # Fallback to Ollama if target was Gemini but failed, or if target is Ollama
        if target_model == 'ollama' or (target_model == 'gemini' and self.use_ollama):
            if self._initialize_ollama():
                self.model_name = 'ollama'
                return
            else:
                logger.warning("Failed to initialize Ollama")
        
        # Last resort: try Google AI if not already tried
        if target_model != 'gemini' and self.google_api_key:
            if self._initialize_google_ai():
                self.model_name = 'gemini'
                return
        
        # If all fails, raise an error
        raise Exception("Failed to initialize any AI model. Check your configuration and connectivity.")
    
    def _initialize_google_ai(self):
        """Initialize Google AI client"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.google_api_key)
            
            # Create GenerationConfig object
            from google.generativeai.types import GenerationConfig
            generation_config_obj = GenerationConfig(
                temperature=self.google_generation_config.get('temperature', 0.7),
                top_p=self.google_generation_config.get('top_p', 0.8),
                top_k=self.google_generation_config.get('top_k', 40),
                max_output_tokens=self.google_generation_config.get('max_output_tokens', 8192),
            )
            
            self.model = genai.GenerativeModel(
                model_name=self.google_model_name,
                generation_config=generation_config_obj,
                safety_settings=getattr(settings, 'GOOGLE_AI_SAFETY_SETTINGS', [])
            )
            logger.info(f"Google AI initialized with model: {self.google_model_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Google AI model '{self.google_model_name}': {str(e)}")
            return False
    
    def _initialize_ollama(self):
        """Initialize Ollama client"""
        try:
            # Test Ollama connection
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info(f"Ollama initialized with model: {self.ollama_model}")
                return True
            else:
                logger.error(f"Ollama API returned status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Failed to initialize Ollama: {str(e)}")
            return False
    
    def _generate_with_ollama(self, prompt: str) -> str:
        """Generate text using Ollama API"""
        try:
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.generation_config.get('temperature', 0.7),
                    "top_p": self.generation_config.get('top_p', 0.9),
                    "num_predict": self.generation_config.get('max_tokens', 4000)
                }
            }
            
            # No timeout for Ollama to prevent timeout issues
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return "Error generating response from Ollama"
                
        except Exception as e:
            logger.error(f"Ollama generation failed: {str(e)}")
            # Return a fallback response instead of error
            return "I'm here to help you analyze your data! However, I'm experiencing some technical difficulties with my AI model. Please try again in a moment, or let me know what specific analysis you'd like to perform on your dataset."
    
    def _generate_with_google_ai(self, prompt: str) -> str:
        """Generate text using Google AI API"""
        try:
            # Google AI generation (now enabled for production)
            print(f"=== GOOGLE AI API CALL DEBUG ===")
            print(f"Prompt length: {len(prompt)}")
            print(f"Model: {self.model}")
            print(f"API Key configured: {bool(self.google_api_key)}")
            print(f"Making API call...")
            
            response = self.model.generate_content(prompt)
            
            print(f"Response received: {type(response)}")
            print(f"Response attributes: {dir(response)}")
            print(f"===============================")
            
            # Handle different response types - improved handling for complex responses
            try:
                # First try the simple text accessor
                if hasattr(response, 'text') and response.text:
                    return response.text
            except ValueError:
                # If simple text accessor fails, use the parts accessor
                print("Simple text accessor failed, using parts accessor...")
            
            # Extract text from parts (more reliable method)
            if hasattr(response, 'parts') and response.parts:
                print(f"Extracting text from {len(response.parts)} parts...")
                text_parts = []
                for i, part in enumerate(response.parts):
                    print(f"Part {i}: {type(part)} - {dir(part)}")
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                        print(f"Part {i} text length: {len(part.text)}")
                if text_parts:
                    return ''.join(text_parts)
            
            # Extract text from candidates (fallback method)
            if hasattr(response, 'candidates') and response.candidates:
                print(f"Extracting text from {len(response.candidates)} candidates...")
                text_parts = []
                for i, candidate in enumerate(response.candidates):
                    print(f"Candidate {i}: {type(candidate)} - {dir(candidate)}")
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        for j, part in enumerate(candidate.content.parts):
                            print(f"Candidate {i}, Part {j}: {type(part)} - {dir(part)}")
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                                print(f"Candidate {i}, Part {j} text length: {len(part.text)}")
                if text_parts:
                    return ''.join(text_parts)
            
            # If no text found, log the response structure for debugging
            print(f"No text content found in response")
            print(f"Response type: {type(response)}")
            print(f"Response attributes: {dir(response)}")
            logger.warning("Google AI response has no text content")
            return "No response generated from Google AI"
                
        except Exception as e:
            # Enhanced error handling for Google AI API
            print(f"=== GOOGLE AI ERROR DEBUG ===")
            print(f"Exception type: {type(e)}")
            print(f"Exception message: {str(e)}")
            print(f"Exception attributes: {dir(e)}")
            if hasattr(e, 'status_code'):
                print(f"Status code: {e.status_code}")
            if hasattr(e, 'response'):
                print(f"Response: {e.response}")
            print(f"=============================")
            
            error_details = self._extract_google_ai_error_details(e)
            logger.error(f"Google AI generation failed: {error_details}")
            return f"Google AI Error: {error_details}"
    
    def _extract_google_ai_error_details(self, error: Exception) -> str:
        """Extract detailed error information from Google AI API exceptions"""
        try:
            error_str = str(error)
            error_type = type(error).__name__
            
            # Check for specific Google AI error types
            if hasattr(error, 'status_code'):
                status_code = error.status_code
                if status_code == 429:
                    return f"Rate limit exceeded (429). You've exceeded the requests per minute (RPM) or tokens per minute (TPM) limit. Please try again in a few minutes."
                elif status_code == 400:
                    return f"Bad request (400). Check your prompt length and content. Prompt may be too long or contain invalid characters."
                elif status_code == 401:
                    return f"Authentication failed (401). Check your API key configuration."
                elif status_code == 403:
                    return f"Access forbidden (403). Check your API permissions and billing setup."
                elif status_code == 500:
                    return f"Google AI server error (500). This could be due to: 1) Service maintenance, 2) Quota exceeded (check daily limits), 3) Model overload. Try again in a few minutes."
                elif status_code == 503:
                    return f"Service unavailable (503). Google AI is temporarily down for maintenance."
                else:
                    return f"HTTP {status_code}: {error_str}"
            
            # Check for quota exceeded errors
            if "quota" in error_str.lower() or "limit" in error_str.lower():
                return f"Quota/Limit exceeded: {error_str}"
            
            # Check for token limit errors
            if "token" in error_str.lower() and "limit" in error_str.lower():
                return f"Token limit exceeded: {error_str}"
            
            # Check for content policy violations
            if "policy" in error_str.lower() or "safety" in error_str.lower():
                return f"Content policy violation: {error_str}"
            
            # Check for model-specific errors
            if "model" in error_str.lower():
                return f"Model error: {error_str}"
            
            # Check for billing/payment issues
            if "billing" in error_str.lower() or "payment" in error_str.lower():
                return f"Billing/Payment issue: {error_str}"
            
            # Check for internal server errors
            if "internal" in error_str.lower() and "error" in error_str.lower():
                return f"Internal server error: {error_str}. This is usually temporary - try again in a few minutes."
            
            # Check for service unavailable
            if "service" in error_str.lower() and "unavailable" in error_str.lower():
                return f"Service unavailable: {error_str}. Google AI may be experiencing issues."
            
            # Check for response parsing errors
            if "response.text" in error_str.lower() and "quick accessor" in error_str.lower():
                return f"Response parsing error: {error_str}. This is a technical issue with the response format."
            
            # Generic error with type information
            return f"{error_type}: {error_str}"
            
        except Exception as parse_error:
            # Fallback if error parsing fails
            return f"Unknown error: {str(error)} (Parse error: {str(parse_error)})"
    
    def _count_tokens(self, text: str) -> int:
        """Simple token counting for Ollama (approximation)"""
        # Simple approximation: 1 token ≈ 4 characters for English text
        # This is a rough estimate, but sufficient for development
        return len(text) // 4
    
    def generate_text(self, prompt: str, user, context_messages: Optional[List[Dict]] = None,
                     analysis_result: Optional[AnalysisResult] = None, 
                     include_images: bool = False, rag_context: Optional[str] = None,
                     session: Optional[AnalysisSession] = None) -> Dict[str, Any]:
        """
        Generate text using Ollama (development) or Google AI (production) with context and token tracking
        
        Args:
            prompt: Input prompt for text generation
            user: User making the request
            context_messages: Previous conversation context
            analysis_result: Associated analysis result
            include_images: Whether to include images in the generation
            rag_context: Optional RAG context for enhanced responses
            session: Optional AnalysisSession for context
            
        Returns:
            Dict containing generated text, token usage, and metadata
        """
        correlation_id = f"llm_{int(timezone.now().timestamp())}"
        start_time = time.time()
        
        # DEBUG: Log input parameters
        print(f"=== LLM PROCESSOR DEBUG ===")
        print(f"User ID: {getattr(user, 'id', 'None')}")
        print(f"Session ID: {getattr(session, 'id', 'None') if session else 'None'}")
        print(f"Analysis Result ID: {getattr(analysis_result, 'id', 'None') if analysis_result else 'None'}")
        print(f"Dataset ID: {getattr(getattr(session, 'primary_dataset', None), 'id', 'None') if session and getattr(session, 'primary_dataset', None) else 'None'}")
        print(f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        print(f"Context messages count: {len(context_messages) if context_messages else 0}")
        print(f"RAG context: {rag_context[:100] if rag_context else 'None'}")
        print(f"Model used: {self.model_name}")
        print(f"========================")
        
        try:
            # Prepare context with RAG integration and dataset information
            full_prompt = self._prepare_prompt_with_context(prompt, context_messages, analysis_result, rag_context, session)
            
            # DEBUG: Log prepared prompt
            print(f"=== PREPARED PROMPT DEBUG ===")
            print(f"Full prompt length: {len(full_prompt)}")
            print(f"Full prompt preview: {full_prompt[:200]}{'...' if len(full_prompt) > 200 else ''}")
            print(f"============================")
            
            # Calculate input tokens
            input_tokens = self._count_tokens(full_prompt)
            
            # Check user token limits
            if not self._check_token_limits(user, input_tokens):
                raise ValueError("User has exceeded token limits")
            
            # Generate response using the selected model
            print(f"=== GENERATION START ===")
            print(f"Using model: {self.model_name}")
            if self.model_name == 'gemini' and not self.use_ollama and self.google_api_key:
                print("Calling Google AI generation...")
                generated_text = self._generate_with_google_ai(full_prompt)
            elif self.use_ollama:
                print("Calling Ollama generation...")
                generated_text = self._generate_with_ollama(full_prompt)
            else:
                # Fallback to Google AI if Ollama is not available
                print("Fallback to Google AI generation...")
                generated_text = self._generate_with_google_ai(full_prompt)
            print(f"=== GENERATION END ===")
            
            # DEBUG: Log generated response
            print(f"=== GENERATED RESPONSE DEBUG ===")
            print(f"Generated text length: {len(generated_text)}")
            print(f"Generated text preview: {generated_text[:200]}{'...' if len(generated_text) > 200 else ''}")
            print(f"===============================")
            
            # Calculate output tokens
            output_tokens = self._count_tokens(generated_text)
            
            # Calculate costs
            input_cost = (input_tokens / 1000) * self.input_token_cost
            output_cost = (output_tokens / 1000) * self.output_token_cost
            total_cost = input_cost + output_cost
            
            # Update user token usage
            self._update_user_token_usage(user, input_tokens, output_tokens, total_cost)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            result = {
                'text': generated_text,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens,
                'total_cost': total_cost,
                'execution_time': execution_time,
                'correlation_id': correlation_id,
                'model_used': self.model_name
            }
            
            # DEBUG: Log final result
            print(f"=== FINAL RESULT DEBUG ===")
            print(f"Input tokens: {input_tokens}")
            print(f"Output tokens: {output_tokens}")
            print(f"Total tokens: {result['total_tokens']}")
            print(f"Total cost: {result['total_cost']}")
            print(f"Execution time: {result['execution_time']:.2f}s")
            print(f"==========================")
            
            return result
            
        except Exception as e:
            logger.error(f"Text generation failed: {str(e)}", exc_info=True)
            print(f"=== ERROR IN LLM PROCESSOR ===")
            print(f"Error: {str(e)}")
            print(f"User ID: {getattr(user, 'id', 'None')}")
            print(f"=============================")
            raise ValueError(f"Text generation failed: {str(e)}")
    
    def process_message(self, user, message: str, session_id: Optional[str] = None, 
                       context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process chat message and generate AI response
        
        Args:
            user: User sending the message
            message: User's message
            session_id: Optional session ID for context
            context: Optional additional context
            
        Returns:
            Dict containing response and metadata
        """
        try:
            # Get or create session if session_id provided
            session = None
            if session_id:
                try:
                    session = AnalysisSession.objects.get(id=int(session_id))
                except (AnalysisSession.DoesNotExist, ValueError):
                    # If session doesn't exist or session_id is not a valid integer, 
                    # we'll create chat messages without session
                    pass
            
            # Get context messages from database
            context_messages = self.get_context_messages(int(session_id) if session_id else 0, user) if session_id else []
            
            # Add current message to context
            context_messages.append({
                'role': 'user',
                'content': message,
                'timestamp': timezone.now().isoformat()
            })
            
            # Get RAG context if available
            rag_context = None
            if session_id:
                try:
                    # Use search_vectors_by_text method
                    rag_results = self.rag_service.search_vectors_by_text(
                        query=message,
                        user=user,
                        top_k=5
                    )
                    rag_context = '\n'.join([result.get('data', {}).get('text', '') for result in rag_results])
                except Exception as e:
                    logger.warning(f"RAG context retrieval failed: {str(e)}")
            
            # Generate response with dataset context
            result = self.generate_text(
                prompt=message,
                user=user,
                context_messages=context_messages,
                rag_context=rag_context,
                session=session  # Pass the session to generate_text for dataset context
            )
            
            # Create chat message records
            correlation_id = result.get('correlation_id', '') or str(int(timezone.now().timestamp()))
            user_message = self._create_chat_message(
                user, message, 'user', 0, 0, None, correlation_id, session
            )
            
            ai_message = self._create_chat_message(
                user, result['text'], 'ai', 
                result['input_tokens'], result['output_tokens'], 
                None, correlation_id, session
            )
            
            return {
                'success': True,
                'message_id': ai_message.id if hasattr(ai_message, 'id') else 0,
                'user_message': message,
                'response': result['text'],
                'input_tokens': result['input_tokens'],
                'output_tokens': result['output_tokens'],
                'total_tokens': result['input_tokens'] + result['output_tokens'],
                'cost': result.get('total_cost', 0.0),
                'created_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Message processing failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_data(self, data: Dict[str, Any], analysis_type: str, user,
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
                              user, rag_context: Optional[str] = None) -> Dict[str, Any]:
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
            
            {f"Relevant Context from Previous Analysis:{chr(10)}{rag_context}{chr(10)}" if rag_context else ""}
            
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
    
    def process_batch_requests(self, requests: List[Dict[str, Any]], user) -> List[Dict[str, Any]]:
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
            }  # type: ignore
            
        except Exception as e:
            logger.error(f"Batch processing failed: {str(e)}")
            raise ValueError(f"Batch processing failed: {str(e)}")
    
    def get_context_messages(self, session_id: int, user, limit: int = 10):
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
    
    def clear_context_cache(self, session_id: int, user) -> None:
        """Clear context cache for a session"""
        try:
            cache_key = f"context_{session_id}_{user.id}"
            cache.delete(cache_key)
        except Exception as e:
            logger.warning(f"Failed to clear context cache: {str(e)}")
    
    def _prepare_prompt_with_context(self, prompt: str, context_messages: Optional[List[Dict]], 
                                   analysis_result: Optional[AnalysisResult], rag_context: Optional[str] = None,
                                   session: Optional[AnalysisSession] = None) -> str:
        """Prepare prompt with context, analysis results, and dataset information"""
        # Add output contract instruction to ensure consistent code formatting and context handling
        output_contract = """
IMPORTANT CODE EXECUTION REQUIREMENTS:
1. When you output Python code, always wrap it in a triple-backtick code block with the python language tag:
```python
# your code here
```

2. CRITICAL: Each code block is executed independently. To maintain context between blocks:
   - Always include necessary imports in each code block
   - Re-run data loading/preparation in each block if needed
   - Use descriptive variable names and comments
   - Handle data type conversions properly (e.g., encode categorical variables before correlation analysis)
   - Include error handling for data operations

3. REQUIRED IMPORTS: Always include these imports in each code block:
```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
```

4. OUTPUT FORMAT: Use simple text output without emojis, colors, or special formatting:
   - Use plain text for interpretations
   - Use simple markdown tables (not complex formatting)
   - NEVER use status indicators like ✅, ❌, or any emojis
   - NEVER include "Status:", "Execution Time:", "Code Execution Result", or any execution status sections
   - NEVER include "Code Execution Error" or similar error status sections
   - Keep output clean and professional
   - Use only standard ASCII characters

5. Do not include prose inside the code fence. This ensures the code can be detected and executed in the sandbox.
"""
        
        full_prompt = prompt + output_contract
        
        # Add dataset context if session is provided
        if session:
            dataset = session.primary_dataset
            dataset_info = f"""
Dataset Context:
- Name: {dataset.name}
- Description: {dataset.description or 'No description provided'}
- Rows: {dataset.row_count}
- Columns: {dataset.column_count}
- Data Quality Score: {dataset.data_quality_score or 'N/A'}
- Column Types: {json.dumps(dataset.data_types, indent=2) if dataset.data_types else 'Not available'}
"""
            full_prompt = f"{dataset_info}\n\n{full_prompt}"
        
        # Add context messages
        if context_messages:
            context_text = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in context_messages[-self.max_context_messages:]
            ])
            full_prompt = f"Previous conversation:\n{context_text}\n\nCurrent request: {full_prompt}"
        
        # Add analysis result context
        if analysis_result:
            result_context = f"\n\nAnalysis Result Context:\n"
            result_context += f"Tool: {analysis_result.tool_used.name}\n"
            result_context += f"Output Type: {analysis_result.output_type}\n"
            
            if analysis_result.result_data:
                if analysis_result.output_type == 'table':
                    data = analysis_result.result_data.get('data', []) if isinstance(analysis_result.result_data, dict) and 'data' in analysis_result.result_data else []
                    if data:
                        result_context += f"Data: {json.dumps(data[:5], indent=2)}...\n"  # First 5 rows
                elif analysis_result.output_type == 'text':
                    text = analysis_result.result_data.get('text', '') if isinstance(analysis_result.result_data, dict) and 'text' in analysis_result.result_data else ''
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
    
    # _count_tokens method moved to top of class for Ollama compatibility
    
    def _check_token_limits(self, user, input_tokens: int) -> bool:
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
    
    def _update_user_token_usage(self, user, input_tokens: int, 
                                output_tokens: int, total_cost: float) -> None:
        """Update user token usage and costs"""
        try:
            with transaction.atomic():
                user.token_usage_current_month += input_tokens + output_tokens
                user.save(update_fields=['token_usage_current_month'])
                
        except Exception as e:
            logger.error(f"Failed to update user token usage: {str(e)}")
    
    def _generate_fallback_response(self, prompt: str) -> str:
        """
        Generate a fallback response when Google AI API is unavailable
        """
        # Simple keyword-based fallback responses
        prompt_lower = prompt.lower()
        
        if "interpret" in prompt_lower and "analysis" in prompt_lower:
            return """I apologize, but I'm currently experiencing technical difficulties with the AI service. However, I can provide some general insights about your analysis:

**General Analysis Interpretation:**
- The data shows statistical patterns that can be interpreted
- Key metrics indicate trends and relationships in your dataset
- Visualizations help identify outliers and distributions
- Statistical measures provide insights into data quality and characteristics

**Recommendations:**
- Review the statistical summaries for key insights
- Examine visualizations for patterns and outliers
- Consider the data quality metrics provided
- Look for correlations and trends in the results

Please try the AI interpretation again in a few minutes, or contact support if the issue persists."""
        
        elif "help" in prompt_lower or "assist" in prompt_lower:
            return """I'm here to help you with your data analysis! While I'm experiencing some technical difficulties, I can still assist you with:

**Available Features:**
- Run various analysis tools on your datasets
- Generate descriptive statistics and visualizations
- Create correlation analyses and statistical summaries
- Upload and manage your datasets
- View analysis history and results

**Getting Started:**
1. Upload your dataset using the upload button
2. Select analysis tools from the tools menu
3. Configure parameters and run analyses
4. View results with charts and statistics

Please try again in a few minutes for AI-powered interpretations."""
        
        else:
            return """I apologize, but I'm currently experiencing technical difficulties with the AI service. 

**What I can still help with:**
- Running analysis tools on your data
- Generating statistical summaries and visualizations
- Managing your datasets and analysis sessions
- Viewing your analysis history

**For AI interpretations:**
Please try again in a few minutes. The AI service should be restored shortly.

Thank you for your patience!"""
    
    def _create_chat_message(self, user, content: str, message_type: str,
                           input_tokens: int, output_tokens: int,
                           analysis_result: Optional[AnalysisResult],
                           correlation_id: str, session: Optional[AnalysisSession]):
        """Create chat message record"""
        return ChatMessage.objects.create(
            content=content,
            message_type=message_type,
            llm_model=self.ollama_model if self.use_ollama else getattr(self, 'model_name', 'unknown'),
            token_count=input_tokens + output_tokens,
            analysis_result=analysis_result,
            user=user,
            session=session,
            metadata={
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'correlation_id': correlation_id,
                'generation_time': timezone.now().isoformat()
            }
        )
    
    def get_user_token_usage(self, user) -> Dict[str, Any]:
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
    
    def reset_monthly_usage(self, user) -> bool:
        """Reset user's monthly token usage (admin function)"""
        try:
            user.token_usage_current_month = 0
            user.save(update_fields=['token_usage_current_month'])
            
            logger.info(f"Reset token usage for user {user.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset monthly usage: {str(e)}")
            return False
    
    def _get_rag_context_for_prompt(self, prompt: str, user, 
                                   analysis_result = None) -> str:
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
                dataset = analysis_result.session.primary_dataset if analysis_result and analysis_result.session else None
                if dataset:
                    search_queries.extend([
                        f"dataset {dataset.name}",
                        f"analysis result {analysis_result.tool_used.name}",
                        f"{analysis_result.tool_used.name} {dataset.name}"
                    ])
            
            for query in search_queries:
                if not query.strip():
                    continue
                    
                # Search for global notes
                global_results = self.rag_service.search_vectors_by_text(
                    query=query,
                    user=user,
                    dataset=None,
                    top_k=2,
                    similarity_threshold=0.6
                )
                
                # Search for dataset-scoped notes if analysis result available
                if analysis_result:
                    dataset = analysis_result.session.primary_dataset
                    dataset_results = self.rag_service.search_vectors_by_text(
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
    
    def generate_text_with_rag(self, prompt: str, user, 
                             context_messages = None,
                             analysis_result = None, 
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