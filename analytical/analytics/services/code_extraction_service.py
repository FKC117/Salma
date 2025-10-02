"""
Code Extraction Service

This service handles extraction of Python code blocks from LLM responses
and prepares them for sandbox execution.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)


class CodeExtractionService:
    """
    Service for extracting and formatting Python code from LLM responses
    """
    
    def __init__(self):
        self.python_patterns = [
            # Markdown-style code blocks (most reliable)
            r'```python\n(.*?)```',
            r'```py\n(.*?)```',
            
            # Generic code blocks only if they contain Python keywords
            r'```\n((?:import|from|def|class|if|for|while|try|except|with|print|return|yield|lambda|async|await).*?)```',
            
            # AI-generated patterns with stricter validation
            r'### [^\n]*\n\npython\n((?:import|from|def|class|if|for|while|try|except|with|print|return|yield|lambda|async|await).*?)(?=\n\n###|\s*$)',
            r'\n\s*python\s*\n((?:import|from|def|class|if|for|while|try|except|with|print|return|yield|lambda|async|await).*?)(?=\n\s*[A-Z#]|\n\s*$)',
            
            # Direct Python code patterns with validation
            r'(?:^|\n)(python\s*\n((?:import|from|def|class|if|for|while|try|except|with|print|return|yield|lambda|async|await).*?))(?=\n\n|\n[A-Z]|\n#|\Z)',
            
            # Pattern for "python" followed by import statements (no newline)
            r'(?:^|\n)(python\s+import.*?)(?=\n\n|\n[A-Z]|\n#|\Z)',
            
            # New pattern for "Python Code" header format with validation
            r'Python Code\s*\n\s*\n\s*\n\s*\n((?:import|from|def|class|if|for|while|try|except|with|print|return|yield|lambda|async|await).*?)(?=\n\s*$|\n\s*\n\s*[A-Z]|\Z)',
            
            # Pattern for "Python Code" followed by multiple newlines and then code with validation
            r'Python Code\s*\n+((?:import|from|def|class|if|for|while|try|except|with|print|return|yield|lambda|async|await).*?)(?=\n\s*$|\n\s*\n\s*[A-Z]|\Z)',
        ]
    
    def extract_python_code_blocks(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract all Python code blocks from text
        
        Args:
            text: Input text containing potential code blocks
            
        Returns:
            List of dictionaries containing extracted code blocks
        """
        # Reduced debug output for performance
        print(f"=== CODE EXTRACTION DEBUG ===")
        print(f"Input text length: {len(text)}")
        
        code_blocks = []
        
        for i, pattern in enumerate(self.python_patterns):
            matches = re.finditer(pattern, text, re.DOTALL | re.MULTILINE)
            for match in matches:
                code = match.group(1).strip()
                
                # Clean up the code
                code = self._clean_python_code(code)
                
                if self._is_valid_python_code(code):
                    code_blocks.append({
                        'code': code,
                        'language': 'python',
                        'start_pos': match.start(),
                        'end_pos': match.end(),
                        'pattern_used': pattern
                    })
                    print(f"✅ Pattern {i+1}: Valid Python code ({len(code)} chars)")
                else:
                    print(f"❌ Pattern {i+1}: Invalid Python code rejected")
        
        # Remove duplicates and sort by position
        code_blocks = self._deduplicate_code_blocks(code_blocks)
        
        print(f"=== CODE EXTRACTION RESULT ===")
        print(f"Total code blocks extracted: {len(code_blocks)}")
        print(f"===============================")
        
        logger.info(f"Extracted {len(code_blocks)} Python code blocks")
        return code_blocks
    
    def _clean_python_code(self, code: str) -> str:
        """Clean and normalize Python code"""
        # Remove 'python' prefix if present
        if code.startswith('python'):
            code = code[6:].strip()
        
        # Remove leading/trailing whitespace
        code = code.strip()
        
        # Remove any markdown formatting
        code = re.sub(r'^```.*?\n', '', code)
        code = re.sub(r'\n```$', '', code)
        
        return code
    
    def _is_valid_python_code(self, code: str) -> bool:
        """Check if the extracted text is valid Python code"""
        if not code or len(code.strip()) < 10:
            return False
        
        # Check for markdown/HTML patterns that should be rejected
        markdown_patterns = [
            r'^#+\s+',  # Headers starting with #
            r'^\*\s+',  # Bullet points
            r'^\d+\.\s+',  # Numbered lists
            r'^##\s+',  # Markdown headers
            r'^\*\*.*\*\*',  # Bold text
            r'^_.*_$',  # Italic text
            r'^\|.*\|',  # Table rows
            r'^```',  # Code block markers
            r'^<.*>$',  # HTML tags
        ]
        
        for pattern in markdown_patterns:
            if re.match(pattern, code.strip(), re.MULTILINE):
                print(f"❌ Rejected markdown/HTML pattern: {pattern}")
                return False
        
        # Check for Python keywords or imports (must have at least one)
        python_indicators = [
            'import ', 'from ', 'def ', 'class ', 'if ', 'for ', 'while ',
            'try:', 'except:', 'with ', 'return ', 'print(', 'pd.', 'plt.',
            'sns.', 'numpy', 'pandas', 'matplotlib', 'seaborn', 'df.',
            'plt.figure', 'plt.show', 'plt.savefig', 'plt.close'
        ]
        
        code_lower = code.lower()
        has_python_indicator = any(indicator in code_lower for indicator in python_indicators)
        
        # Additional check: must not be mostly text/descriptive content
        lines = code.strip().split('\n')
        code_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
        
        if len(code_lines) < 2:  # Must have at least 2 non-comment lines
            print(f"❌ Too few code lines: {len(code_lines)}")
            return False
        
        # Check if it's mostly descriptive text (not code)
        descriptive_words = ['insight', 'analysis', 'interpretation', 'conclusion', 'summary', 'finding']
        text_content_ratio = sum(1 for line in code_lines if any(word in line.lower() for word in descriptive_words)) / len(code_lines)
        
        if text_content_ratio > 0.5:  # More than 50% descriptive text
            print(f"❌ Too much descriptive text: {text_content_ratio:.2f}")
            return False
        
        return has_python_indicator
    
    def _deduplicate_code_blocks(self, code_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate code blocks"""
        seen_codes = set()
        unique_blocks = []
        
        for block in code_blocks:
            code_hash = hash(block['code'])
            if code_hash not in seen_codes:
                seen_codes.add(code_hash)
                unique_blocks.append(block)
        
        return unique_blocks
    
    def format_code_block_for_display(self, code: str) -> Dict[str, str]:
        """
        Format code block for display (no execute button since we auto-execute)
        
        Args:
            code: Python code to format
            
        Returns:
            Dictionary with formatted HTML
        """
        html = f'''
        <div class="code-block-container">
            <div class="code-header">
                <div class="code-title">
                    <i class="fas fa-code"></i> Python Code
                </div>
                <div class="code-actions">
                    <span class="badge bg-success">
                        <i class="fas fa-check"></i> Auto-executed
                    </span>
                </div>
            </div>
            <pre class="code-block"><code class="language-python">{code}</code></pre>
        </div>
        '''
        
        return {
            'html': html,
            'raw_code': code
        }
    
    def extract_and_format_code_blocks(self, text: str) -> str:
        """
        Extract Python code blocks and replace them with formatted HTML
        
        Args:
            text: Input text containing code blocks
            
        Returns:
            Text with code blocks replaced by formatted HTML
        """
        code_blocks = self.extract_python_code_blocks(text)
        
        # Sort by position (reverse order to avoid position shifts)
        code_blocks.sort(key=lambda x: x['start_pos'], reverse=True)
        
        formatted_text = text
        
        for block in code_blocks:
            formatted_block = self.format_code_block_for_display(block['code'])
            
            # Replace the original code block with formatted HTML
            start_pos = block['start_pos']
            end_pos = block['end_pos']
            
            formatted_text = (
                formatted_text[:start_pos] + 
                formatted_block['html'] + 
                formatted_text[end_pos:]
            )
        
        return formatted_text

