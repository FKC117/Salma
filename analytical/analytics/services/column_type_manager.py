"""
Column Type Manager for Automatic Categorization

This service automatically detects and categorizes column types in datasets,
providing intelligent type detection with confidence scoring and statistics calculation.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime, date
import re
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)


class ColumnTypeManager:
    """
    Service for automatic column type detection and categorization
    """
    
    def __init__(self):
        self.type_hierarchy = {
            'numeric': ['integer', 'float', 'decimal'],
            'datetime': ['date', 'datetime', 'time', 'timestamp'],
            'categorical': ['category', 'boolean', 'ordinal'],
            'text': ['string', 'text', 'url', 'email'],
            'identifier': ['id', 'uuid', 'key']
        }
        
        # Type detection patterns
        self.patterns = {
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'url': r'^https?://[^\s/$.?#].[^\s]*$',
            'phone': r'^[\+]?[1-9][\d]{0,15}$',
            'uuid': r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            'credit_card': r'^\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}$',
            'ssn': r'^\d{3}-?\d{2}-?\d{4}$',
            'zip_code': r'^\d{5}(-\d{4})?$',
            'ip_address': r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        }
        
        # Date/time formats to try
        self.date_formats = [
            '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S',
            '%m/%d/%Y %H:%M:%S', '%d/%m/%Y %H:%M:%S', '%Y-%m-%d %H:%M',
            '%m/%d/%Y %H:%M', '%d/%m/%Y %H:%M', '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S.%fZ'
        ]
    
    def detect_column_type(self, column_data: pd.Series) -> str:
        """
        Detect the most appropriate type for a column
        
        Args:
            column_data: Pandas Series containing the column data
            
        Returns:
            String representing the detected column type
        """
        if column_data.empty:
            return 'unknown'
        
        # Remove null values for analysis
        non_null_data = column_data.dropna()
        if len(non_null_data) == 0:
            return 'unknown'
        
        # Calculate type scores
        type_scores = self._calculate_type_scores(non_null_data)
        
        # Return the type with highest score
        best_type = max(type_scores.items(), key=lambda x: x[1])
        return best_type[0] if best_type[1] > 0.5 else 'string'
    
    def _calculate_type_scores(self, data: pd.Series) -> Dict[str, float]:
        """Calculate confidence scores for different type categories"""
        scores = {}
        
        # Check each type category
        for category, types in self.type_hierarchy.items():
            category_score = 0
            for type_name in types:
                # Remove the call to non-existent method
                type_score = 0.0  # Default score
                category_score = max(category_score, type_score)
            scores[category] = category_score
        
        # Add specific type scores
        scores.update({
            'integer': self._calculate_integer_score(data),
            'float': self._calculate_float_score(data),
            'decimal': self._calculate_decimal_score(data),
            'date': self._calculate_date_score(data),
            'datetime': self._calculate_datetime_score(data),
            'time': self._calculate_time_score(data),
            'boolean': self._calculate_boolean_score(data),
            'category': self._calculate_category_score(data),
            'email': self._calculate_pattern_score(data, 'email'),
            'url': self._calculate_pattern_score(data, 'url'),
            'phone': self._calculate_pattern_score(data, 'phone'),
            'uuid': self._calculate_pattern_score(data, 'uuid'),
            'id': self._calculate_id_score(data),
            'string': self._calculate_string_score(data)
        })
        
        return scores
    
    def _calculate_integer_score(self, data: pd.Series) -> float:
        """Calculate confidence score for integer type"""
        try:
            # Try to convert to numeric
            numeric_data = pd.to_numeric(data, errors='coerce')
            non_null_numeric = numeric_data.dropna()
            
            if len(non_null_numeric) == 0:
                return 0.0
            
            # Check if all values are integers
            is_integer = (non_null_numeric % 1 == 0).all()
            completeness = len(non_null_numeric) / len(data)
            
            if is_integer and completeness > 0.8:
                return 0.9
            elif is_integer and completeness > 0.5:
                return 0.7
            else:
                return 0.3
                
        except Exception:
            return 0.0
    
    def _calculate_float_score(self, data: pd.Series) -> float:
        """Calculate confidence score for float type"""
        try:
            numeric_data = pd.to_numeric(data, errors='coerce')
            non_null_numeric = numeric_data.dropna()
            
            if len(non_null_numeric) == 0:
                return 0.0
            
            completeness = len(non_null_numeric) / len(data)
            
            if completeness > 0.8:
                return 0.8
            elif completeness > 0.5:
                return 0.6
            else:
                return 0.2
                
        except Exception:
            return 0.0
    
    def _calculate_decimal_score(self, data: pd.Series) -> float:
        """Calculate confidence score for decimal type"""
        try:
            # Check for decimal-like strings
            decimal_count = 0
            for value in data.astype(str):
                try:
                    Decimal(str(value))
                    decimal_count += 1
                except (InvalidOperation, ValueError):
                    continue
            
            completeness = decimal_count / len(data)
            
            if completeness > 0.8:
                return 0.85
            elif completeness > 0.5:
                return 0.65
            else:
                return 0.2
                
        except Exception:
            return 0.0
    
    def _calculate_date_score(self, data: pd.Series) -> float:
        """Calculate confidence score for date type"""
        try:
            date_count = 0
            for value in data.astype(str):
                if self._is_date_like(value):
                    date_count += 1
            
            completeness = date_count / len(data)
            
            if completeness > 0.8:
                return 0.9
            elif completeness > 0.5:
                return 0.7
            else:
                return 0.3
                
        except Exception:
            return 0.0
    
    def _calculate_datetime_score(self, data: pd.Series) -> float:
        """Calculate confidence score for datetime type"""
        try:
            datetime_count = 0
            for value in data.astype(str):
                if self._is_datetime_like(value):
                    datetime_count += 1
            
            completeness = datetime_count / len(data)
            
            if completeness > 0.8:
                return 0.9
            elif completeness > 0.5:
                return 0.7
            else:
                return 0.3
                
        except Exception:
            return 0.0
    
    def _calculate_time_score(self, data: pd.Series) -> float:
        """Calculate confidence score for time type"""
        try:
            time_count = 0
            for value in data.astype(str):
                if self._is_time_like(value):
                    time_count += 1
            
            completeness = time_count / len(data)
            
            if completeness > 0.8:
                return 0.8
            elif completeness > 0.5:
                return 0.6
            else:
                return 0.2
                
        except Exception:
            return 0.0
    
    def _calculate_boolean_score(self, data: pd.Series) -> float:
        """Calculate confidence score for boolean type"""
        try:
            # Check for common boolean representations
            boolean_values = {
                'true', 'false', 'yes', 'no', 'y', 'n', '1', '0',
                't', 'f', 'on', 'off', 'enabled', 'disabled'
            }
            
            boolean_count = 0
            for value in data.astype(str).str.lower():
                if value in boolean_values:
                    boolean_count += 1
            
            completeness = boolean_count / len(data)
            
            if completeness > 0.9:
                return 0.95
            elif completeness > 0.7:
                return 0.8
            elif completeness > 0.5:
                return 0.6
            else:
                return 0.2
                
        except Exception:
            return 0.0
    
    def _calculate_category_score(self, data: pd.Series) -> float:
        """Calculate confidence score for categorical type"""
        try:
            unique_count = data.nunique()
            total_count = len(data)
            uniqueness_ratio = unique_count / total_count
            
            # Categorical if low uniqueness and reasonable number of unique values
            if 0.01 <= uniqueness_ratio <= 0.5 and unique_count <= 100:
                return 0.8
            elif 0.01 <= uniqueness_ratio <= 0.7 and unique_count <= 1000:
                return 0.6
            else:
                return 0.2
                
        except Exception:
            return 0.0
    
    def _calculate_pattern_score(self, data: pd.Series, pattern_name: str) -> float:
        """Calculate confidence score for pattern-based types"""
        try:
            pattern = self.patterns.get(pattern_name)
            if not pattern:
                return 0.0
            
            matches = data.astype(str).str.match(pattern, case=False).sum()
            completeness = matches / len(data)
            
            if completeness > 0.8:
                return 0.9
            elif completeness > 0.5:
                return 0.7
            else:
                return 0.2
                
        except Exception:
            return 0.0
    
    def _calculate_id_score(self, data: pd.Series) -> float:
        """Calculate confidence score for ID type"""
        try:
            # Check if column name suggests ID
            column_name = data.name.lower() if hasattr(data, 'name') else ''
            id_indicators = ['id', 'key', 'pk', 'identifier', 'code']
            
            name_score = 0.5 if any(indicator in column_name for indicator in id_indicators) else 0.0
            
            # Check for uniqueness
            uniqueness_ratio = data.nunique() / len(data)
            uniqueness_score = 0.5 if uniqueness_ratio > 0.95 else 0.0
            
            # Check for sequential or UUID-like patterns
            pattern_score = 0.0
            if data.dtype == 'object':
                # Check for UUID pattern
                uuid_matches = data.astype(str).str.match(self.patterns['uuid'], case=False).sum()
                if uuid_matches > 0:
                    pattern_score = 0.3
                # Check for sequential numbers
                elif pd.to_numeric(data, errors='coerce').notna().all():
                    pattern_score = 0.2
            
            total_score = name_score + uniqueness_score + pattern_score
            return min(total_score, 1.0)
            
        except Exception:
            return 0.0
    
    def _calculate_string_score(self, data: pd.Series) -> float:
        """Calculate confidence score for string type (fallback)"""
        try:
            # String is the fallback type, so it gets a base score
            non_null_count = data.notna().sum()
            completeness = non_null_count / len(data)
            
            # Lower score if other types are more likely
            return max(0.1, 0.5 * completeness)
            
        except Exception:
            return 0.1
    
    def _is_date_like(self, value: str) -> bool:
        """Check if value looks like a date"""
        for fmt in self.date_formats:
            try:
                datetime.strptime(value, fmt)
                return True
            except ValueError:
                continue
        return False
    
    def _is_datetime_like(self, value: str) -> bool:
        """Check if value looks like a datetime"""
        # Check for datetime patterns
        datetime_patterns = [
            r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}',
            r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}',
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
        ]
        
        for pattern in datetime_patterns:
            if re.match(pattern, value):
                return True
        
        return self._is_date_like(value)
    
    def _is_time_like(self, value: str) -> bool:
        """Check if value looks like a time"""
        time_patterns = [
            r'^\d{1,2}:\d{2}(:\d{2})?$',
            r'^\d{1,2}:\d{2}(:\d{2})?\s*[AP]M$'
        ]
        
        for pattern in time_patterns:
            if re.match(pattern, value, re.IGNORECASE):
                return True
        
        return False
    
    def calculate_confidence_score(self, data: pd.Series, detected_type: str) -> float:
        """Calculate confidence score for detected type"""
        type_scores = self._calculate_type_scores(data)
        return type_scores.get(detected_type, 0.0)
    
    def calculate_statistics(self, data: pd.Series, column_type: str) -> Dict[str, Any]:
        """Calculate comprehensive statistics for a column based on its type"""
        stats = {}
        
        try:
            if column_type in ['integer', 'float', 'decimal']:
                stats.update(self._calculate_numeric_statistics(data))
            elif column_type in ['date', 'datetime', 'time']:
                stats.update(self._calculate_datetime_statistics(data))
            elif column_type == 'boolean':
                stats.update(self._calculate_boolean_statistics(data))
            elif column_type == 'category':
                stats.update(self._calculate_categorical_statistics(data))
            else:
                stats.update(self._calculate_text_statistics(data))
                
        except Exception as e:
            logger.warning(f"Error calculating statistics for column {data.name}: {str(e)}")
        
        return stats
    
    def _calculate_numeric_statistics(self, data: pd.Series) -> Dict[str, Any]:
        """Calculate statistics for numeric columns"""
        numeric_data = pd.to_numeric(data, errors='coerce').dropna()
        
        if len(numeric_data) == 0:
            return {}
        
        stats = {
            'min_value': float(numeric_data.min()),
            'max_value': float(numeric_data.max()),
            'mean_value': float(numeric_data.mean()),
            'median_value': float(numeric_data.median()),
            'std_deviation': float(numeric_data.std()),
            'has_outliers': self._detect_outliers(numeric_data),
            'has_duplicates': numeric_data.duplicated().any()
        }
        
        # Add quartiles
        quartiles = numeric_data.quantile([0.25, 0.5, 0.75])
        stats.update({
            'q1': float(quartiles[0.25]),
            'q2': float(quartiles[0.5]),
            'q3': float(quartiles[0.75])
        })
        
        return stats
    
    def _calculate_datetime_statistics(self, data: pd.Series) -> Dict[str, Any]:
        """Calculate statistics for datetime columns"""
        # Try to convert to datetime
        datetime_data = pd.to_datetime(data, errors='coerce').dropna()
        
        if len(datetime_data) == 0:
            return {}
        
        stats = {
            'min_value': datetime_data.min().isoformat(),
            'max_value': datetime_data.max().isoformat(),
            'has_duplicates': datetime_data.duplicated().any()
        }
        
        # Calculate time range
        time_range = datetime_data.max() - datetime_data.min()
        stats['time_range_days'] = time_range.days
        
        return stats
    
    def _calculate_boolean_statistics(self, data: pd.Series) -> Dict[str, Any]:
        """Calculate statistics for boolean columns"""
        # Convert to boolean
        boolean_data = self._convert_to_boolean(data)
        
        if len(boolean_data) == 0:
            return {}
        
        true_count = boolean_data.sum()
        false_count = len(boolean_data) - true_count
        
        stats = {
            'true_count': int(true_count),
            'false_count': int(false_count),
            'true_percentage': float(true_count / len(boolean_data) * 100),
            'false_percentage': float(false_count / len(boolean_data) * 100)
        }
        
        return stats
    
    def _calculate_categorical_statistics(self, data: pd.Series) -> Dict[str, Any]:
        """Calculate statistics for categorical columns"""
        value_counts = data.value_counts()
        top_values = value_counts.head(10).to_dict()
        
        stats = {
            'top_values': top_values,
            'value_counts': value_counts.to_dict(),
            'has_duplicates': data.duplicated().any()
        }
        
        return stats
    
    def _calculate_text_statistics(self, data: pd.Series) -> Dict[str, Any]:
        """Calculate statistics for text columns"""
        text_data = data.astype(str).dropna()
        
        if len(text_data) == 0:
            return {}
        
        # Calculate text length statistics
        lengths = text_data.str.len()
        
        stats = {
            'min_length': int(lengths.min()),
            'max_length': int(lengths.max()),
            'mean_length': float(lengths.mean()),
            'median_length': float(lengths.median()),
            'has_duplicates': text_data.duplicated().any()
        }
        
        return stats
    
    def _detect_outliers(self, data: pd.Series) -> bool:
        """Detect if column has outliers using IQR method"""
        try:
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = (data < lower_bound) | (data > upper_bound)
            return outliers.any()
            
        except Exception:
            return False
    
    def _convert_to_boolean(self, data: pd.Series) -> pd.Series:
        """Convert data to boolean values"""
        boolean_mapping = {
            'true': True, 'false': False, 'yes': True, 'no': False,
            'y': True, 'n': False, '1': True, '0': False,
            't': True, 'f': False, 'on': True, 'off': False,
            'enabled': True, 'disabled': False
        }
        
        return data.astype(str).str.lower().map(boolean_mapping)
    
    def suggest_analysis_tools(self, column_type: str, column_stats: Dict[str, Any]) -> List[str]:
        """Suggest appropriate analysis tools for a column type"""
        suggestions = []
        
        if column_type in ['integer', 'float', 'decimal']:
            suggestions.extend([
                'descriptive_statistics', 'correlation_analysis', 'regression_analysis',
                'outlier_detection', 'distribution_analysis', 'hypothesis_testing'
            ])
        elif column_type in ['date', 'datetime', 'time']:
            suggestions.extend([
                'time_series_analysis', 'seasonality_analysis', 'trend_analysis',
                'date_range_analysis', 'frequency_analysis'
            ])
        elif column_type == 'boolean':
            suggestions.extend([
                'frequency_analysis', 'proportion_analysis', 'chi_square_test'
            ])
        elif column_type == 'category':
            suggestions.extend([
                'frequency_analysis', 'crosstab_analysis', 'chi_square_test',
                'contingency_table', 'mode_analysis'
            ])
        else:
            suggestions.extend([
                'text_analysis', 'word_frequency', 'sentiment_analysis',
                'pattern_matching', 'length_analysis'
            ])
        
        return suggestions
    
    def get_column_metadata(self, data: pd.Series, column_type: str) -> Dict[str, Any]:
        """Get comprehensive metadata for a column"""
        metadata = {
            'detected_type': column_type,
            'confidence_score': self.calculate_confidence_score(data, column_type),
            'statistics': self.calculate_statistics(data, column_type),
            'suggested_tools': self.suggest_analysis_tools(column_type, {}),
            'data_quality': self._assess_data_quality(data),
            'completeness': float(data.notna().sum() / len(data) * 100),
            'uniqueness': float(data.nunique() / len(data) * 100)
        }
        
        return metadata
    
    def _assess_data_quality(self, data: pd.Series) -> Dict[str, Any]:
        """Assess data quality metrics for a column"""
        total_count = len(data)
        null_count = data.isnull().sum()
        unique_count = data.nunique()
        
        return {
            'completeness_score': float((total_count - null_count) / total_count * 100),
            'uniqueness_score': float(unique_count / total_count * 100),
            'consistency_score': self._calculate_consistency_score(data),
            'overall_quality': self._calculate_overall_quality_score(data)
        }
    
    def _calculate_consistency_score(self, data: pd.Series) -> float:
        """Calculate consistency score for data"""
        try:
            if data.dtype == 'object':
                # Check for consistent formatting
                non_null_data = data.dropna()
                if len(non_null_data) == 0:
                    return 100.0
                
                # Check for consistent string length patterns
                lengths = non_null_data.astype(str).str.len()
                length_std = lengths.std()
                length_mean = lengths.mean()
                
                if length_mean > 0:
                    cv = length_std / length_mean
                    consistency = max(0, 100 - cv * 100)
                else:
                    consistency = 100.0
            else:
                consistency = 100.0
            
            return float(consistency)
            
        except Exception:
            return 50.0
    
    def _calculate_overall_quality_score(self, data: pd.Series) -> float:
        """Calculate overall data quality score"""
        try:
            completeness = float(data.notna().sum() / len(data) * 100)
            consistency = self._calculate_consistency_score(data)
            
            # Weighted average
            overall_score = (completeness * 0.6 + consistency * 0.4)
            return float(overall_score)
            
        except Exception:
            return 0.0
