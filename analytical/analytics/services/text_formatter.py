"""
Professional Text Formatter for Analysis Results

This service formats raw analysis text into human-readable, professional format
while preserving tables, charts, and code blocks.
"""

import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class TextFormatter:
    """
    Service for formatting analysis text into professional, readable format
    """
    
    def __init__(self):
        self.section_patterns = [
            r'###\s*(\d+\.?\s*[^#\n]+)',  # Main sections (### 1. Section Name)
            r'##\s*([^#\n]+)',           # Subsections (## Section Name)
            r'#\s*([^#\n]+)',            # Major headings (# Title)
        ]
        
        self.interpretation_patterns = [
            r'Interpretation\s*\([^)]*\):\s*([^#]+?)(?=###|##|#|$)',
            r'Interpretation:\s*([^#]+?)(?=###|##|#|$)',
            r'Key Findings:\s*([^#]+?)(?=###|##|#|$)',
            r'Summary:\s*([^#]+?)(?=###|##|#|$)',
        ]
    
    def format_analysis_text(self, text: str) -> str:
        """
        Format analysis text into professional, readable format
        
        Args:
            text: Raw analysis text
            
        Returns:
            Formatted text with professional styling
        """
        try:
            # Split text into sections
            sections = self._split_into_sections(text)
            
            # Format each section
            formatted_sections = []
            for section in sections:
                formatted_section = self._format_section(section)
                if formatted_section.strip():
                    formatted_sections.append(formatted_section)
            
            # Join sections with proper spacing
            formatted_text = '\n\n'.join(formatted_sections)
            
            # Clean up extra whitespace
            formatted_text = self._clean_whitespace(formatted_text)
            
            return formatted_text
            
        except Exception as e:
            logger.error(f"Error formatting analysis text: {str(e)}")
            return text  # Return original text if formatting fails
    
    def _split_into_sections(self, text: str) -> List[Dict[str, Any]]:
        """Split text into logical sections"""
        sections = []
        
        # Find all section headers
        section_matches = []
        for pattern in self.section_patterns:
            matches = list(re.finditer(pattern, text, re.MULTILINE))
            section_matches.extend(matches)
        
        # Sort by position
        section_matches.sort(key=lambda x: x.start())
        
        # Remove duplicate headers at the same position
        unique_matches = []
        seen_positions = set()
        for match in section_matches:
            if match.start() not in seen_positions:
                unique_matches.append(match)
                seen_positions.add(match.start())
        
        # Extract sections
        current_pos = 0
        for i, match in enumerate(unique_matches):
            # Add content before this section
            if match.start() > current_pos:
                content = text[current_pos:match.start()].strip()
                if content:
                    sections.append({
                        'type': 'content',
                        'content': content,
                        'position': current_pos
                    })
            
            # Add section header
            section_title = match.group(1).strip()
            sections.append({
                'type': 'section',
                'title': section_title,
                'position': match.start()
            })
            
            current_pos = match.end()
        
        # Add remaining content
        if current_pos < len(text):
            content = text[current_pos:].strip()
            if content:
                sections.append({
                    'type': 'content',
                    'content': content,
                    'position': current_pos
                })
        
        return sections
    
    def _format_section(self, section: Dict[str, Any]) -> str:
        """Format a single section"""
        if section['type'] == 'section':
            return self._format_section_header(section['title'])
        elif section['type'] == 'content':
            return self._format_content(section['content'])
        else:
            return section.get('content', '')
    
    def _format_section_header(self, title: str) -> str:
        """Format section headers professionally"""
        # Clean up the title
        title = title.strip()
        
        # Remove numbering if it exists
        title = re.sub(r'^\d+\.?\s*', '', title)
        
        # Capitalize properly
        title = title.title()
        
        # Format as professional heading
        return f"## {title}"
    
    def _format_content(self, content: str) -> str:
        """Format content sections"""
        if not content.strip():
            return ""
        
        # Remove any section headers that might be in the content
        content = re.sub(r'^#+\s+.*$', '', content, flags=re.MULTILINE)
        content = content.strip()
        
        if not content:
            return ""
        
        # Check if content contains code blocks, tables, or charts
        if self._contains_code_block(content):
            return self._format_code_section(content)
        elif self._contains_table(content):
            return self._format_table_section(content)
        elif self._contains_chart(content):
            return self._format_chart_section(content)
        else:
            return self._format_text_section(content)
    
    def _contains_code_block(self, content: str) -> bool:
        """Check if content contains code blocks"""
        return '```python' in content or '```' in content
    
    def _contains_table(self, content: str) -> bool:
        """Check if content contains tables"""
        return '|' in content and '---' in content
    
    def _contains_chart(self, content: str) -> bool:
        """Check if content contains charts"""
        return '__SANDBOX_IMAGE__' in content or 'Generated Plot' in content
    
    def _format_code_section(self, content: str) -> str:
        """Format sections containing code"""
        # Extract code blocks and text separately
        parts = re.split(r'```python\s*\n(.*?)\n```', content, flags=re.DOTALL)
        
        formatted_parts = []
        for i, part in enumerate(parts):
            if i % 2 == 0:  # Text part
                if part.strip():
                    formatted_parts.append(self._format_text_section(part))
            else:  # Code part
                if part.strip():
                    formatted_parts.append(f"```python\n{part.strip()}\n```")
        
        return '\n\n'.join(formatted_parts)
    
    def _format_table_section(self, content: str) -> str:
        """Format sections containing tables"""
        # Tables are already well-formatted, just clean up surrounding text
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                if '|' in line and '---' not in line:  # Table row
                    formatted_lines.append(line)
                elif '---' in line:  # Table separator
                    formatted_lines.append(line)
                elif line.startswith('---'):  # Table header
                    formatted_lines.append(line)
                else:  # Regular text
                    formatted_lines.append(self._format_text_line(line))
        
        return '\n'.join(formatted_lines)
    
    def _format_chart_section(self, content: str) -> str:
        """Format sections containing charts"""
        # Charts are already well-formatted, just clean up surrounding text
        return self._format_text_section(content)
    
    def _format_text_section(self, content: str) -> str:
        """Format regular text sections"""
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                formatted_line = self._format_text_line(line)
                formatted_lines.append(formatted_line)
        
        return '\n'.join(formatted_lines)
    
    def _format_text_line(self, line: str) -> str:
        """Format a single line of text"""
        # Skip empty lines
        if not line.strip():
            return ""
        
        # Skip lines that are just dashes or separators
        if re.match(r'^[-=*]+$', line.strip()):
            return ""
        
        # Skip lines that are just section headers (already processed)
        if re.match(r'^#+\s+', line.strip()):
            return ""
        
        # Format bullet points
        if re.match(r'^\*\s+', line):
            return f"• {line[2:].strip()}"
        
        # Format numbered lists
        if re.match(r'^\d+\.\s+', line):
            return line
        
        # Format interpretation sections
        if line.startswith('Interpretation'):
            return f"**{line}**"
        
        # Format key findings
        if line.startswith('Key Findings'):
            return f"**{line}**"
        
        # Format summary sections
        if line.startswith('Summary'):
            return f"**{line}**"
        
        # Format recommendations
        if line.startswith('Recommendation'):
            return f"**{line}**"
        
        # Regular text - ensure proper capitalization
        if line.endswith('.'):
            return line
        elif line.endswith(':'):
            return line
        else:
            return line
    
    def _clean_whitespace(self, text: str) -> str:
        """Clean up excessive whitespace"""
        # Remove multiple consecutive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove trailing whitespace from lines
        lines = text.split('\n')
        cleaned_lines = [line.rstrip() for line in lines]
        
        return '\n'.join(cleaned_lines)
    
    def format_interpretation(self, interpretation: str) -> str:
        """Format interpretation sections specifically"""
        if not interpretation.strip():
            return ""
        
        # Clean up the interpretation
        interpretation = interpretation.strip()
        
        # Remove "Interpretation:" prefix if present
        interpretation = re.sub(r'^Interpretation\s*\([^)]*\):\s*', '', interpretation)
        interpretation = re.sub(r'^Interpretation:\s*', '', interpretation)
        
        # Format bullet points
        lines = interpretation.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                if line.startswith('*'):
                    # Convert * to •
                    formatted_lines.append(f"• {line[1:].strip()}")
                else:
                    formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def format_recommendations(self, recommendations: str) -> str:
        """Format recommendations sections specifically"""
        if not recommendations.strip():
            return ""
        
        # Clean up the recommendations
        recommendations = recommendations.strip()
        
        # Format as professional recommendations
        lines = recommendations.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                if line.startswith('*'):
                    # Convert * to •
                    formatted_lines.append(f"• {line[1:].strip()}")
                else:
                    formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
