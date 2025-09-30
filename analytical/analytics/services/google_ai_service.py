"""
Google AI API Integration Service (T010)
Handles Google AI API calls with token tracking and rate limiting
"""

import os
import json
import time
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime, timedelta
import google.generativeai as genai
import tiktoken

class GoogleAIService:
    """Service for Google AI API integration with token tracking"""
    
    def __init__(self):
        self.api_key = settings.GOOGLE_AI_API_KEY
        self.model_name = settings.GOOGLE_AI_MODEL  # gemini-1.5-flash
        self.max_tokens_per_user = settings.MAX_TOKENS_PER_USER
        self.token_cost_per_input = settings.TOKEN_COST_PER_INPUT
        self.token_cost_per_output = settings.TOKEN_COST_PER_OUTPUT
        
        # Configure Google AI
        genai.configure(api_key=self.api_key)
        
        # Configure generation settings
        self.generation_config = genai.types.GenerationConfig(**settings.GOOGLE_AI_GENERATION_CONFIG)
        self.safety_settings = settings.GOOGLE_AI_SAFETY_SETTINGS
        
        # Create model with configuration
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings
        )
        
        # Token encoding for counting
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        try:
            return len(self.tokenizer.encode(text))
        except Exception as e:
            # Fallback: rough estimation (1 token ≈ 4 characters)
            return len(text) // 4
    
    def get_user_token_usage(self, user_id: int) -> Dict:
        """Get current token usage for user"""
        cache_key = f"user_tokens_{user_id}"
        usage = cache.get(cache_key, {
            'input_tokens': 0,
            'output_tokens': 0,
            'total_cost': 0.0,
            'reset_date': timezone.now().date()
        })
        
        # Reset monthly
        if usage['reset_date'] != timezone.now().date():
            usage = {
                'input_tokens': 0,
                'output_tokens': 0,
                'total_cost': 0.0,
                'reset_date': timezone.now().date()
            }
            cache.set(cache_key, usage, 86400 * 30)  # 30 days
        
        return usage
    
    def update_user_token_usage(self, user_id: int, input_tokens: int, output_tokens: int):
        """Update user token usage"""
        usage = self.get_user_token_usage(user_id)
        usage['input_tokens'] += input_tokens
        usage['output_tokens'] += output_tokens
        usage['total_cost'] += (input_tokens * self.token_cost_per_input + 
                               output_tokens * self.token_cost_per_output)
        
        cache_key = f"user_tokens_{user_id}"
        cache.set(cache_key, usage, 86400 * 30)  # 30 days
        
        return usage
    
    def check_token_limit(self, user_id: int, additional_tokens: int = 0) -> Tuple[bool, str]:
        """Check if user has exceeded token limit"""
        usage = self.get_user_token_usage(user_id)
        total_tokens = usage['input_tokens'] + usage['output_tokens'] + additional_tokens
        
        if total_tokens > self.max_tokens_per_user:
            return False, f"Token limit exceeded. Used: {total_tokens}/{self.max_tokens_per_user}"
        
        return True, "OK"
    
    def generate_response(self, prompt: str, user_id: int, context: Optional[List[Dict]] = None) -> Dict:
        """
        Generate AI response with token tracking
        
        Args:
            prompt: User prompt
            user_id: User ID for token tracking
            context: Previous conversation context
            
        Returns:
            Dict with response, tokens used, and metadata
        """
        try:
            # Check token limit
            prompt_tokens = self.count_tokens(prompt)
            can_proceed, message = self.check_token_limit(user_id, prompt_tokens)
            
            if not can_proceed:
                return {
                    'success': False,
                    'error': message,
                    'tokens_used': 0,
                    'cost': 0.0
                }
            
            # Prepare context if provided
            full_prompt = prompt
            if context:
                context_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in context[-10:]])  # Last 10 messages
                full_prompt = f"Context:\n{context_text}\n\nCurrent question: {prompt}"
            
            # Generate response
            start_time = time.time()
            response = self.model.generate_content(full_prompt)
            generation_time = time.time() - start_time
            
            # Count tokens
            input_tokens = self.count_tokens(full_prompt)
            output_tokens = self.count_tokens(response.text)
            
            # Update token usage
            self.update_user_token_usage(user_id, input_tokens, output_tokens)
            
            # Calculate cost
            cost = input_tokens * self.token_cost_per_input + output_tokens * self.token_cost_per_output
            
            return {
                'success': True,
                'response': response.text,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens,
                'cost': cost,
                'generation_time': generation_time,
                'model': self.model_name,
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tokens_used': 0,
                'cost': 0.0
            }
    
    def batch_generate_responses(self, prompts: List[str], user_id: int) -> List[Dict]:
        """Generate multiple responses in batch"""
        results = []
        
        for prompt in prompts:
            result = self.generate_response(prompt, user_id)
            results.append(result)
            
            # Add delay between requests to avoid rate limiting
            time.sleep(0.5)
        
        return results
    
    def get_user_usage_stats(self, user_id: int) -> Dict:
        """Get detailed usage statistics for user"""
        usage = self.get_user_token_usage(user_id)
        
        return {
            'user_id': user_id,
            'input_tokens': usage['input_tokens'],
            'output_tokens': usage['output_tokens'],
            'total_tokens': usage['input_tokens'] + usage['output_tokens'],
            'total_cost': usage['total_cost'],
            'remaining_tokens': self.max_tokens_per_user - (usage['input_tokens'] + usage['output_tokens']),
            'usage_percentage': ((usage['input_tokens'] + usage['output_tokens']) / self.max_tokens_per_user) * 100,
            'reset_date': usage['reset_date']
        }
    
    def format_response_for_chat(self, response: str, analysis_results: Optional[Dict] = None) -> str:
        """Format AI response for chat display"""
        formatted_response = response
        
        if analysis_results:
            # Add analysis results to response
            if 'tables' in analysis_results:
                formatted_response += "\n\n**Analysis Tables:**\n"
                for table in analysis_results['tables']:
                    formatted_response += f"- {table['title']}\n"
            
            if 'charts' in analysis_results:
                formatted_response += "\n\n**Generated Charts:**\n"
                for chart in analysis_results['charts']:
                    formatted_response += f"- {chart['title']}\n"
            
            if 'recommendations' in analysis_results:
                formatted_response += "\n\n**Recommendations:**\n"
                for rec in analysis_results['recommendations']:
                    formatted_response += f"- {rec}\n"
        
        return formatted_response
    
    def validate_api_key(self) -> bool:
        """Validate Google AI API key"""
        try:
            # Test API key by listing models
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            models = list(genai.list_models())
            return len(models) > 0
        except Exception as e:
            print(f"API key validation failed: {e}")
            return False

# Global instance
google_ai_service = GoogleAIService()
