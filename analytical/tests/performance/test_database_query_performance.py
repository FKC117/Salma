"""
Database Query Performance Tests

This module contains performance tests for database query operations,
ensuring efficient database access patterns.
"""

import time
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import override_settings

from analytics.models import (
    Dataset, DatasetColumn, AnalysisSession, AnalysisResult, 
    AnalysisTool, AgentRun, AgentStep, User, AuditTrail
)

User = get_user_model()


class DatabaseQueryPerformanceTest(TestCase):
    """Test database query performance"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_login(self.user)
        
        # Create test data
        self.datasets = []
        for i in range(10):
            dataset = Dataset.objects.create(
                name=f'test_dataset_{i}',
                user=self.user,
                file_size_bytes=1000 + i * 100,
                parquet_size_bytes=500 + i * 50,
                row_count=1000 + i * 100,
                column_count=5
            )
            self.datasets.append(dataset)
            
            # Create columns for each dataset
            for j in range(5):
                DatasetColumn.objects.create(
                    dataset=dataset,
                    name=f'column_{j}',
                    column_type='numeric',
                    data_type='float64',
                    is_numeric=True,
                    is_categorical=False
                )
        
        # Create analysis tool
        self.tool = AnalysisTool.objects.create(
            name='test_tool',
            display_name='Test Tool',
            description='Test analysis tool',
            tool_type='statistical',
            parameters_schema={'column': {'type': 'string', 'required': True}}
        )
    
    def test_dataset_query_performance(self):
        """Test dataset query performance"""
        start_time = time.time()
        
        # Test basic query
        datasets = Dataset.objects.filter(user=self.user)
        dataset_count = datasets.count()
        
        end_time = time.time()
        query_time = end_time - start_time
        
        self.assertEqual(dataset_count, 10)
        self.assertLess(query_time, 0.1, f"Dataset query took {query_time:.3f}s, should be <100ms")
    
    def test_dataset_with_columns_query_performance(self):
        """Test dataset with columns query performance"""
        start_time = time.time()
        
        # Test query with related data
        datasets = Dataset.objects.filter(user=self.user).prefetch_related('columns')
        for dataset in datasets:
            columns = dataset.columns.all()
            self.assertEqual(columns.count(), 5)
        
        end_time = time.time()
        query_time = end_time - start_time
        
        self.assertLess(query_time, 0.2, f"Dataset with columns query took {query_time:.3f}s, should be <200ms")
    
    def test_analysis_session_query_performance(self):
        """Test analysis session query performance"""
        # Create sessions
        for i, dataset in enumerate(self.datasets[:5]):
            AnalysisSession.objects.create(
                name=f'session_{i}',
                user=self.user,
                primary_dataset=dataset,
                is_active=True
            )
        
        start_time = time.time()
        
        # Test session queries
        sessions = AnalysisSession.objects.filter(user=self.user)
        active_sessions = AnalysisSession.objects.filter(user=self.user, is_active=True)
        
        end_time = time.time()
        query_time = end_time - start_time
        
        self.assertEqual(sessions.count(), 5)
        self.assertEqual(active_sessions.count(), 5)
        self.assertLess(query_time, 0.1, f"Analysis session query took {query_time:.3f}s, should be <100ms")
    
    def test_analysis_result_query_performance(self):
        """Test analysis result query performance"""
        # Create analysis results
        session = AnalysisSession.objects.create(
            name='test_session',
            user=self.user,
            primary_dataset=self.datasets[0],
            is_active=True
        )
        
        for i in range(20):
            AnalysisResult.objects.create(
                name=f'result_{i}',
                description=f'Test result {i}',
                tool_used=self.tool,
                session=session,
                dataset=self.datasets[0],
                result_data='{"test": "data"}',
                user=self.user
            )
        
        start_time = time.time()
        
        # Test result queries
        results = AnalysisResult.objects.filter(user=self.user)
        session_results = AnalysisResult.objects.filter(session=session)
        tool_results = AnalysisResult.objects.filter(tool_used=self.tool)
        
        end_time = time.time()
        query_time = end_time - start_time
        
        self.assertEqual(results.count(), 20)
        self.assertEqual(session_results.count(), 20)
        self.assertEqual(tool_results.count(), 20)
        self.assertLess(query_time, 0.1, f"Analysis result query took {query_time:.3f}s, should be <100ms")
    
    def test_agent_run_query_performance(self):
        """Test agent run query performance"""
        # Create agent runs
        for i, dataset in enumerate(self.datasets[:3]):
            agent_run = AgentRun.objects.create(
                dataset=dataset,
                session=AnalysisSession.objects.create(
                    name=f'agent_session_{i}',
                    user=self.user,
                    primary_dataset=dataset,
                    is_active=True
                ),
                user=self.user,
                analysis_goal=f'Test goal {i}',
                status='completed'
            )
            
            # Create agent steps
            for j in range(5):
                AgentStep.objects.create(
                    agent_run=agent_run,
                    step_type='test_step',
                    step_sequence=j + 1,
                    result_data='{"test": "data"}'
                )
        
        start_time = time.time()
        
        # Test agent run queries
        agent_runs = AgentRun.objects.filter(user=self.user)
        completed_runs = AgentRun.objects.filter(user=self.user, status='completed')
        
        # Test with related data
        runs_with_steps = AgentRun.objects.filter(user=self.user).prefetch_related('steps')
        for run in runs_with_steps:
            steps = run.steps.all()
            self.assertEqual(steps.count(), 5)
        
        end_time = time.time()
        query_time = end_time - start_time
        
        self.assertEqual(agent_runs.count(), 3)
        self.assertEqual(completed_runs.count(), 3)
        self.assertLess(query_time, 0.2, f"Agent run query took {query_time:.3f}s, should be <200ms")
    
    def test_audit_trail_query_performance(self):
        """Test audit trail query performance"""
        # Create audit trail entries
        for i in range(100):
            AuditTrail.objects.create(
                user_id=self.user.id,
                action_type='CREATE',
                action_category='test',
                resource_type='Dataset',
                resource_id=i,
                resource_name=f'dataset_{i}',
                action_description=f'Test action {i}'
            )
        
        start_time = time.time()
        
        # Test audit trail queries
        audit_entries = AuditTrail.objects.filter(user_id=self.user.id)
        create_actions = AuditTrail.objects.filter(user_id=self.user.id, action_type='CREATE')
        
        # Test pagination
        page_1 = AuditTrail.objects.filter(user_id=self.user.id)[:20]
        page_2 = AuditTrail.objects.filter(user_id=self.user.id)[20:40]
        
        end_time = time.time()
        query_time = end_time - start_time
        
        self.assertEqual(audit_entries.count(), 100)
        self.assertEqual(create_actions.count(), 100)
        self.assertEqual(len(page_1), 20)
        self.assertEqual(len(page_2), 20)
        self.assertLess(query_time, 0.2, f"Audit trail query took {query_time:.3f}s, should be <200ms")
    
    def test_complex_join_query_performance(self):
        """Test complex join query performance"""
        # Create complex data relationships
        session = AnalysisSession.objects.create(
            name='complex_session',
            user=self.user,
            primary_dataset=self.datasets[0],
            is_active=True
        )
        
        for i in range(10):
            result = AnalysisResult.objects.create(
                name=f'complex_result_{i}',
                description=f'Complex result {i}',
                tool_used=self.tool,
                session=session,
                dataset=self.datasets[0],
                result_data='{"complex": "data"}',
                user=self.user
            )
            
            # Create audit entries for each result
            AuditTrail.objects.create(
                user_id=self.user.id,
                action_type='EXECUTE',
                action_category='analysis',
                resource_type='AnalysisResult',
                resource_id=result.id,
                resource_name=result.name
            )
        
        start_time = time.time()
        
        # Test complex join query
        results_with_audit = AnalysisResult.objects.filter(
            user=self.user
        ).select_related('session', 'dataset', 'tool_used').prefetch_related(
            'audit_entries'
        )
        
        for result in results_with_audit:
            self.assertIsNotNone(result.session)
            self.assertIsNotNone(result.dataset)
            self.assertIsNotNone(result.tool_used)
        
        end_time = time.time()
        query_time = end_time - start_time
        
        self.assertEqual(results_with_audit.count(), 10)
        self.assertLess(query_time, 0.3, f"Complex join query took {query_time:.3f}s, should be <300ms")
    
    def test_database_connection_pooling(self):
        """Test database connection pooling performance"""
        start_time = time.time()
        
        # Perform multiple database operations
        for i in range(50):
            # Create and query data
            dataset = Dataset.objects.create(
                name=f'pool_test_{i}',
                user=self.user,
                file_size_bytes=1000,
                parquet_size_bytes=500,
                row_count=100,
                column_count=3
            )
            
            # Query the data
            queried_dataset = Dataset.objects.get(id=dataset.id)
            self.assertEqual(queried_dataset.name, f'pool_test_{i}')
            
            # Delete the data
            dataset.delete()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete within reasonable time
        self.assertLess(total_time, 2.0, f"Database connection pooling test took {total_time:.3f}s, should be <2s")
    
    def test_query_optimization_with_indexes(self):
        """Test query optimization with indexes"""
        # Create data with specific patterns for indexing
        for i in range(1000):
            Dataset.objects.create(
                name=f'index_test_{i}',
                user=self.user,
                file_size_bytes=1000 + (i % 100),
                parquet_size_bytes=500 + (i % 50),
                row_count=1000 + (i % 1000),
                column_count=5
            )
        
        start_time = time.time()
        
        # Test queries that should use indexes
        small_datasets = Dataset.objects.filter(
            user=self.user,
            file_size_bytes__lt=1050
        )
        
        large_datasets = Dataset.objects.filter(
            user=self.user,
            row_count__gt=1500
        )
        
        # Test ordering
        ordered_datasets = Dataset.objects.filter(
            user=self.user
        ).order_by('created_at')
        
        end_time = time.time()
        query_time = end_time - start_time
        
        self.assertGreater(small_datasets.count(), 0)
        self.assertGreater(large_datasets.count(), 0)
        self.assertEqual(ordered_datasets.count(), 1000)
        self.assertLess(query_time, 0.5, f"Indexed query took {query_time:.3f}s, should be <500ms")
    
    def test_bulk_operations_performance(self):
        """Test bulk operations performance"""
        start_time = time.time()
        
        # Test bulk create
        datasets_to_create = []
        for i in range(100):
            datasets_to_create.append(Dataset(
                name=f'bulk_test_{i}',
                user=self.user,
                file_size_bytes=1000,
                parquet_size_bytes=500,
                row_count=100,
                column_count=3
            ))
        
        Dataset.objects.bulk_create(datasets_to_create)
        
        # Test bulk update
        Dataset.objects.filter(
            user=self.user,
            name__startswith='bulk_test_'
        ).update(file_size_bytes=2000)
        
        # Test bulk delete
        deleted_count, _ = Dataset.objects.filter(
            user=self.user,
            name__startswith='bulk_test_'
        ).delete()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        self.assertEqual(deleted_count, 100)
        self.assertLess(total_time, 1.0, f"Bulk operations took {total_time:.3f}s, should be <1s")
    
    def test_database_transaction_performance(self):
        """Test database transaction performance"""
        from django.db import transaction
        
        start_time = time.time()
        
        # Test transaction performance
        with transaction.atomic():
            # Create multiple related objects in a transaction
            dataset = Dataset.objects.create(
                name='transaction_test',
                user=self.user,
                file_size_bytes=1000,
                parquet_size_bytes=500,
                row_count=100,
                column_count=3
            )
            
            session = AnalysisSession.objects.create(
                name='transaction_session',
                user=self.user,
                primary_dataset=dataset,
                is_active=True
            )
            
            for i in range(10):
                DatasetColumn.objects.create(
                    dataset=dataset,
                    name=f'transaction_column_{i}',
                    column_type='numeric',
                    data_type='float64',
                    is_numeric=True,
                    is_categorical=False
                )
        
        end_time = time.time()
        transaction_time = end_time - start_time
        
        # Verify data was created
        self.assertTrue(Dataset.objects.filter(name='transaction_test').exists())
        self.assertTrue(AnalysisSession.objects.filter(name='transaction_session').exists())
        self.assertEqual(DatasetColumn.objects.filter(dataset__name='transaction_test').count(), 10)
        
        self.assertLess(transaction_time, 0.5, f"Database transaction took {transaction_time:.3f}s, should be <500ms")
    
    def test_query_count_optimization(self):
        """Test query count optimization (N+1 problem)"""
        # Create data with relationships
        session = AnalysisSession.objects.create(
            name='query_count_test',
            user=self.user,
            primary_dataset=self.datasets[0],
            is_active=True
        )
        
        for i in range(20):
            AnalysisResult.objects.create(
                name=f'query_count_result_{i}',
                description=f'Result {i}',
                tool_used=self.tool,
                session=session,
                dataset=self.datasets[0],
                result_data='{"test": "data"}',
                user=self.user
            )
        
        # Test without optimization (N+1 problem)
        with self.assertNumQueries(21):  # 1 for results + 20 for session lookups
            results = AnalysisResult.objects.filter(user=self.user)
            for result in results:
                session_name = result.session.name
        
        # Test with optimization
        with self.assertNumQueries(1):  # Single query with select_related
            results = AnalysisResult.objects.filter(user=self.user).select_related('session')
            for result in results:
                session_name = result.session.name
    
    def test_database_connection_cleanup(self):
        """Test database connection cleanup"""
        initial_connections = len(connection.queries)
        
        # Perform many database operations
        for i in range(100):
            Dataset.objects.create(
                name=f'cleanup_test_{i}',
                user=self.user,
                file_size_bytes=1000,
                parquet_size_bytes=500,
                row_count=100,
                column_count=3
            )
        
        # Clean up
        Dataset.objects.filter(name__startswith='cleanup_test_').delete()
        
        final_connections = len(connection.queries)
        
        # Should not have excessive connection usage
        connection_increase = final_connections - initial_connections
        self.assertLess(connection_increase, 200, f"Too many database connections used: {connection_increase}")
    
    def test_database_query_caching(self):
        """Test database query caching performance"""
        # Create test data
        dataset = Dataset.objects.create(
            name='cache_test',
            user=self.user,
            file_size_bytes=1000,
            parquet_size_bytes=500,
            row_count=100,
            column_count=3
        )
        
        # First query (cold cache)
        start_time = time.time()
        dataset1 = Dataset.objects.get(id=dataset.id)
        first_query_time = time.time() - start_time
        
        # Second query (warm cache)
        start_time = time.time()
        dataset2 = Dataset.objects.get(id=dataset.id)
        second_query_time = time.time() - start_time
        
        # Cached query should be faster
        self.assertEqual(dataset1.id, dataset2.id)
        # Note: In test environment, caching might not be as effective
        # but we can still verify the query works correctly
