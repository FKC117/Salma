"""
Machine Learning Tools

This module provides comprehensive machine learning tools for the analytical system.
All tools are designed to work with pandas DataFrames and return standardized results.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.svm import SVC, SVR
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                           mean_squared_error, mean_absolute_error, r2_score,
                           classification_report, confusion_matrix, silhouette_score)
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, f_classif, f_regression
from typing import Dict, List, Any, Optional, Tuple, Union
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class MachineLearningTools:
    """
    Collection of machine learning tools for data analysis
    """
    
    @staticmethod
    def train_classifier(df: pd.DataFrame, target_column: str, 
                        feature_columns: Optional[List[str]] = None,
                        model_type: str = 'random_forest', test_size: float = 0.2,
                        random_state: int = 42) -> Dict[str, Any]:
        """
        Train a classification model
        
        Args:
            df: Input DataFrame
            target_column: Name of target column
            feature_columns: List of feature columns (if None, all except target)
            model_type: Type of model ('random_forest', 'logistic_regression', 'svm')
            test_size: Proportion of data for testing
            random_state: Random state for reproducibility
            
        Returns:
            Dict containing model results and metrics
        """
        try:
            if target_column not in df.columns:
                return {"error": f"Target column '{target_column}' not found in DataFrame"}
            
            if feature_columns is None:
                feature_columns = [col for col in df.columns if col != target_column]
            else:
                missing_cols = [col for col in feature_columns if col not in df.columns]
                if missing_cols:
                    return {"error": f"Feature columns not found: {missing_cols}"}
            
            # Prepare data
            X = df[feature_columns].copy()
            y = df[target_column].copy()
            
            # Handle missing values
            X = X.fillna(X.mean() if X.select_dtypes(include=[np.number]).shape[1] > 0 else X.mode().iloc[0])
            y = y.fillna(y.mode().iloc[0]) if y.dtype == 'object' else y.fillna(y.mean())
            
            # Encode categorical variables
            label_encoders = {}
            for col in X.select_dtypes(include=['object']).columns:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
                label_encoders[col] = le
            
            # Encode target if categorical
            if y.dtype == 'object':
                le_target = LabelEncoder()
                y = le_target.fit_transform(y.astype(str))
                target_classes = le_target.classes_.tolist()
            else:
                le_target = None
                target_classes = None
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state, stratify=y if le_target else None
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model
            if model_type == 'random_forest':
                model = RandomForestClassifier(n_estimators=100, random_state=random_state)
            elif model_type == 'logistic_regression':
                model = LogisticRegression(random_state=random_state, max_iter=1000)
            elif model_type == 'svm':
                model = SVC(random_state=random_state, probability=True)
            else:
                return {"error": f"Unknown model type: {model_type}"}
            
            model.fit(X_train_scaled, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test_scaled)
            y_pred_proba = model.predict_proba(X_test_scaled) if hasattr(model, 'predict_proba') else None
            
            # Calculate metrics
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
            recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
            f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
            
            # Feature importance (if available)
            feature_importance = None
            if hasattr(model, 'feature_importances_'):
                feature_importance = dict(zip(feature_columns, model.feature_importances_))
            elif hasattr(model, 'coef_'):
                feature_importance = dict(zip(feature_columns, abs(model.coef_[0])))
            
            return {
                'type': 'classification',
                'model_type': model_type,
                'metrics': {
                    'accuracy': float(accuracy),
                    'precision': float(precision),
                    'recall': float(recall),
                    'f1_score': float(f1),
                    'cv_mean': float(cv_scores.mean()),
                    'cv_std': float(cv_scores.std())
                },
                'predictions': {
                    'y_test': y_test.tolist(),
                    'y_pred': y_pred.tolist(),
                    'y_pred_proba': y_pred_proba.tolist() if y_pred_proba is not None else None
                },
                'feature_importance': feature_importance,
                'target_classes': target_classes,
                'feature_columns': feature_columns,
                'data_info': {
                    'train_size': len(X_train),
                    'test_size': len(X_test),
                    'n_features': len(feature_columns),
                    'created_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in train_classifier: {str(e)}")
            return {"error": f"Classification training failed: {str(e)}"}
    
    @staticmethod
    def train_regressor(df: pd.DataFrame, target_column: str,
                       feature_columns: Optional[List[str]] = None,
                       model_type: str = 'random_forest', test_size: float = 0.2,
                       random_state: int = 42) -> Dict[str, Any]:
        """
        Train a regression model
        
        Args:
            df: Input DataFrame
            target_column: Name of target column
            feature_columns: List of feature columns (if None, all except target)
            model_type: Type of model ('random_forest', 'linear_regression', 'svr')
            test_size: Proportion of data for testing
            random_state: Random state for reproducibility
            
        Returns:
            Dict containing model results and metrics
        """
        try:
            if target_column not in df.columns:
                return {"error": f"Target column '{target_column}' not found in DataFrame"}
            
            if feature_columns is None:
                feature_columns = [col for col in df.columns if col != target_column]
            else:
                missing_cols = [col for col in feature_columns if col not in df.columns]
                if missing_cols:
                    return {"error": f"Feature columns not found: {missing_cols}"}
            
            # Prepare data
            X = df[feature_columns].copy()
            y = df[target_column].copy()
            
            # Handle missing values
            X = X.fillna(X.mean() if X.select_dtypes(include=[np.number]).shape[1] > 0 else X.mode().iloc[0])
            y = y.fillna(y.mean())
            
            # Encode categorical variables
            label_encoders = {}
            for col in X.select_dtypes(include=['object']).columns:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
                label_encoders[col] = le
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model
            if model_type == 'random_forest':
                model = RandomForestRegressor(n_estimators=100, random_state=random_state)
            elif model_type == 'linear_regression':
                model = LinearRegression()
            elif model_type == 'svr':
                model = SVR()
            else:
                return {"error": f"Unknown model type: {model_type}"}
            
            model.fit(X_train_scaled, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test_scaled)
            
            # Calculate metrics
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='r2')
            
            # Feature importance (if available)
            feature_importance = None
            if hasattr(model, 'feature_importances_'):
                feature_importance = dict(zip(feature_columns, model.feature_importances_))
            elif hasattr(model, 'coef_'):
                feature_importance = dict(zip(feature_columns, abs(model.coef_)))
            
            return {
                'type': 'regression',
                'model_type': model_type,
                'metrics': {
                    'mse': float(mse),
                    'rmse': float(rmse),
                    'mae': float(mae),
                    'r2_score': float(r2),
                    'cv_mean': float(cv_scores.mean()),
                    'cv_std': float(cv_scores.std())
                },
                'predictions': {
                    'y_test': y_test.tolist(),
                    'y_pred': y_pred.tolist()
                },
                'feature_importance': feature_importance,
                'feature_columns': feature_columns,
                'data_info': {
                    'train_size': len(X_train),
                    'test_size': len(X_test),
                    'n_features': len(feature_columns),
                    'created_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in train_regressor: {str(e)}")
            return {"error": f"Regression training failed: {str(e)}"}
    
    @staticmethod
    def clustering(df: pd.DataFrame, feature_columns: Optional[List[str]] = None,
                  n_clusters: int = 3, algorithm: str = 'kmeans',
                  random_state: int = 42) -> Dict[str, Any]:
        """
        Perform clustering analysis
        
        Args:
            df: Input DataFrame
            feature_columns: List of feature columns (if None, all numeric columns)
            n_clusters: Number of clusters
            algorithm: Clustering algorithm ('kmeans', 'dbscan')
            random_state: Random state for reproducibility
            
        Returns:
            Dict containing clustering results
        """
        try:
            if feature_columns is None:
                feature_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            else:
                missing_cols = [col for col in feature_columns if col not in df.columns]
                if missing_cols:
                    return {"error": f"Feature columns not found: {missing_cols}"}
            
            if len(feature_columns) < 2:
                return {"error": "At least 2 numeric columns required for clustering"}
            
            # Prepare data
            X = df[feature_columns].copy()
            X = X.fillna(X.mean())
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Perform clustering
            if algorithm == 'kmeans':
                model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
                cluster_labels = model.fit_predict(X_scaled)
                cluster_centers = model.cluster_centers_
            elif algorithm == 'dbscan':
                model = DBSCAN(eps=0.5, min_samples=5)
                cluster_labels = model.fit_predict(X_scaled)
                cluster_centers = None
            else:
                return {"error": f"Unknown clustering algorithm: {algorithm}"}
            
            # Calculate silhouette score
            if len(set(cluster_labels)) > 1:
                silhouette_avg = silhouette_score(X_scaled, cluster_labels)
            else:
                silhouette_avg = -1
            
            # Cluster statistics
            unique_labels = np.unique(cluster_labels)
            cluster_stats = []
            
            for label in unique_labels:
                if label == -1:  # Noise points in DBSCAN
                    continue
                cluster_data = X[cluster_labels == label]
                cluster_stats.append({
                    'cluster_id': int(label),
                    'size': len(cluster_data),
                    'percentage': len(cluster_data) / len(X) * 100,
                    'centroid': cluster_data.mean().to_dict() if cluster_centers is None else None
                })
            
            return {
                'type': 'clustering',
                'algorithm': algorithm,
                'n_clusters': len(unique_labels),
                'cluster_labels': cluster_labels.tolist(),
                'cluster_centers': cluster_centers.tolist() if cluster_centers is not None else None,
                'silhouette_score': float(silhouette_avg),
                'cluster_statistics': cluster_stats,
                'feature_columns': feature_columns,
                'data_info': {
                    'total_points': len(X),
                    'n_features': len(feature_columns),
                    'created_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in clustering: {str(e)}")
            return {"error": f"Clustering failed: {str(e)}"}
    
    @staticmethod
    def feature_selection(df: pd.DataFrame, target_column: str,
                         feature_columns: Optional[List[str]] = None,
                         k: int = 10, method: str = 'f_classif') -> Dict[str, Any]:
        """
        Perform feature selection
        
        Args:
            df: Input DataFrame
            target_column: Name of target column
            feature_columns: List of feature columns (if None, all except target)
            k: Number of top features to select
            method: Selection method ('f_classif', 'f_regression', 'mutual_info')
            
        Returns:
            Dict containing feature selection results
        """
        try:
            if target_column not in df.columns:
                return {"error": f"Target column '{target_column}' not found in DataFrame"}
            
            if feature_columns is None:
                feature_columns = [col for col in df.columns if col != target_column]
            else:
                missing_cols = [col for col in feature_columns if col not in df.columns]
                if missing_cols:
                    return {"error": f"Feature columns not found: {missing_cols}"}
            
            # Prepare data
            X = df[feature_columns].copy()
            y = df[target_column].copy()
            
            # Handle missing values
            X = X.fillna(X.mean() if X.select_dtypes(include=[np.number]).shape[1] > 0 else X.mode().iloc[0])
            y = y.fillna(y.mode().iloc[0]) if y.dtype == 'object' else y.fillna(y.mean())
            
            # Encode categorical variables
            for col in X.select_dtypes(include=['object']).columns:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
            
            # Determine if classification or regression
            is_classification = y.dtype == 'object' or len(y.unique()) < 10
            
            # Select appropriate scoring function
            if method == 'f_classif' and is_classification:
                score_func = f_classif
            elif method == 'f_regression' and not is_classification:
                score_func = f_regression
            else:
                return {"error": f"Method '{method}' not suitable for {'classification' if is_classification else 'regression'}"}
            
            # Perform feature selection
            selector = SelectKBest(score_func=score_func, k=min(k, len(feature_columns)))
            X_selected = selector.fit_transform(X, y)
            
            # Get selected features
            selected_features = [feature_columns[i] for i in selector.get_support(indices=True)]
            feature_scores = dict(zip(feature_columns, selector.scores_))
            
            return {
                'type': 'feature_selection',
                'method': method,
                'k': k,
                'selected_features': selected_features,
                'feature_scores': feature_scores,
                'is_classification': is_classification,
                'data_info': {
                    'total_features': len(feature_columns),
                    'selected_count': len(selected_features),
                    'created_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in feature_selection: {str(e)}")
            return {"error": f"Feature selection failed: {str(e)}"}
    
    @staticmethod
    def pca_analysis(df: pd.DataFrame, feature_columns: Optional[List[str]] = None,
                    n_components: int = 2, explained_variance_threshold: float = 0.95) -> Dict[str, Any]:
        """
        Perform Principal Component Analysis
        
        Args:
            df: Input DataFrame
            feature_columns: List of feature columns (if None, all numeric columns)
            n_components: Number of components to return
            explained_variance_threshold: Threshold for cumulative explained variance
            
        Returns:
            Dict containing PCA results
        """
        try:
            if feature_columns is None:
                feature_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            else:
                missing_cols = [col for col in feature_columns if col not in df.columns]
                if missing_cols:
                    return {"error": f"Feature columns not found: {missing_cols}"}
            
            if len(feature_columns) < 2:
                return {"error": "At least 2 numeric columns required for PCA"}
            
            # Prepare data
            X = df[feature_columns].copy()
            X = X.fillna(X.mean())
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Perform PCA
            pca = PCA(n_components=min(n_components, len(feature_columns)))
            X_pca = pca.fit_transform(X_scaled)
            
            # Calculate explained variance
            explained_variance_ratio = pca.explained_variance_ratio_
            cumulative_variance = np.cumsum(explained_variance_ratio)
            
            # Find number of components for threshold
            n_components_threshold = np.argmax(cumulative_variance >= explained_variance_threshold) + 1
            
            # Component loadings
            components = pca.components_
            feature_loadings = {}
            for i, component in enumerate(components):
                feature_loadings[f'PC{i+1}'] = dict(zip(feature_columns, component))
            
            return {
                'type': 'pca_analysis',
                'n_components': n_components,
                'explained_variance_ratio': explained_variance_ratio.tolist(),
                'cumulative_variance': cumulative_variance.tolist(),
                'n_components_threshold': int(n_components_threshold),
                'transformed_data': X_pca.tolist(),
                'feature_loadings': feature_loadings,
                'feature_columns': feature_columns,
                'data_info': {
                    'original_features': len(feature_columns),
                    'total_variance_explained': float(cumulative_variance[-1]),
                    'created_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in pca_analysis: {str(e)}")
            return {"error": f"PCA analysis failed: {str(e)}"}
    
    @staticmethod
    def model_evaluation(df: pd.DataFrame, target_column: str,
                        feature_columns: Optional[List[str]] = None,
                        model_type: str = 'classification',
                        cv_folds: int = 5) -> Dict[str, Any]:
        """
        Comprehensive model evaluation with cross-validation
        
        Args:
            df: Input DataFrame
            target_column: Name of target column
            feature_columns: List of feature columns (if None, all except target)
            model_type: Type of model ('classification', 'regression')
            cv_folds: Number of cross-validation folds
            
        Returns:
            Dict containing evaluation results
        """
        try:
            if target_column not in df.columns:
                return {"error": f"Target column '{target_column}' not found in DataFrame"}
            
            if feature_columns is None:
                feature_columns = [col for col in df.columns if col != target_column]
            else:
                missing_cols = [col for col in feature_columns if col not in df.columns]
                if missing_cols:
                    return {"error": f"Feature columns not found: {missing_cols}"}
            
            # Prepare data
            X = df[feature_columns].copy()
            y = df[target_column].copy()
            
            # Handle missing values
            X = X.fillna(X.mean() if X.select_dtypes(include=[np.number]).shape[1] > 0 else X.mode().iloc[0])
            y = y.fillna(y.mode().iloc[0]) if y.dtype == 'object' else y.fillna(y.mean())
            
            # Encode categorical variables
            for col in X.select_dtypes(include=['object']).columns:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
            
            # Determine if classification or regression
            is_classification = y.dtype == 'object' or len(y.unique()) < 10
            
            if model_type == 'classification' and not is_classification:
                return {"error": "Target column appears to be continuous, not categorical"}
            elif model_type == 'regression' and is_classification:
                return {"error": "Target column appears to be categorical, not continuous"}
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Define models to evaluate
            if is_classification:
                models = {
                    'Random Forest': RandomForestClassifier(random_state=42),
                    'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000),
                    'SVM': SVC(random_state=42)
                }
                scoring = 'accuracy'
            else:
                models = {
                    'Random Forest': RandomForestRegressor(random_state=42),
                    'Linear Regression': LinearRegression(),
                    'SVR': SVR()
                }
                scoring = 'r2'
            
            # Evaluate models
            results = {}
            for name, model in models.items():
                try:
                    cv_scores = cross_val_score(model, X_scaled, y, cv=cv_folds, scoring=scoring)
                    results[name] = {
                        'mean_score': float(cv_scores.mean()),
                        'std_score': float(cv_scores.std()),
                        'scores': cv_scores.tolist()
                    }
                except Exception as e:
                    results[name] = {'error': str(e)}
            
            # Find best model
            best_model = max(results.keys(), key=lambda x: results[x].get('mean_score', -1))
            
            return {
                'type': 'model_evaluation',
                'model_type': model_type,
                'is_classification': is_classification,
                'cv_folds': cv_folds,
                'scoring': scoring,
                'results': results,
                'best_model': best_model,
                'feature_columns': feature_columns,
                'data_info': {
                    'total_samples': len(X),
                    'n_features': len(feature_columns),
                    'created_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in model_evaluation: {str(e)}")
            return {"error": f"Model evaluation failed: {str(e)}"}
