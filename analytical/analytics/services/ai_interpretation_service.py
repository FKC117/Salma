"""
AI Interpretation Service
Handles AI-powered interpretation of analysis results
"""

import json
import logging
from typing import Dict, List, Optional, Any
from django.conf import settings
from analytics.services.llm_processor import LLMProcessor

logger = logging.getLogger(__name__)

class AIImterpretationService:
    """
    Service for providing AI-powered interpretation of analysis results
    """
    
    def __init__(self):
        self.llm_processor = LLMProcessor()
    
    def interpret_analysis_result(
        self,
        analysis_data: Dict[str, Any],
        analysis_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate AI interpretation for analysis results
        
        Args:
            analysis_data: The analysis result data
            analysis_type: Type of analysis ('text', 'table', 'chart')
            context: Additional context for interpretation
            
        Returns:
            Dictionary containing AI interpretation
        """
        try:
            # Create interpretation prompt based on analysis type
            prompt = self._create_interpretation_prompt(analysis_data, analysis_type, context)
            
            # Get AI interpretation
            interpretation = self.llm_processor.process_analysis_interpretation(prompt)
            
            return {
                'success': True,
                'interpretation': interpretation,
                'analysis_type': analysis_type,
                'timestamp': analysis_data.get('timestamp'),
                'confidence': self._calculate_confidence(analysis_data, analysis_type)
            }
            
        except Exception as e:
            logger.error(f"Error generating AI interpretation: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'analysis_type': analysis_type
            }
    
    def _create_interpretation_prompt(
        self,
        analysis_data: Dict[str, Any],
        analysis_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create interpretation prompt based on analysis type"""
        
        base_prompt = f"""
You are an expert data analyst and statistician. Please provide a comprehensive interpretation of the following {analysis_type} analysis result.

Analysis Title: {analysis_data.get('title', 'Untitled Analysis')}
Analysis Content:
{analysis_data.get('content', 'No content available')}

Please provide:
1. A clear summary of the key findings
2. Statistical significance and practical implications
3. Potential patterns or trends identified
4. Recommendations for further analysis
5. Any limitations or caveats to consider

Format your response in clear, professional language suitable for business stakeholders.
"""
        
        # Add type-specific guidance
        if analysis_type == 'text':
            base_prompt += """
Focus on:
- Statistical measures and their meaning
- Data quality and reliability
- Key insights and patterns
- Business implications
"""
        elif analysis_type == 'table':
            base_prompt += """
Focus on:
- Data structure and completeness
- Statistical relationships between variables
- Data quality metrics
- Trends and patterns in the data
- Recommendations for data improvement
"""
        elif analysis_type == 'chart':
            base_prompt += """
Focus on:
- Visual patterns and trends
- Statistical relationships shown
- Data distribution characteristics
- Outliers and anomalies
- Visual clarity and effectiveness
"""
        
        # Add context if provided
        if context:
            base_prompt += f"\n\nAdditional Context:\n{json.dumps(context, indent=2)}"
        
        return base_prompt
    
    def _calculate_confidence(
        self,
        analysis_data: Dict[str, Any],
        analysis_type: str
    ) -> float:
        """Calculate confidence score for the interpretation"""
        confidence = 0.5  # Base confidence
        
        # Adjust based on content quality
        content = analysis_data.get('content', '')
        if len(content) > 100:
            confidence += 0.1
        if len(content) > 500:
            confidence += 0.1
        if len(content) > 1000:
            confidence += 0.1
        
        # Adjust based on analysis type
        if analysis_type == 'chart':
            confidence += 0.1  # Charts are generally more interpretable
        elif analysis_type == 'table':
            confidence += 0.05  # Tables provide structured data
        
        # Adjust based on data completeness
        if 'statistical_summary' in content.lower():
            confidence += 0.1
        if 'correlation' in content.lower():
            confidence += 0.05
        if 'significance' in content.lower():
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def generate_insights(
        self,
        analysis_data: Dict[str, Any],
        analysis_type: str,
        insight_count: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate specific insights from analysis results"""
        try:
            prompt = f"""
Based on the following {analysis_type} analysis, generate {insight_count} specific, actionable insights.

Analysis Data:
{analysis_data.get('content', 'No content available')}

For each insight, provide:
1. A clear, concise statement
2. The supporting evidence
3. The business impact
4. A confidence level (0-100%)

Format as JSON array with objects containing: title, description, evidence, impact, confidence
"""
            
            response = self.llm_processor.process_analysis_interpretation(prompt)
            
            # Try to parse JSON response
            try:
                insights = json.loads(response)
                if isinstance(insights, list):
                    return insights
            except json.JSONDecodeError:
                pass
            
            # Fallback: create insights from text response
            return self._parse_insights_from_text(response, insight_count)
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return []
    
    def _parse_insights_from_text(self, text: str, count: int) -> List[Dict[str, Any]]:
        """Parse insights from text response when JSON parsing fails"""
        insights = []
        lines = text.split('\n')
        
        current_insight = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith(('1.', '2.', '3.', '4.', '5.')):
                if current_insight:
                    insights.append(current_insight)
                current_insight = {
                    'title': line,
                    'description': '',
                    'evidence': '',
                    'impact': '',
                    'confidence': 75
                }
            elif current_insight and line:
                if not current_insight['description']:
                    current_insight['description'] = line
                else:
                    current_insight['description'] += ' ' + line
        
        if current_insight:
            insights.append(current_insight)
        
        return insights[:count]
    
    def generate_recommendations(
        self,
        analysis_data: Dict[str, Any],
        analysis_type: str,
        recommendation_count: int = 3
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on analysis"""
        try:
            prompt = f"""
Based on the following {analysis_type} analysis, generate {recommendation_count} specific, actionable recommendations.

Analysis Data:
{analysis_data.get('content', 'No content available')}

For each recommendation, provide:
1. A clear action item
2. The rationale
3. Priority level (High/Medium/Low)
4. Expected impact
5. Implementation difficulty (Easy/Medium/Hard)

Format as JSON array with objects containing: action, rationale, priority, impact, difficulty
"""
            
            response = self.llm_processor.process_analysis_interpretation(prompt)
            
            # Try to parse JSON response
            try:
                recommendations = json.loads(response)
                if isinstance(recommendations, list):
                    return recommendations
            except json.JSONDecodeError:
                pass
            
            # Fallback: create recommendations from text response
            return self._parse_recommendations_from_text(response, recommendation_count)
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    def _parse_recommendations_from_text(self, text: str, count: int) -> List[Dict[str, Any]]:
        """Parse recommendations from text response when JSON parsing fails"""
        recommendations = []
        lines = text.split('\n')
        
        current_rec = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith(('1.', '2.', '3.', '4.', '5.')):
                if current_rec:
                    recommendations.append(current_rec)
                current_rec = {
                    'action': line,
                    'rationale': '',
                    'priority': 'Medium',
                    'impact': 'Medium',
                    'difficulty': 'Medium'
                }
            elif current_rec and line:
                if not current_rec['rationale']:
                    current_rec['rationale'] = line
                else:
                    current_rec['rationale'] += ' ' + line
        
        if current_rec:
            recommendations.append(current_rec)
        
        return recommendations[:count]
    
    def compare_analyses(
        self,
        analysis1: Dict[str, Any],
        analysis2: Dict[str, Any],
        analysis_type: str
    ) -> Dict[str, Any]:
        """Compare two analysis results and provide insights"""
        try:
            prompt = f"""
Compare the following two {analysis_type} analyses and provide insights on their differences, similarities, and implications.

Analysis 1:
Title: {analysis1.get('title', 'Untitled')}
Content: {analysis1.get('content', 'No content')}

Analysis 2:
Title: {analysis2.get('title', 'Untitled')}
Content: {analysis2.get('content', 'No content')}

Please provide:
1. Key differences between the analyses
2. Similarities and common patterns
3. Which analysis provides more valuable insights
4. Recommendations for combining or using both analyses
5. Potential reasons for differences

Format your response in clear, structured language.
"""
            
            comparison = self.llm_processor.process_analysis_interpretation(prompt)
            
            return {
                'success': True,
                'comparison': comparison,
                'analysis1_title': analysis1.get('title'),
                'analysis2_title': analysis2.get('title'),
                'analysis_type': analysis_type
            }
            
        except Exception as e:
            logger.error(f"Error comparing analyses: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'analysis_type': analysis_type
            }


# Global instance
ai_interpretation_service = AIImterpretationService()
