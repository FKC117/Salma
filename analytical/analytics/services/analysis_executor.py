"""
Analysis Executor for Tool Execution

This service handles the execution of analysis tools with comprehensive error handling,
caching, and result management. It integrates with LangChain tools and provides
secure execution environment.
"""

import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
import traceback

from analytics.models import (
    AnalysisTool, AnalysisResult, AnalysisSession, Dataset, 
    GeneratedImage, User, AuditTrail
)
from analytics.services.audit_trail_manager import AuditTrailManager
from analytics.services.column_type_manager import ColumnTypeManager
from analytics.services.vector_note_manager import VectorNoteManager

logger = logging.getLogger(__name__)


class AnalysisExecutor:
    """
    Service for executing analysis tools with comprehensive error handling and caching
    """
    
    def __init__(self):
        self.audit_manager = AuditTrailManager()
        self.column_manager = ColumnTypeManager()
        self.vector_note_manager = VectorNoteManager()
        self.cache_timeout = settings.ANALYSIS_CACHE_TTL
        self.max_execution_time = 300  # 5 minutes
        self.supported_output_types = ['table', 'chart', 'text', 'image', 'json']
        
        # Configure matplotlib for non-interactive use
        plt.style.use('default')
        sns.set_style("darkgrid")
        
        # Set up figure defaults
        plt.rcParams['figure.figsize'] = (10, 6)
        plt.rcParams['figure.dpi'] = 100
        plt.rcParams['savefig.dpi'] = 100
        plt.rcParams['font.size'] = 10
    
    def execute_analysis(self, tool_name: str, parameters: Dict[str, Any], 
                        session: AnalysisSession, user: User) -> Dict[str, Any]:
        """
        Execute an analysis tool with the given parameters
        
        Args:
            tool_name: Name of the analysis tool to execute
            parameters: Parameters for the tool execution
            session: Analysis session
            user: User executing the analysis
            
        Returns:
            Dict containing analysis results and metadata
        """
        correlation_id = f"analysis_{int(timezone.now().timestamp())}"
        start_time = time.time()
        
        try:
            # Get analysis tool
            tool = AnalysisTool.objects.get(name=tool_name, is_active=True)
            
            # Validate parameters
            self._validate_parameters(tool, parameters)
            
            # Check cache first
            cache_key = self._generate_cache_key(tool_name, parameters, session)
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info(f"Using cached result for tool {tool_name}")
                return self._load_cached_result(cached_result)
            
            # Load dataset
            dataset = session.primary_dataset
            df = self._load_dataset(dataset)
            
            # Validate column types
            self._validate_column_types(tool, df)
            
            # Execute tool
            result_data = self._execute_tool_function(tool, parameters, df, session)
            
            # Create analysis result
            with transaction.atomic():
                analysis_result = self._create_analysis_result(
                    tool, parameters, result_data, session, user, 
                    time.time() - start_time, correlation_id
                )
                
                # Cache the result
                self._cache_result(cache_key, analysis_result)
                
                # RAG Indexing: Create vector note for analysis result
                self._index_analysis_result_for_rag(analysis_result, result_data, user, session)
                
                # Log audit trail
                self.audit_manager.log_action(
                    user_id=user.id,
                    action_type='analysis',
                    action_category='analysis',
                    resource_type='analysis_result',
                    resource_id=analysis_result.id,
                    resource_name=f"{tool.display_name} Analysis",
                    action_description=f"Analysis tool {tool.display_name} executed successfully",
                    success=True,
                    correlation_id=correlation_id,
                    execution_time_ms=int((time.time() - start_time) * 1000)
                )
            
            logger.info(f"Analysis {tool_name} executed successfully in {time.time() - start_time:.2f}s")
            
            return {
                'analysis_id': analysis_result.id,
                'tool_name': tool.display_name,
                'result_data': result_data,
                'execution_time': time.time() - start_time,
                'cached': False,
                'success': True
            }
            
        except AnalysisTool.DoesNotExist:
            error_msg = f"Analysis tool '{tool_name}' not found or inactive"
            logger.error(error_msg)
            self._log_analysis_error(user, tool_name, error_msg, correlation_id)
            raise ValueError(error_msg)
            
        except Exception as e:
            error_msg = f"Analysis execution failed: {str(e)}"
            logger.error(f"Analysis {tool_name} failed: {str(e)}", exc_info=True)
            self._log_analysis_error(user, tool_name, error_msg, correlation_id)
            raise
    
    def _validate_parameters(self, tool: AnalysisTool, parameters: Dict[str, Any]) -> None:
        """Validate parameters against tool schema"""
        required_params = tool.required_parameters
        optional_params = tool.optional_parameters
        
        # Check required parameters
        for param in required_params:
            if param not in parameters:
                raise ValueError(f"Required parameter '{param}' is missing")
        
        # Check parameter types and values
        for param, value in parameters.items():
            if param in required_params or param in optional_params:
                # Basic validation - can be extended with more sophisticated validation
                if value is None and param in required_params:
                    raise ValueError(f"Required parameter '{param}' cannot be None")
    
    def _validate_column_types(self, tool: AnalysisTool, df: pd.DataFrame) -> None:
        """Validate that dataset has required column types for the tool"""
        required_types = tool.required_column_types
        
        if not required_types:
            return
        
        # Get column types from dataset
        column_types = {}
        for column in df.columns:
            detected_type = self.column_manager.detect_column_type(df[column])
            column_types[column] = detected_type
        
        # Check if required types are present
        for required_type in required_types:
            if not any(required_type in col_type for col_type in column_types.values()):
                raise ValueError(f"Tool requires at least one column of type '{required_type}'")
    
    def _execute_tool_function(self, tool: AnalysisTool, parameters: Dict[str, Any], 
                              df: pd.DataFrame, session: AnalysisSession) -> Dict[str, Any]:
        """Execute the actual tool function"""
        try:
            # Import and execute tool function
            tool_module = __import__(f'analytics.tools.{tool.tool_class}', fromlist=[tool.tool_function])
            tool_function = getattr(tool_module, tool.tool_function)
            
            # Execute with timeout
            result = tool_function(df, parameters, session)
            
            # Validate result format
            self._validate_result_format(result, tool)
            
            return result
            
        except ImportError as e:
            raise ValueError(f"Tool module not found: {str(e)}")
        except AttributeError as e:
            raise ValueError(f"Tool function not found: {str(e)}")
        except Exception as e:
            raise ValueError(f"Tool execution failed: {str(e)}")
    
    def _validate_result_format(self, result: Dict[str, Any], tool: AnalysisTool) -> None:
        """Validate that result has the expected format"""
        if not isinstance(result, dict):
            raise ValueError("Tool result must be a dictionary")
        
        # Check for required result fields
        if 'output_type' not in result:
            raise ValueError("Tool result must include 'output_type'")
        
        if result['output_type'] not in self.supported_output_types:
            raise ValueError(f"Unsupported output type: {result['output_type']}")
        
        # Validate based on output type
        if result['output_type'] == 'table' and 'data' not in result:
            raise ValueError("Table output must include 'data' field")
        elif result['output_type'] == 'chart' and 'chart_data' not in result:
            raise ValueError("Chart output must include 'chart_data' field")
        elif result['output_type'] == 'text' and 'text' not in result:
            raise ValueError("Text output must include 'text' field")
    
    def _load_dataset(self, dataset: Dataset) -> pd.DataFrame:
        """Load dataset from Parquet file"""
        try:
            if not dataset.parquet_path:
                raise ValueError("Dataset does not have a Parquet file")
            
            df = pd.read_parquet(dataset.parquet_path)
            return df
            
        except Exception as e:
            raise ValueError(f"Failed to load dataset: {str(e)}")
    
    def _create_analysis_result(self, tool: AnalysisTool, parameters: Dict[str, Any],
                               result_data: Dict[str, Any], session: AnalysisSession,
                               user: User, execution_time: float, correlation_id: str) -> AnalysisResult:
        """Create AnalysisResult record"""
        return AnalysisResult.objects.create(
            name=f"{tool.display_name} Analysis",
            description=f"Analysis using {tool.display_name} tool",
            tool_used=tool,
            session=session,
            dataset=session.primary_dataset,
            result_data=result_data,
            parameters_used=parameters,
            execution_time_ms=int(execution_time * 1000),
            output_type=result_data.get('output_type', 'text'),
            confidence_score=self._calculate_confidence_score(result_data),
            quality_score=self._calculate_quality_score(result_data),
            user=user
        )
    
    def _calculate_confidence_score(self, result_data: Dict[str, Any]) -> float:
        """Calculate confidence score for analysis result"""
        # Base confidence score
        confidence = 0.8
        
        # Adjust based on result quality indicators
        if result_data.get('output_type') == 'table':
            data = result_data.get('data', [])
            if len(data) > 0:
                confidence += 0.1
        elif result_data.get('output_type') == 'chart':
            chart_data = result_data.get('chart_data', {})
            if chart_data.get('data_points', 0) > 10:
                confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _calculate_quality_score(self, result_data: Dict[str, Any]) -> float:
        """Calculate quality score for analysis result"""
        # Base quality score
        quality = 0.7
        
        # Adjust based on result completeness
        if result_data.get('output_type') == 'table':
            data = result_data.get('data', [])
            if len(data) > 0:
                quality += 0.2
        elif result_data.get('output_type') == 'chart':
            chart_data = result_data.get('chart_data', {})
            if chart_data.get('data_points', 0) > 5:
                quality += 0.2
        
        return min(quality, 1.0)
    
    def _generate_cache_key(self, tool_name: str, parameters: Dict[str, Any], 
                           session: AnalysisSession) -> str:
        """Generate cache key for analysis result"""
        # Create deterministic key from tool name, parameters, and dataset
        key_data = {
            'tool': tool_name,
            'parameters': sorted(parameters.items()),
            'dataset_id': session.primary_dataset.id,
            'session_id': session.id
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return f"analysis_{hash(key_string)}"
    
    def _cache_result(self, cache_key: str, analysis_result: AnalysisResult) -> None:
        """Cache analysis result"""
        try:
            cache_data = {
                'analysis_id': analysis_result.id,
                'result_data': analysis_result.result_data,
                'execution_time': analysis_result.execution_time_ms,
                'created_at': analysis_result.created_at.isoformat()
            }
            
            cache.set(cache_key, cache_data, self.cache_timeout)
            analysis_result.cache_key = cache_key
            analysis_result.cache_expires_at = timezone.now() + timedelta(seconds=self.cache_timeout)
            analysis_result.is_cached = True
            analysis_result.save(update_fields=['cache_key', 'cache_expires_at', 'is_cached'])
            
        except Exception as e:
            logger.warning(f"Failed to cache analysis result: {str(e)}")
    
    def _load_cached_result(self, cached_data: Dict[str, Any]) -> Dict[str, Any]:
        """Load result from cache"""
        return {
            'analysis_id': cached_data['analysis_id'],
            'result_data': cached_data['result_data'],
            'execution_time': cached_data['execution_time'],
            'cached': True,
            'success': True
        }
    
    def _log_analysis_error(self, user: User, tool_name: str, error_msg: str, correlation_id: str) -> None:
        """Log analysis error to audit trail"""
        try:
            self.audit_manager.log_action(
                user_id=user.id,
                action_type='analysis',
                action_category='analysis',
                resource_type='analysis_result',
                resource_name=f"{tool_name} Analysis",
                action_description=f"Analysis tool {tool_name} execution failed",
                success=False,
                error_message=error_msg,
                correlation_id=correlation_id
            )
        except Exception as e:
            logger.error(f"Failed to log analysis error: {str(e)}")
    
    def get_analysis_result(self, analysis_id: int, user: User) -> Optional[AnalysisResult]:
        """Get analysis result by ID"""
        try:
            return AnalysisResult.objects.get(id=analysis_id, user=user)
        except AnalysisResult.DoesNotExist:
            return None
    
    def list_analysis_results(self, session: AnalysisSession, user: User, 
                             limit: int = 50) -> List[AnalysisResult]:
        """List analysis results for a session"""
        return AnalysisResult.objects.filter(
            session=session, user=user
        ).order_by('-created_at')[:limit]
    
    def delete_analysis_result(self, analysis_id: int, user: User) -> bool:
        """Delete analysis result"""
        try:
            result = AnalysisResult.objects.get(id=analysis_id, user=user)
            
            # Clear cache if exists
            if result.cache_key:
                cache.delete(result.cache_key)
            
            # Delete associated images
            result.generated_images.all().delete()
            
            # Delete result
            result.delete()
            
            # Log audit trail
            self.audit_manager.log_action(
                user_id=user.id,
                action_type='delete',
                action_category='analysis',
                resource_type='analysis_result',
                resource_id=analysis_id,
                resource_name=result.name,
                action_description="Analysis result deleted",
                success=True,
                data_changed=True
            )
            
            return True
            
        except AnalysisResult.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Failed to delete analysis result {analysis_id}: {str(e)}")
            return False
    
    def generate_chart(self, chart_data: Dict[str, Any], chart_type: str = 'line') -> str:
        """Generate chart and return base64 encoded image"""
        try:
            plt.figure(figsize=(10, 6))
            
            if chart_type == 'line':
                plt.plot(chart_data.get('x', []), chart_data.get('y', []))
            elif chart_type == 'bar':
                plt.bar(chart_data.get('x', []), chart_data.get('y', []))
            elif chart_type == 'scatter':
                plt.scatter(chart_data.get('x', []), chart_data.get('y', []))
            elif chart_type == 'histogram':
                plt.hist(chart_data.get('data', []), bins=chart_data.get('bins', 10))
            else:
                raise ValueError(f"Unsupported chart type: {chart_type}")
            
            plt.title(chart_data.get('title', 'Chart'))
            plt.xlabel(chart_data.get('xlabel', 'X'))
            plt.ylabel(chart_data.get('ylabel', 'Y'))
            
            # Save to bytes
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
            buffer.seek(0)
            
            # Encode as base64
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            plt.close()
            
            return image_base64
            
        except Exception as e:
            logger.error(f"Chart generation failed: {str(e)}")
            raise ValueError(f"Chart generation failed: {str(e)}")
    
    def save_generated_image(self, image_base64: str, analysis_result: AnalysisResult,
                           image_name: str, user: User) -> GeneratedImage:
        """Save generated image to database and file system"""
        try:
            # Decode base64 image
            image_data = base64.b64decode(image_base64)
            
            # Create image record
            image = GeneratedImage.objects.create(
                name=image_name,
                description=f"Generated chart for {analysis_result.name}",
                image_format='PNG',
                width=1000,  # Default values
                height=600,
                dpi=100,
                tool_used=analysis_result.tool_used,
                parameters_used=analysis_result.parameters_used,
                analysis_result=analysis_result,
                user=user
            )
            
            # Save image file
            image_path = f"images/analysis_{analysis_result.id}_{image.id}.png"
            image.file_path = image_path
            image.save()
            
            # Save to file system
            full_path = settings.MEDIA_ROOT / image_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'wb') as f:
                f.write(image_data)
            
            return image
            
        except Exception as e:
            logger.error(f"Failed to save generated image: {str(e)}")
            raise ValueError(f"Failed to save generated image: {str(e)}")
    
    def get_tool_suggestions(self, dataset: Dataset, user: User) -> List[Dict[str, Any]]:
        """Get suggested analysis tools for a dataset"""
        try:
            # Get dataset columns
            columns = dataset.columns.all()
            
            # Get available tools
            available_tools = AnalysisTool.objects.filter(is_active=True)
            
            suggestions = []
            
            for tool in available_tools:
                # Check if tool is compatible with dataset
                if self._is_tool_compatible(tool, columns):
                    suggestions.append({
                        'tool_id': tool.id,
                        'tool_name': tool.name,
                        'display_name': tool.display_name,
                        'description': tool.description,
                        'category': tool.category,
                        'confidence': self._calculate_tool_confidence(tool, columns)
                    })
            
            # Sort by confidence
            suggestions.sort(key=lambda x: x['confidence'], reverse=True)
            
            return suggestions[:10]  # Return top 10 suggestions
            
        except Exception as e:
            logger.error(f"Failed to get tool suggestions: {str(e)}")
            return []
    
    def _is_tool_compatible(self, tool: AnalysisTool, columns: List) -> bool:
        """Check if tool is compatible with dataset columns"""
        if not tool.required_column_types:
            return True
        
        column_types = [col.confirmed_type for col in columns]
        
        for required_type in tool.required_column_types:
            if not any(required_type in col_type for col_type in column_types):
                return False
        
        return True
    
    def _calculate_tool_confidence(self, tool: AnalysisTool, columns: List) -> float:
        """Calculate confidence score for tool compatibility"""
        if not tool.required_column_types:
            return 0.8
        
        column_types = [col.confirmed_type for col in columns]
        matches = 0
        
        for required_type in tool.required_column_types:
            if any(required_type in col_type for col_type in column_types):
                matches += 1
        
        return matches / len(tool.required_column_types)
    
    def _index_analysis_result_for_rag(self, analysis_result: AnalysisResult, 
                                      result_data: Dict[str, Any], user: User, 
                                      session: AnalysisSession) -> None:
        """
        Index analysis result for RAG (Retrieval-Augmented Generation) system
        
        Args:
            analysis_result: AnalysisResult model instance
            result_data: Result data from tool execution
            user: User who executed the analysis
            session: Analysis session
        """
        try:
            # Create analysis result vector note
            self._create_analysis_result_note(analysis_result, result_data, user, session)
            
            # Create insights vector note if applicable
            if result_data.get('output_type') in ['table', 'chart']:
                self._create_analysis_insights_note(analysis_result, result_data, user, session)
            
            logger.info(f"RAG indexing completed for analysis result {analysis_result.id}")
            
        except Exception as e:
            logger.error(f"RAG indexing failed for analysis result {analysis_result.id}: {str(e)}")
            # Don't raise exception - RAG indexing is not critical for analysis execution
    
    def _create_analysis_result_note(self, analysis_result: AnalysisResult, 
                                   result_data: Dict[str, Any], user: User, 
                                   session: AnalysisSession) -> None:
        """Create vector note for analysis result"""
        try:
            tool = analysis_result.tool
            dataset = session.primary_dataset
            
            result_text = f"""
            Analysis Result: {tool.display_name}
            Dataset: {dataset.name}
            Tool: {tool.name}
            Parameters: {analysis_result.parameters_used}
            Output Type: {result_data.get('output_type', 'unknown')}
            Execution Time: {analysis_result.execution_time_ms}ms
            Created: {analysis_result.created_at.strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            # Add result-specific content based on output type
            if result_data.get('output_type') == 'table':
                table_data = result_data.get('data', {})
                if isinstance(table_data, dict) and 'rows' in table_data:
                    result_text += f"\nTable Data: {len(table_data['rows'])} rows"
                    if 'columns' in table_data:
                        result_text += f", {len(table_data['columns'])} columns"
            
            elif result_data.get('output_type') == 'chart':
                chart_data = result_data.get('chart_data', {})
                if isinstance(chart_data, dict):
                    result_text += f"\nChart Type: {chart_data.get('type', 'unknown')}"
                    if 'title' in chart_data:
                        result_text += f"\nChart Title: {chart_data['title']}"
            
            elif result_data.get('output_type') == 'text':
                text_content = result_data.get('text', '')
                if text_content:
                    # Truncate long text for vector note
                    truncated_text = text_content[:500] + "..." if len(text_content) > 500 else text_content
                    result_text += f"\nResult Text: {truncated_text}"
            
            self.vector_note_manager.create_vector_note(
                title=f"Analysis Result: {tool.display_name}",
                text=result_text.strip(),
                scope='dataset',
                content_type='analysis_result',
                user=user,
                dataset=dataset,
                metadata={
                    'analysis_id': analysis_result.id,
                    'tool_name': tool.name,
                    'tool_display_name': tool.display_name,
                    'output_type': result_data.get('output_type'),
                    'execution_time_ms': analysis_result.execution_time_ms,
                    'parameters': analysis_result.parameters_used
                },
                confidence_score=0.9
            )
            
        except Exception as e:
            logger.error(f"Failed to create analysis result note: {str(e)}")
    
    def _create_analysis_insights_note(self, analysis_result: AnalysisResult, 
                                     result_data: Dict[str, Any], user: User, 
                                     session: AnalysisSession) -> None:
        """Create vector note for analysis insights"""
        try:
            tool = analysis_result.tool
            dataset = session.primary_dataset
            
            # Generate insights based on result type
            insights_text = f"""
            Analysis Insights: {tool.display_name}
            Dataset: {dataset.name}
            
            Key Findings:
            """
            
            if result_data.get('output_type') == 'table':
                table_data = result_data.get('data', {})
                if isinstance(table_data, dict):
                    insights_text += f"- Generated table with {len(table_data.get('rows', []))} rows"
                    if 'summary' in table_data:
                        insights_text += f"\n- Summary: {table_data['summary']}"
            
            elif result_data.get('output_type') == 'chart':
                chart_data = result_data.get('chart_data', {})
                if isinstance(chart_data, dict):
                    chart_type = chart_data.get('type', 'unknown')
                    insights_text += f"- Created {chart_type} visualization"
                    if 'insights' in chart_data:
                        insights_text += f"\n- Insights: {chart_data['insights']}"
            
            # Add tool-specific insights
            if tool.name == 'descriptive_statistics':
                insights_text += "\n- Descriptive statistics calculated for dataset columns"
            elif tool.name == 'correlation_analysis':
                insights_text += "\n- Correlation analysis performed between variables"
            elif tool.name == 'regression_analysis':
                insights_text += "\n- Regression analysis completed"
            elif 'visualization' in tool.name:
                insights_text += "\n- Data visualization generated"
            
            self.vector_note_manager.create_vector_note(
                title=f"Analysis Insights: {tool.display_name}",
                text=insights_text.strip(),
                scope='dataset',
                content_type='analysis_insights',
                user=user,
                dataset=dataset,
                metadata={
                    'analysis_id': analysis_result.id,
                    'tool_name': tool.name,
                    'insights_type': 'analysis_summary',
                    'output_type': result_data.get('output_type')
                },
                confidence_score=0.8
            )
            
        except Exception as e:
            logger.error(f"Failed to create analysis insights note: {str(e)}")
