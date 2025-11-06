#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Query Filter Tests

Tests all filter implementations:
- Relational filters (SQL)
- Vector filters (embeddings)
- Graph filters (Neo4j)
- File storage filters
- Combined filters
"""
import pytest
import tempfile
import os
import numpy as np

# Filter imports
from search.query_filters_relational import RelationalFilter
from search.query_filters_vector import VectorFilter
from search.query_filters_graph import GraphFilter
from search.query_filters_file_storage import FileStorageFilter
from search.query_filters_combined import CombinedFilter
from database.database_api_sqlite import SQLiteDatabaseAPI


class TestRelationalFilter:
    """Test SQL-based relational filters"""
    
    @pytest.fixture
    def db(self):
        """Create temporary database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db_api = SQLiteDatabaseAPI(db_path)
        db_api.execute_query("""
            CREATE TABLE documents (
                id INTEGER PRIMARY KEY,
                title TEXT,
                category TEXT,
                created_date TEXT,
                status TEXT
            )
        """)
        
        # Insert test data
        test_data = [
            (1, "Doc A", "Finance", "2024-01-01", "active"),
            (2, "Doc B", "HR", "2024-01-15", "active"),
            (3, "Doc C", "Finance", "2024-02-01", "archived"),
            (4, "Doc D", "IT", "2024-02-15", "active"),
            (5, "Doc E", "Finance", "2024-03-01", "draft")
        ]
        for record in test_data:
            db_api.execute_query(
                "INSERT INTO documents VALUES (?, ?, ?, ?, ?)",
                record
            )
        
        yield db_api
        
        db_api.close()
        os.unlink(db_path)
    
    def test_simple_filter(self, db):
        """Test simple equality filter"""
        filter = RelationalFilter(db, table="documents")
        
        # Filter by category
        results = filter.filter(category="Finance")
        assert len(results) == 3
        
        # Filter by status
        results = filter.filter(status="active")
        assert len(results) == 3
    
    def test_combined_filters(self, db):
        """Test multiple filter conditions (AND)"""
        filter = RelationalFilter(db, table="documents")
        
        # Finance AND active
        results = filter.filter(category="Finance", status="active")
        assert len(results) == 1
        assert results[0][1] == "Doc A"
    
    def test_date_range_filter(self, db):
        """Test date range filtering"""
        filter = RelationalFilter(db, table="documents")
        
        # Documents created in January 2024
        results = filter.filter_date_range(
            "created_date",
            start="2024-01-01",
            end="2024-01-31"
        )
        assert len(results) == 2
    
    def test_like_filter(self, db):
        """Test LIKE pattern matching"""
        filter = RelationalFilter(db, table="documents")
        
        # Titles containing "Doc"
        results = filter.filter_like("title", "%Doc%")
        assert len(results) == 5
        
        # Titles starting with "Doc A"
        results = filter.filter_like("title", "Doc A%")
        assert len(results) == 1
    
    def test_in_filter(self, db):
        """Test IN clause filtering"""
        filter = RelationalFilter(db, table="documents")
        
        # Category in (Finance, IT)
        results = filter.filter_in("category", ["Finance", "IT"])
        assert len(results) == 4


class TestVectorFilter:
    """Test vector-based similarity filters"""
    
    @pytest.fixture
    def vector_db(self):
        """Create mock vector database"""
        # Mock embeddings (3-dimensional for testing)
        embeddings = {
            "doc1": np.array([1.0, 0.0, 0.0]),
            "doc2": np.array([0.9, 0.1, 0.0]),
            "doc3": np.array([0.0, 1.0, 0.0]),
            "doc4": np.array([0.0, 0.0, 1.0]),
            "doc5": np.array([0.5, 0.5, 0.0])
        }
        return embeddings
    
    def test_cosine_similarity(self, vector_db):
        """Test cosine similarity search"""
        filter = VectorFilter(embeddings=vector_db)
        
        # Query vector similar to doc1
        query = np.array([0.95, 0.05, 0.0])
        
        results = filter.filter_by_similarity(
            query,
            top_k=2,
            similarity_metric="cosine"
        )
        
        # Should return doc1 and doc2 (most similar)
        assert len(results) == 2
        assert results[0][0] == "doc1"
    
    def test_euclidean_distance(self, vector_db):
        """Test euclidean distance search"""
        filter = VectorFilter(embeddings=vector_db)
        
        # Query vector
        query = np.array([1.0, 0.0, 0.0])
        
        results = filter.filter_by_similarity(
            query,
            top_k=3,
            similarity_metric="euclidean"
        )
        
        assert len(results) == 3
    
    def test_threshold_filtering(self, vector_db):
        """Test filtering by similarity threshold"""
        filter = VectorFilter(embeddings=vector_db)
        
        query = np.array([1.0, 0.0, 0.0])
        
        # Only vectors with similarity > 0.8
        results = filter.filter_by_threshold(
            query,
            threshold=0.8,
            similarity_metric="cosine"
        )
        
        # Should return doc1 and doc2
        assert len(results) >= 1


