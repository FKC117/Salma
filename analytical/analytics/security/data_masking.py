"""
Sensitive Data Masking Module

This module provides comprehensive data masking and anonymization capabilities
for protecting sensitive information including PII, financial data, healthcare data,
and other confidential information in compliance with GDPR, HIPAA, and other regulations.
"""

import re
import hashlib
import random
import string
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, date
import pandas as pd
import numpy as np
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class SensitiveDataMasker:
    """
    Comprehensive sensitive data masking and anonymization
    """
    
    # Common PII patterns
    PII_PATTERNS = {
        # Email addresses
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        
        # Phone numbers (various formats)
        'phone': r'(\+?1[-.\s]?)?(\(?[0-9]{3}\)?[-.\s]?)?[0-9]{3}[-.\s]?[0-9]{4}',
        
        # Social Security Numbers
        'ssn': r'\b\d{3}-?\d{2}-?\d{4}\b',
        
        # Credit card numbers
        'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
        
        # IP addresses
        'ip_address': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        
        # URLs
        'url': r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?',
        
        # Dates (various formats)
        'date': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
        
        # Addresses (simplified pattern)
        'address': r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Place|Pl)',
        
        # Bank account numbers
        'bank_account': r'\b\d{8,17}\b',
        
        # Medical record numbers
        'medical_record': r'\bMRN:?\s*\d{6,10}\b',
    }
    
    # Common sensitive field names (case-insensitive)
    SENSITIVE_FIELD_NAMES = [
        # Personal identifiers
        'ssn', 'social_security_number', 'social_security', 'sin',
        'passport', 'passport_number', 'drivers_license', 'license_number',
        'national_id', 'tax_id', 'employee_id', 'patient_id', 'medical_record_number',
        
        # Contact information
        'email', 'email_address', 'phone', 'phone_number', 'mobile', 'telephone',
        'address', 'street_address', 'home_address', 'mailing_address',
        'zip_code', 'postal_code', 'zipcode',
        
        # Financial information
        'credit_card', 'card_number', 'account_number', 'bank_account',
        'routing_number', 'iban', 'swift_code', 'salary', 'income', 'wage',
        
        # Authentication
        'password', 'passwd', 'pwd', 'secret', 'token', 'api_key', 'auth_token',
        
        # Healthcare
        'diagnosis', 'medical_condition', 'prescription', 'treatment',
        'insurance_number', 'policy_number',
        
        # Personal details
        'birth_date', 'date_of_birth', 'dob', 'age', 'gender', 'race', 'ethnicity',
        'marital_status', 'religion', 'nationality',
    ]
    
    # Masking strategies
    MASKING_STRATEGIES = {
        'partial': 'Show first and last characters, mask middle',
        'full': 'Replace entire value with mask characters',
        'hash': 'Replace with cryptographic hash',
        'fake': 'Replace with realistic fake data',
        'null': 'Replace with null/empty value',
        'redact': 'Replace with [REDACTED] placeholder',
        'format_preserving': 'Maintain format but change values',
    }
    
    def __init__(self):
        self.masking_enabled = getattr(settings, 'DATA_MASKING_ENABLED', True)
        self.default_strategy = getattr(settings, 'DATA_MASKING_DEFAULT_STRATEGY', 'partial')
        self.mask_character = getattr(settings, 'DATA_MASKING_CHARACTER', '*')
        self.preserve_length = getattr(settings, 'DATA_MASKING_PRESERVE_LENGTH', True)
        
        # Custom patterns from settings
        custom_patterns = getattr(settings, 'DATA_MASKING_CUSTOM_PATTERNS', {})
        self.patterns = {**self.PII_PATTERNS, **custom_patterns}
        
        # Custom sensitive fields from settings
        custom_fields = getattr(settings, 'DATA_MASKING_SENSITIVE_FIELDS', [])
        self.sensitive_fields = self.SENSITIVE_FIELD_NAMES + custom_fields
    
    def mask_dataframe(self, df: pd.DataFrame, strategy: str = None) -> pd.DataFrame:
        """
        Mask sensitive data in a pandas DataFrame
        
        Args:
            df: Input DataFrame
            strategy: Masking strategy to use
            
        Returns:
            DataFrame with masked sensitive data
        """
        if not self.masking_enabled:
            return df
        
        strategy = strategy or self.default_strategy
        masked_df = df.copy()
        
        # Detect and mask sensitive columns
        for column in masked_df.columns:
            if self._is_sensitive_field(column):
                logger.info(f"Masking sensitive column: {column}")
                masked_df[column] = self._mask_series(masked_df[column], strategy, column)
            else:
                # Check for PII patterns in data
                if masked_df[column].dtype == 'object':  # String columns
                    sample_data = masked_df[column].dropna().astype(str).head(100).str.cat(sep=' ')
                    detected_patterns = self._detect_pii_patterns(sample_data)
                    
                    if detected_patterns:
                        logger.info(f"Detected PII patterns in column {column}: {detected_patterns}")
                        masked_df[column] = self._mask_series(masked_df[column], strategy, column)
        
        return masked_df
    
    def mask_dictionary(self, data: Dict[str, Any], strategy: str = None) -> Dict[str, Any]:
        """
        Mask sensitive data in a dictionary
        
        Args:
            data: Input dictionary
            strategy: Masking strategy to use
            
        Returns:
            Dictionary with masked sensitive data
        """
        if not self.masking_enabled:
            return data
        
        strategy = strategy or self.default_strategy
        masked_data = {}
        
        for key, value in data.items():
            if self._is_sensitive_field(key):
                masked_data[key] = self._mask_value(value, strategy, key)
            elif isinstance(value, dict):
                masked_data[key] = self.mask_dictionary(value, strategy)
            elif isinstance(value, list):
                masked_data[key] = [
                    self.mask_dictionary(item, strategy) if isinstance(item, dict) 
                    else self._mask_value(item, strategy, key) if self._is_sensitive_field(key)
                    else item
                    for item in value
                ]
            elif isinstance(value, str):
                # Check for PII patterns in string values
                detected_patterns = self._detect_pii_patterns(value)
                if detected_patterns:
                    masked_data[key] = self._mask_string_patterns(value, detected_patterns, strategy)
                else:
                    masked_data[key] = value
            else:
                masked_data[key] = value
        
        return masked_data
    
    def mask_string(self, text: str, strategy: str = None) -> str:
        """
        Mask sensitive data in a string
        
        Args:
            text: Input string
            strategy: Masking strategy to use
            
        Returns:
            String with masked sensitive data
        """
        if not self.masking_enabled or not text:
            return text
        
        strategy = strategy or self.default_strategy
        detected_patterns = self._detect_pii_patterns(text)
        
        if detected_patterns:
            return self._mask_string_patterns(text, detected_patterns, strategy)
        
        return text
    
    def _is_sensitive_field(self, field_name: str) -> bool:
        """Check if field name indicates sensitive data"""
        field_lower = field_name.lower()
        return any(sensitive in field_lower for sensitive in self.sensitive_fields)
    
    def _detect_pii_patterns(self, text: str) -> List[str]:
        """Detect PII patterns in text"""
        detected = []
        
        for pattern_name, pattern in self.patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                detected.append(pattern_name)
        
        return detected
    
    def _mask_series(self, series: pd.Series, strategy: str, field_name: str) -> pd.Series:
        """Mask a pandas Series"""
        return series.apply(lambda x: self._mask_value(x, strategy, field_name))
    
    def _mask_value(self, value: Any, strategy: str, field_name: str = '') -> Any:
        """Mask a single value based on strategy"""
        if pd.isna(value) or value is None:
            return value
        
        value_str = str(value)
        
        if strategy == 'partial':
            return self._partial_mask(value_str)
        elif strategy == 'full':
            return self._full_mask(value_str)
        elif strategy == 'hash':
            return self._hash_mask(value_str)
        elif strategy == 'fake':
            return self._fake_mask(value_str, field_name)
        elif strategy == 'null':
            return None
        elif strategy == 'redact':
            return '[REDACTED]'
        elif strategy == 'format_preserving':
            return self._format_preserving_mask(value_str, field_name)
        else:
            return self._partial_mask(value_str)
    
    def _mask_string_patterns(self, text: str, patterns: List[str], strategy: str) -> str:
        """Mask detected PII patterns in string"""
        masked_text = text
        
        for pattern_name in patterns:
            if pattern_name in self.patterns:
                pattern = self.patterns[pattern_name]
                matches = re.finditer(pattern, masked_text, re.IGNORECASE)
                
                for match in reversed(list(matches)):  # Reverse to maintain indices
                    original = match.group()
                    masked = self._mask_value(original, strategy, pattern_name)
                    masked_text = masked_text[:match.start()] + str(masked) + masked_text[match.end():]
        
        return masked_text
    
    def _partial_mask(self, value: str) -> str:
        """Partial masking - show first and last characters"""
        if len(value) <= 2:
            return self.mask_character * len(value)
        elif len(value) <= 4:
            return value[0] + self.mask_character * (len(value) - 2) + value[-1]
        else:
            visible_chars = max(2, len(value) // 4)
            middle_length = len(value) - (2 * visible_chars)
            return value[:visible_chars] + self.mask_character * middle_length + value[-visible_chars:]
    
    def _full_mask(self, value: str) -> str:
        """Full masking - replace entire value"""
        if self.preserve_length:
            return self.mask_character * len(value)
        else:
            return self.mask_character * 8  # Fixed length
    
    def _hash_mask(self, value: str) -> str:
        """Hash masking - replace with hash"""
        return hashlib.sha256(value.encode()).hexdigest()[:16]
    
    def _fake_mask(self, value: str, field_name: str) -> str:
        """Generate fake data based on field type"""
        field_lower = field_name.lower()
        
        if 'email' in field_lower:
            return f"user{random.randint(1000, 9999)}@example.com"
        elif 'phone' in field_lower:
            return f"({random.randint(100, 999)}) {random.randint(100, 999)}-{random.randint(1000, 9999)}"
        elif 'ssn' in field_lower:
            return f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"
        elif 'address' in field_lower:
            return f"{random.randint(100, 9999)} Main Street"
        elif 'name' in field_lower:
            first_names = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Lisa']
            last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia']
            return f"{random.choice(first_names)} {random.choice(last_names)}"
        else:
            # Generate random string of similar length
            length = min(len(value), 12)
            return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def _format_preserving_mask(self, value: str, field_name: str) -> str:
        """Format-preserving masking"""
        field_lower = field_name.lower()
        
        if 'phone' in field_lower:
            # Preserve phone format
            digits_only = re.sub(r'\D', '', value)
            if len(digits_only) >= 10:
                return re.sub(r'\d', lambda m: str(random.randint(0, 9)), value)
        
        elif 'ssn' in field_lower:
            # Preserve SSN format
            return re.sub(r'\d', lambda m: str(random.randint(0, 9)), value)
        
        elif 'credit_card' in field_lower:
            # Preserve credit card format
            return re.sub(r'\d', lambda m: str(random.randint(0, 9)), value)
        
        elif 'date' in field_lower:
            # Keep date format but change values
            if re.match(r'\d{4}-\d{2}-\d{2}', value):
                return f"{random.randint(1980, 2020)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        
        # Default: preserve structure but mask characters
        result = ""
        for char in value:
            if char.isalpha():
                result += random.choice(string.ascii_letters)
            elif char.isdigit():
                result += str(random.randint(0, 9))
            else:
                result += char
        
        return result
    
    def get_masking_report(self, original_data: Any, masked_data: Any) -> Dict[str, Any]:
        """Generate a report of masking operations"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'masking_enabled': self.masking_enabled,
            'strategy_used': self.default_strategy,
            'fields_masked': [],
            'patterns_detected': [],
            'statistics': {}
        }
        
        if isinstance(original_data, pd.DataFrame):
            # DataFrame masking report
            for column in original_data.columns:
                if not original_data[column].equals(masked_data[column]):
                    report['fields_masked'].append(column)
            
            report['statistics'] = {
                'total_columns': len(original_data.columns),
                'masked_columns': len(report['fields_masked']),
                'total_rows': len(original_data),
                'masking_percentage': (len(report['fields_masked']) / len(original_data.columns)) * 100
            }
        
        elif isinstance(original_data, dict):
            # Dictionary masking report
            def compare_dicts(orig, masked, path=""):
                for key in orig.keys():
                    current_path = f"{path}.{key}" if path else key
                    if key in masked and orig[key] != masked[key]:
                        report['fields_masked'].append(current_path)
                    elif isinstance(orig[key], dict) and isinstance(masked.get(key), dict):
                        compare_dicts(orig[key], masked[key], current_path)
            
            compare_dicts(original_data, masked_data)
            
            report['statistics'] = {
                'total_fields': len(str(original_data).split(':')),
                'masked_fields': len(report['fields_masked']),
            }
        
        return report
    
    def validate_masking_compliance(self, data: Any) -> Dict[str, Any]:
        """Validate that data masking meets compliance requirements"""
        compliance_report = {
            'compliant': True,
            'violations': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Check for remaining PII patterns
        data_str = str(data)
        
        for pattern_name, pattern in self.patterns.items():
            matches = re.findall(pattern, data_str, re.IGNORECASE)
            if matches:
                compliance_report['compliant'] = False
                compliance_report['violations'].append({
                    'type': 'pii_detected',
                    'pattern': pattern_name,
                    'matches': len(matches),
                    'examples': matches[:3]  # Show first 3 examples
                })
        
        # Check for sensitive field names
        if isinstance(data, (dict, pd.DataFrame)):
            fields = data.keys() if isinstance(data, dict) else data.columns
            
            for field in fields:
                if self._is_sensitive_field(field):
                    compliance_report['warnings'].append({
                        'type': 'sensitive_field_name',
                        'field': field,
                        'recommendation': 'Consider renaming or masking this field'
                    })
        
        return compliance_report


# Convenience functions
def mask_dataframe(df: pd.DataFrame, strategy: str = 'partial') -> pd.DataFrame:
    """
    Convenience function to mask a DataFrame
    
    Args:
        df: Input DataFrame
        strategy: Masking strategy
        
    Returns:
        Masked DataFrame
    """
    masker = SensitiveDataMasker()
    return masker.mask_dataframe(df, strategy)


def mask_dictionary(data: Dict[str, Any], strategy: str = 'partial') -> Dict[str, Any]:
    """
    Convenience function to mask a dictionary
    
    Args:
        data: Input dictionary
        strategy: Masking strategy
        
    Returns:
        Masked dictionary
    """
    masker = SensitiveDataMasker()
    return masker.mask_dictionary(data, strategy)


def mask_string(text: str, strategy: str = 'partial') -> str:
    """
    Convenience function to mask a string
    
    Args:
        text: Input string
        strategy: Masking strategy
        
    Returns:
        Masked string
    """
    masker = SensitiveDataMasker()
    return masker.mask_string(text, strategy)


def detect_sensitive_data(data: Any) -> Dict[str, Any]:
    """
    Detect sensitive data in various data types
    
    Args:
        data: Data to analyze
        
    Returns:
        Detection report
    """
    masker = SensitiveDataMasker()
    
    if isinstance(data, pd.DataFrame):
        sensitive_columns = []
        for column in data.columns:
            if masker._is_sensitive_field(column):
                sensitive_columns.append(column)
        
        return {
            'type': 'dataframe',
            'sensitive_columns': sensitive_columns,
            'total_columns': len(data.columns),
            'risk_level': 'high' if sensitive_columns else 'low'
        }
    
    elif isinstance(data, dict):
        sensitive_fields = []
        for key in data.keys():
            if masker._is_sensitive_field(key):
                sensitive_fields.append(key)
        
        return {
            'type': 'dictionary',
            'sensitive_fields': sensitive_fields,
            'total_fields': len(data),
            'risk_level': 'high' if sensitive_fields else 'low'
        }
    
    elif isinstance(data, str):
        detected_patterns = masker._detect_pii_patterns(data)
        
        return {
            'type': 'string',
            'detected_patterns': detected_patterns,
            'risk_level': 'high' if detected_patterns else 'low'
        }
    
    else:
        return {
            'type': 'unknown',
            'risk_level': 'low'
        }
