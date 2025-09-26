"""
File Processing Service with Security Sanitization

This service handles secure file upload, processing, and conversion to Parquet format.
It includes comprehensive security sanitization to remove formulas, macros, and malicious content.
"""

import os
import hashlib
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone
from django.db import transaction
import bleach
import openpyxl
import json
import re

from analytical.analytics.models import Dataset, DatasetColumn, User, AuditTrail
from analytics.services.audit_trail_manager import AuditTrailManager
from analytics.services.vector_note_manager import VectorNoteManager

logger = logging.getLogger(__name__)


class FileProcessingService:
    """
    Service for secure file processing and Parquet conversion
    """
    
    def __init__(self):
        self.audit_manager = AuditTrailManager()
        self.vector_note_manager = VectorNoteManager()
        self.supported_formats = ['.csv', '.xlsx', '.xls', '.json']
        self.max_file_size = settings.FILE_UPLOAD_MAX_MEMORY_SIZE
        self.media_root = Path(settings.MEDIA_ROOT)
        self.datasets_dir = self.media_root / 'datasets'
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
        
        # Security settings
        self.allowed_tags = ['table', 'tr', 'td', 'th', 'thead', 'tbody', 'tfoot']
        self.allowed_attributes = {
            'table': ['class', 'id'],
            'tr': ['class', 'id'],
            'td': ['class', 'id', 'colspan', 'rowspan'],
            'th': ['class', 'id', 'colspan', 'rowspan'],
            'thead': ['class', 'id'],
            'tbody': ['class', 'id'],
            'tfoot': ['class', 'id']
        }
    
    def process_file(self, uploaded_file: UploadedFile, user: User, 
                    dataset_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Process uploaded file with comprehensive security sanitization
        
        Args:
            uploaded_file: Django UploadedFile object
            user: User who uploaded the file
            dataset_name: Optional custom name for the dataset
            
        Returns:
            Dict containing processing results and metadata
        """
        correlation_id = f"file_process_{int(timezone.now().timestamp())}"
        
        try:
            # Security validation
            self._validate_file_security(uploaded_file)
            
            # File size validation
            if uploaded_file.size > self.max_file_size:
                raise ValueError(f"File size {uploaded_file.size} exceeds maximum allowed size {self.max_file_size}")
            
            # Generate file hash for deduplication
            file_hash = self._calculate_file_hash(uploaded_file)
            
            # Check for existing dataset with same hash
            existing_dataset = Dataset.objects.filter(file_hash=file_hash, user=user).first()
            if existing_dataset:
                logger.info(f"File with hash {file_hash} already exists for user {user.id}")
                return {
                    'dataset_id': existing_dataset.id,
                    'file_path': existing_dataset.parquet_path,
                    'columns_info': self._get_columns_info(existing_dataset),
                    'row_count': existing_dataset.row_count,
                    'file_size': existing_dataset.file_size_bytes,
                    'is_duplicate': True
                }
            
            # Process file based on format
            file_extension = Path(uploaded_file.name).suffix.lower()
            
            if file_extension == '.csv':
                df = self._process_csv(uploaded_file)
            elif file_extension in ['.xlsx', '.xls']:
                df = self._process_excel(uploaded_file)
            elif file_extension == '.json':
                df = self._process_json(uploaded_file)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
            
            # Security sanitization
            df = self._sanitize_dataframe(df)
            
            # Generate Parquet file
            parquet_path = self._convert_to_parquet(df, file_hash, user.id)
            
            # Create dataset record
            with transaction.atomic():
                dataset = self._create_dataset_record(
                    uploaded_file, user, df, parquet_path, file_hash, dataset_name
                )
                
                # Create column records
                self._create_column_records(dataset, df)
                
                # Log audit trail
                self.audit_manager.log_action(
                    user_id=user.id,
                    action_type='upload',
                    action_category='data_management',
                    resource_type='dataset',
                    resource_id=dataset.id,
                    resource_name=uploaded_file.name,
                    action_description='File uploaded and processed successfully',
                    success=True,
                    correlation_id=correlation_id,
                    data_changed=True
                )
            
            logger.info(f"File processed successfully: {uploaded_file.name} -> {parquet_path}")
            
            # RAG Indexing: Create vector notes for the dataset
            self._index_dataset_for_rag(dataset, df, user)
            
            return {
                'dataset_id': dataset.id,
                'file_path': parquet_path,
                'columns_info': self._get_columns_info(dataset),
                'row_count': len(df),
                'file_size': uploaded_file.size,
                'is_duplicate': False
            }
            
        except Exception as e:
            logger.error(f"File processing failed: {str(e)}", exc_info=True)
            
            # Log audit trail for failure
            self.audit_manager.log_action(
                user_id=user.id,
                action_type='upload',
                action_category='data_management',
                resource_type='dataset',
                resource_name=uploaded_file.name,
                action_description=f'File upload failed: {str(e)}',
                success=False,
                error_message=str(e),
                correlation_id=correlation_id
            )
            
            raise
    
    def _validate_file_security(self, uploaded_file: UploadedFile) -> None:
        """Validate file for security threats"""
        file_extension = Path(uploaded_file.name).suffix.lower()
        
        if file_extension not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_extension}")
        
        # Check for suspicious file names
        suspicious_patterns = [
            r'\.exe$', r'\.bat$', r'\.cmd$', r'\.scr$', r'\.pif$',
            r'\.com$', r'\.vbs$', r'\.js$', r'\.jar$', r'\.php$'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, uploaded_file.name, re.IGNORECASE):
                raise ValueError(f"Suspicious file type detected: {uploaded_file.name}")
        
        # Check file content for malicious patterns
        uploaded_file.seek(0)
        content_sample = uploaded_file.read(1024)  # Read first 1KB
        uploaded_file.seek(0)  # Reset position
        
        malicious_patterns = [
            b'<script', b'javascript:', b'vbscript:', b'onload=',
            b'onerror=', b'eval(', b'exec(', b'system('
        ]
        
        for pattern in malicious_patterns:
            if pattern in content_sample.lower():
                raise ValueError(f"Potentially malicious content detected in file")
    
    def _calculate_file_hash(self, uploaded_file: UploadedFile) -> str:
        """Calculate SHA-256 hash of uploaded file"""
        uploaded_file.seek(0)
        hasher = hashlib.sha256()
        
        # Read file in chunks to handle large files
        for chunk in iter(lambda: uploaded_file.read(4096), b""):
            hasher.update(chunk)
        
        uploaded_file.seek(0)  # Reset position
        return hasher.hexdigest()
    
    def _process_csv(self, uploaded_file: UploadedFile) -> pd.DataFrame:
        """Process CSV file with security considerations"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            df = None
            
            for encoding in encodings:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                raise ValueError("Could not decode CSV file with any supported encoding")
            
            return df
            
        except Exception as e:
            raise ValueError(f"CSV processing failed: {str(e)}")
    
    def _process_excel(self, uploaded_file: UploadedFile) -> pd.DataFrame:
        """Process Excel file with security sanitization"""
        try:
            # Save uploaded file temporarily
            temp_path = self.datasets_dir / f"temp_{int(timezone.now().timestamp())}.xlsx"
            
            with open(temp_path, 'wb') as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)
            
            # Load with openpyxl for security
            workbook = openpyxl.load_workbook(temp_path, data_only=True)
            
            # Get the first worksheet
            worksheet = workbook.active
            
            # Convert to DataFrame
            data = []
            for row in worksheet.iter_rows(values_only=True):
                data.append(row)
            
            df = pd.DataFrame(data[1:], columns=data[0] if data else [])
            
            # Clean up temp file
            temp_path.unlink()
            
            return df
            
        except Exception as e:
            # Clean up temp file if it exists
            if 'temp_path' in locals() and temp_path.exists():
                temp_path.unlink()
            raise ValueError(f"Excel processing failed: {str(e)}")
    
    def _process_json(self, uploaded_file: UploadedFile) -> pd.DataFrame:
        """Process JSON file"""
        try:
            uploaded_file.seek(0)
            content = uploaded_file.read().decode('utf-8')
            
            # Parse JSON
            data = json.loads(content)
            
            # Convert to DataFrame
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # Try to find array data
                for key, value in data.items():
                    if isinstance(value, list):
                        df = pd.DataFrame(value)
                        break
                else:
                    # Convert dict to single row
                    df = pd.DataFrame([data])
            else:
                raise ValueError("JSON structure not supported")
            
            return df
            
        except Exception as e:
            raise ValueError(f"JSON processing failed: {str(e)}")
    
    def _sanitize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Sanitize DataFrame to remove malicious content"""
        # Create a copy to avoid modifying original
        df_sanitized = df.copy()
        
        # Sanitize string columns
        for column in df_sanitized.columns:
            if df_sanitized[column].dtype == 'object':
                df_sanitized[column] = df_sanitized[column].astype(str).apply(
                    lambda x: self._sanitize_string(x) if pd.notna(x) else x
                )
        
        # Remove any rows that might contain malicious content
        df_sanitized = self._remove_suspicious_rows(df_sanitized)
        
        return df_sanitized
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize individual string values"""
        if not isinstance(text, str):
            return text
        
        # Remove HTML tags and scripts
        text = bleach.clean(text, tags=self.allowed_tags, attributes=self.allowed_attributes)
        
        # Remove potential formula injection
        text = re.sub(r'^[=+\-@]', '', text)  # Remove leading formula characters
        
        # Remove suspicious patterns
        suspicious_patterns = [
            r'javascript:', r'vbscript:', r'data:', r'file:',
            r'<script.*?</script>', r'<iframe.*?</iframe>',
            r'eval\s*\(', r'exec\s*\(', r'system\s*\('
        ]
        
        for pattern in suspicious_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        return text.strip()
    
    def _remove_suspicious_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove rows that might contain malicious content"""
        suspicious_mask = pd.Series([False] * len(df))
        
        for column in df.columns:
            if df[column].dtype == 'object':
                # Check for suspicious patterns in each cell
                column_mask = df[column].astype(str).str.contains(
                    r'<script|javascript:|vbscript:|eval\s*\(|exec\s*\(',
                    case=False, na=False, regex=True
                )
                suspicious_mask |= column_mask
        
        # Remove suspicious rows
        clean_df = df[~suspicious_mask].copy()
        
        if len(clean_df) < len(df):
            logger.warning(f"Removed {len(df) - len(clean_df)} suspicious rows from dataset")
        
        return clean_df
    
    def _convert_to_parquet(self, df: pd.DataFrame, file_hash: str, user_id: int) -> str:
        """Convert DataFrame to Parquet format"""
        # Create user-specific directory
        user_dir = self.datasets_dir / f"user_{user_id}"
        user_dir.mkdir(exist_ok=True)
        
        # Generate Parquet filename
        parquet_filename = f"{file_hash}.parquet"
        parquet_path = user_dir / parquet_filename
        
        # Convert to Parquet
        table = pa.Table.from_pandas(df)
        pq.write_table(table, parquet_path, compression='snappy')
        
        return str(parquet_path)
    
    def _create_dataset_record(self, uploaded_file: UploadedFile, user: User, 
                              df: pd.DataFrame, parquet_path: str, 
                              file_hash: str, dataset_name: Optional[str]) -> Dataset:
        """Create Dataset record in database"""
        return Dataset.objects.create(
            name=dataset_name or Path(uploaded_file.name).stem,
            description=f"Dataset uploaded from {uploaded_file.name}",
            original_filename=uploaded_file.name,
            file_size_bytes=uploaded_file.size,
            file_hash=file_hash,
            original_format=Path(uploaded_file.name).suffix.lower(),
            parquet_path=parquet_path,
            parquet_size_bytes=Path(parquet_path).stat().st_size,
            row_count=len(df),
            column_count=len(df.columns),
            data_types=df.dtypes.to_dict(),
            processing_status='completed',
            security_scan_passed=True,
            sanitized=True,
            data_quality_score=self._calculate_data_quality_score(df),
            metadata={
                'upload_timestamp': timezone.now().isoformat(),
                'file_type': uploaded_file.content_type,
                'processing_version': '1.0'
            },
            user=user
        )
    
    def _create_column_records(self, dataset: Dataset, df: pd.DataFrame) -> None:
        """Create DatasetColumn records for each column"""
        from analytics.services.column_type_manager import ColumnTypeManager
        
        column_manager = ColumnTypeManager()
        
        for column_name in df.columns:
            column_data = df[column_name]
            detected_type = column_manager.detect_column_type(column_data)
            
            DatasetColumn.objects.create(
                name=column_name,
                display_name=column_name.replace('_', ' ').title(),
                description=f"Column {column_name} from {dataset.original_filename}",
                detected_type=detected_type,
                confirmed_type=detected_type,
                confidence_score=column_manager.calculate_confidence_score(column_data, detected_type),
                null_count=column_data.isnull().sum(),
                null_percentage=(column_data.isnull().sum() / len(column_data)) * 100,
                unique_count=column_data.nunique(),
                unique_percentage=(column_data.nunique() / len(column_data)) * 100,
                dataset=dataset,
                **column_manager.calculate_statistics(column_data, detected_type)
            )
    
    def _get_columns_info(self, dataset: Dataset) -> List[Dict[str, Any]]:
        """Get columns information for a dataset"""
        columns = dataset.columns.all()
        return [
            {
                'name': col.name,
                'display_name': col.display_name,
                'type': col.confirmed_type,
                'confidence': col.confidence_score,
                'null_percentage': col.null_percentage,
                'unique_percentage': col.unique_percentage
            }
            for col in columns
        ]
    
    def _calculate_data_quality_score(self, df: pd.DataFrame) -> float:
        """Calculate data quality score (0-100)"""
        if df.empty:
            return 0.0
        
        # Factors affecting quality score
        completeness = (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        consistency = self._calculate_consistency_score(df)
        validity = self._calculate_validity_score(df)
        
        # Weighted average
        quality_score = (completeness * 0.4 + consistency * 0.3 + validity * 0.3)
        return round(quality_score, 2)
    
    def _calculate_consistency_score(self, df: pd.DataFrame) -> float:
        """Calculate data consistency score"""
        # Check for consistent data types within columns
        consistency_issues = 0
        total_cells = len(df) * len(df.columns)
        
        for column in df.columns:
            if df[column].dtype == 'object':
                # Check for mixed types in object columns
                non_null_values = df[column].dropna()
                if len(non_null_values) > 0:
                    first_type = type(non_null_values.iloc[0])
                    type_consistency = (non_null_values.apply(type) == first_type).sum()
                    consistency_issues += len(non_null_values) - type_consistency
        
        consistency_score = max(0, 100 - (consistency_issues / total_cells) * 100)
        return consistency_score
    
    def _calculate_validity_score(self, df: pd.DataFrame) -> float:
        """Calculate data validity score"""
        # Check for obviously invalid data
        validity_issues = 0
        total_cells = len(df) * len(df.columns)
        
        for column in df.columns:
            if df[column].dtype == 'object':
                # Check for empty strings, whitespace-only strings
                validity_issues += (df[column].astype(str).str.strip() == '').sum()
        
        validity_score = max(0, 100 - (validity_issues / total_cells) * 100)
        return validity_score
    
    def delete_dataset(self, dataset_id: int, user: User) -> bool:
        """Delete dataset and associated files"""
        try:
            dataset = Dataset.objects.get(id=dataset_id, user=user)
            
            # Delete Parquet file
            if dataset.parquet_path and Path(dataset.parquet_path).exists():
                Path(dataset.parquet_path).unlink()
            
            # Delete dataset record (cascades to columns)
            dataset.delete()
            
            # Log audit trail
            self.audit_manager.log_action(
                user_id=user.id,
                action_type='delete',
                action_category='data_management',
                resource_type='dataset',
                resource_id=dataset_id,
                resource_name=dataset.name,
                action_description='Dataset deleted successfully',
                success=True,
                data_changed=True
            )
            
            return True
            
        except Dataset.DoesNotExist:
            logger.warning(f"Dataset {dataset_id} not found for user {user.id}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete dataset {dataset_id}: {str(e)}")
            return False
    
    def _index_dataset_for_rag(self, dataset: Dataset, df: pd.DataFrame, user: User) -> None:
        """
        Index dataset content for RAG (Retrieval-Augmented Generation) system
        
        Args:
            dataset: Dataset model instance
            df: Processed DataFrame
            user: User who owns the dataset
        """
        try:
            # Create dataset overview vector note
            self._create_dataset_overview_note(dataset, df, user)
            
            # Create column information vector notes
            self._create_column_info_notes(dataset, df, user)
            
            # Create sample data vector notes (first few rows)
            self._create_sample_data_notes(dataset, df, user)
            
            # Create data quality insights vector notes
            self._create_data_quality_notes(dataset, df, user)
            
            logger.info(f"RAG indexing completed for dataset {dataset.id}")
            
        except Exception as e:
            logger.error(f"RAG indexing failed for dataset {dataset.id}: {str(e)}")
            # Don't raise exception - RAG indexing is not critical for file processing
    
    def _create_dataset_overview_note(self, dataset: Dataset, df: pd.DataFrame, user: User) -> None:
        """Create vector note for dataset overview"""
        try:
            overview_text = f"""
            Dataset: {dataset.name}
            Description: {dataset.description or 'No description provided'}
            File: {dataset.original_filename}
            Rows: {len(df)}
            Columns: {len(df.columns)}
            File Size: {dataset.file_size_bytes} bytes
            Upload Date: {dataset.created_at.strftime('%Y-%m-%d %H:%M:%S')}
            Data Types: {', '.join([f'{col}: {dtype}' for col, dtype in df.dtypes.items()])}
            """
            
            self.vector_note_manager.create_vector_note(
                title=f"Dataset Overview: {dataset.name}",
                text=overview_text.strip(),
                scope='dataset',
                content_type='dataset_overview',
                user=user,
                dataset=dataset,
                metadata={
                    'row_count': len(df),
                    'column_count': len(df.columns),
                    'file_size': dataset.file_size_bytes,
                    'upload_date': dataset.created_at.isoformat()
                },
                confidence_score=1.0
            )
            
        except Exception as e:
            logger.error(f"Failed to create dataset overview note: {str(e)}")
    
    def _create_column_info_notes(self, dataset: Dataset, df: pd.DataFrame, user: User) -> None:
        """Create vector notes for each column information"""
        try:
            for column in df.columns:
                column_info = df[column].describe()
                null_count = df[column].isnull().sum()
                unique_count = df[column].nunique()
                
                column_text = f"""
                Column: {column}
                Data Type: {df[column].dtype}
                Total Values: {len(df)}
                Null Values: {null_count}
                Unique Values: {unique_count}
                Null Percentage: {(null_count / len(df)) * 100:.2f}%
                """
                
                # Add statistical summary for numeric columns
                if df[column].dtype in ['int64', 'float64']:
                    column_text += f"""
                    Mean: {column_info.get('mean', 'N/A')}
                    Median: {column_info.get('50%', 'N/A')}
                    Min: {column_info.get('min', 'N/A')}
                    Max: {column_info.get('max', 'N/A')}
                    Standard Deviation: {column_info.get('std', 'N/A')}
                    """
                
                # Add sample values for categorical columns
                if df[column].dtype == 'object' and unique_count <= 20:
                    top_values = df[column].value_counts().head(5)
                    column_text += f"\nTop Values: {dict(top_values)}"
                
                self.vector_note_manager.create_vector_note(
                    title=f"Column Info: {column}",
                    text=column_text.strip(),
                    scope='dataset',
                    content_type='column_info',
                    user=user,
                    dataset=dataset,
                    metadata={
                        'column_name': column,
                        'data_type': str(df[column].dtype),
                        'null_count': int(null_count),
                        'unique_count': int(unique_count)
                    },
                    confidence_score=1.0
                )
                
        except Exception as e:
            logger.error(f"Failed to create column info notes: {str(e)}")
    
    def _create_sample_data_notes(self, dataset: Dataset, df: pd.DataFrame, user: User) -> None:
        """Create vector notes for sample data (first few rows)"""
        try:
            # Take first 3 rows as sample
            sample_df = df.head(3)
            
            sample_text = f"""
            Sample Data from Dataset: {dataset.name}
            
            First 3 rows:
            {sample_df.to_string()}
            
            This sample shows the structure and content of the dataset.
            """
            
            self.vector_note_manager.create_vector_note(
                title=f"Sample Data: {dataset.name}",
                text=sample_text.strip(),
                scope='dataset',
                content_type='sample_data',
                user=user,
                dataset=dataset,
                metadata={
                    'sample_rows': 3,
                    'total_rows': len(df),
                    'columns': list(df.columns)
                },
                confidence_score=1.0
            )
            
        except Exception as e:
            logger.error(f"Failed to create sample data notes: {str(e)}")
    
    def _create_data_quality_notes(self, dataset: Dataset, df: pd.DataFrame, user: User) -> None:
        """Create vector notes for data quality insights"""
        try:
            quality_score = self._calculate_data_quality_score(df)
            
            # Calculate quality metrics
            total_cells = len(df) * len(df.columns)
            null_cells = df.isnull().sum().sum()
            duplicate_rows = df.duplicated().sum()
            
            quality_text = f"""
            Data Quality Analysis for Dataset: {dataset.name}
            
            Overall Quality Score: {quality_score}/100
            
            Metrics:
            - Total Cells: {total_cells}
            - Null Cells: {null_cells} ({(null_cells/total_cells)*100:.2f}%)
            - Duplicate Rows: {duplicate_rows}
            - Data Completeness: {100 - (null_cells/total_cells)*100:.2f}%
            
            Quality Assessment:
            """
            
            if quality_score >= 90:
                quality_text += "Excellent data quality with minimal issues."
            elif quality_score >= 75:
                quality_text += "Good data quality with some minor issues."
            elif quality_score >= 60:
                quality_text += "Fair data quality with moderate issues."
            else:
                quality_text += "Poor data quality with significant issues."
            
            self.vector_note_manager.create_vector_note(
                title=f"Data Quality: {dataset.name}",
                text=quality_text.strip(),
                scope='dataset',
                content_type='data_quality',
                user=user,
                dataset=dataset,
                metadata={
                    'quality_score': quality_score,
                    'null_cells': int(null_cells),
                    'duplicate_rows': int(duplicate_rows),
                    'total_cells': int(total_cells)
                },
                confidence_score=1.0
            )
            
        except Exception as e:
            logger.error(f"Failed to create data quality notes: {str(e)}")