class TestGraphFilter:
    """Test graph-based filters (Neo4j patterns)"""
    
    def test_relationship_filter(self):
        """Test filtering by relationships"""
        # Mock graph data
        graph = {
            "nodes": [
                {"id": "person1", "type": "Person", "name": "Alice"},
                {"id": "person2", "type": "Person", "name": "Bob"},
                {"id": "company1", "type": "Company", "name": "TechCorp"}
            ],
            "edges": [
                {"from": "person1", "to": "company1", "type": "WORKS_AT"},
                {"from": "person2", "to": "company1", "type": "WORKS_AT"}
            ]
        }
        
        filter = GraphFilter(graph_data=graph)
        
        # Find all people working at TechCorp
        results = filter.filter_by_relationship(
            target_node="company1",
            relationship_type="WORKS_AT",
            direction="incoming"
        )
        
        assert len(results) == 2
    
    def test_path_filter(self):
        """Test filtering by path patterns"""
        graph = {
            "nodes": [
                {"id": "A", "type": "Node"},
                {"id": "B", "type": "Node"},
                {"id": "C", "type": "Node"}
            ],
            "edges": [
                {"from": "A", "to": "B", "type": "CONNECTS"},
                {"from": "B", "to": "C", "type": "CONNECTS"}
            ]
        }
        
        filter = GraphFilter(graph_data=graph)
        
        # Find path A -> B -> C
        path = filter.find_path(start="A", end="C", max_depth=3)
        
        assert path is not None
        assert len(path) >= 2
    
    def test_subgraph_filter(self):
        """Test extracting subgraphs"""
        graph = {
            "nodes": [
                {"id": "1", "category": "A"},
                {"id": "2", "category": "A"},
                {"id": "3", "category": "B"}
            ],
            "edges": [
                {"from": "1", "to": "2", "type": "LINK"},
                {"from": "2", "to": "3", "type": "LINK"}
            ]
        }
        
        filter = GraphFilter(graph_data=graph)
        
        # Get subgraph of category A nodes
        subgraph = filter.extract_subgraph(
            node_filter=lambda n: n.get("category") == "A"
        )
        
        assert len(subgraph["nodes"]) == 2


class TestFileStorageFilter:
    """Test file storage filters"""
    
    @pytest.fixture
    def file_storage(self):
        """Create temporary file storage"""
        temp_dir = tempfile.mkdtemp()
        
        # Create test files
        files = {
            "doc1.txt": {"content": "Finance report", "size": 100, "type": "txt"},
            "doc2.pdf": {"content": "HR policy", "size": 500, "type": "pdf"},
            "doc3.txt": {"content": "IT guide", "size": 200, "type": "txt"},
            "doc4.docx": {"content": "Finance memo", "size": 300, "type": "docx"}
        }
        
        for filename, metadata in files.items():
            path = os.path.join(temp_dir, filename)
            with open(path, 'w') as f:
                f.write(metadata["content"])
        
        yield temp_dir, files
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_filter_by_extension(self, file_storage):
        """Test filtering by file extension"""
        storage_path, files = file_storage
        filter = FileStorageFilter(base_path=storage_path)
        
        # Get all .txt files
        results = filter.filter_by_extension(".txt")
        assert len(results) == 2
    
    def test_filter_by_size(self, file_storage):
        """Test filtering by file size"""
        storage_path, files = file_storage
        filter = FileStorageFilter(base_path=storage_path)
        
        # Files larger than 150 bytes
        results = filter.filter_by_size(min_size=150)
        assert len(results) >= 2
    
    def test_filter_by_content(self, file_storage):
        """Test filtering by content pattern"""
        storage_path, files = file_storage
        filter = FileStorageFilter(base_path=storage_path)
        
        # Files containing "Finance"
        results = filter.filter_by_content_pattern("Finance")
        assert len(results) == 2
    
    def test_filter_by_date(self, file_storage):
        """Test filtering by creation/modification date"""
        storage_path, files = file_storage
        filter = FileStorageFilter(base_path=storage_path)
        
        import datetime
        
        # Files created today
        today = datetime.datetime.now().date()
        results = filter.filter_by_date(start_date=today)
        
        # All test files should match
        assert len(results) >= 4


class TestCombinedFilters:
    """Test combining multiple filter types"""
    
    @pytest.fixture
    def db(self):
        """Create temporary database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db_api = SQLiteDatabaseAPI(db_path)
        db_api.execute_query("""
            CREATE TABLE combined_test (
                id INTEGER PRIMARY KEY,
                category TEXT,
                score REAL
            )
        """)
        
        for i in range(10):
            db_api.execute_query(
                "INSERT INTO combined_test (category, score) VALUES (?, ?)",
                ("cat" + str(i % 3), float(i))
            )
        
        yield db_api
        
        db_api.close()
        os.unlink(db_path)
    
    def test_and_combination(self, db):
        """Test AND combination of filters"""
        filter1 = RelationalFilter(db, table="combined_test")
        filter2 = RelationalFilter(db, table="combined_test")
        
        # Category = cat0 AND score > 5
        results1 = filter1.filter(category="cat0")
        results2 = filter2.filter_numeric("score", min_value=5.0)
        
        # Combine with AND logic
        combined = CombinedFilter.combine_and([
            set(r[0] for r in results1),
            set(r[0] for r in results2)
        ])
        
        assert len(combined) >= 1
    
    def test_or_combination(self, db):
        """Test OR combination of filters"""
        filter1 = RelationalFilter(db, table="combined_test")
        filter2 = RelationalFilter(db, table="combined_test")
        
        # Category = cat0 OR score < 2
        results1 = filter1.filter(category="cat0")
        results2 = filter2.filter_numeric("score", max_value=2.0)
        
        # Combine with OR logic
        combined = CombinedFilter.combine_or([
            set(r[0] for r in results1),
            set(r[0] for r in results2)
        ])
        
        assert len(combined) >= 4


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
