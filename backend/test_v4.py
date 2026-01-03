"""
Test Script for Professional Backend V4

This script tests all major components of the new multi-agent system:
1. DuckDB Service
2. Embedding Service
3. Schema Extraction Service
4. RAG Service
5. Analytics Service V4 (complete pipeline)
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.duckdb_service import duckdb_service
from app.services.embedding_service import embedding_service
from app.services.schema_extraction_service import schema_extraction_service
from app.services.rag_service import rag_service
from app.services.analytics_service_v4 import analytics_service_v4
from app.database import SessionLocal
from app.models import Dataset, User
from app.config import settings
import json


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def print_success(message):
    """Print success message"""
    print(f"✅ {message}")


def print_error(message):
    """Print error message"""
    print(f"❌ {message}")


def print_info(message):
    """Print info message"""
    print(f"ℹ️  {message}")


async def test_duckdb_service():
    """Test DuckDB service"""
    print_section("TEST 1: DuckDB Service")
    
    try:
        # Create a simple test dataset
        import pandas as pd
        import tempfile
        
        # Create sample data
        data = {
            'Product': ['Widget A', 'Widget B', 'Widget C', 'Widget A', 'Widget B'],
            'Revenue': [1000, 1500, 2000, 1200, 1800],
            'Quantity': [10, 15, 20, 12, 18],
            'Date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05']
        }
        df = pd.DataFrame(data)
        
        # Save to temp CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            temp_file = f.name
        
        print_info(f"Created test CSV with {len(df)} rows")
        
        # Test loading file
        dataset_id = 999  # Test dataset ID
        result = duckdb_service.load_file(dataset_id, temp_file, "data")
        
        print_success(f"Loaded file into DuckDB: {result['row_count']} rows, {len(result['schema'])} columns")
        
        # Test schema extraction
        schema = duckdb_service.get_schema(dataset_id, "data")
        print_info(f"Schema: {json.dumps(schema, indent=2)}")
        
        # Test query execution
        sql = 'SELECT "Product", SUM("Revenue") as total_revenue FROM data GROUP BY "Product" ORDER BY total_revenue DESC'
        query_result = duckdb_service.execute_query(dataset_id, sql)
        
        if query_result['success']:
            print_success(f"Query executed successfully: {query_result['row_count']} rows returned")
            print_info(f"Results: {json.dumps(query_result['data'], indent=2)}")
        else:
            print_error(f"Query failed: {query_result.get('error')}")
        
        # Test column statistics
        stats = duckdb_service.get_column_stats(dataset_id, "data")
        print_success(f"Column statistics generated for {len(stats)} columns")
        print_info(f"Revenue stats: {json.dumps(stats.get('Revenue', {}), indent=2)}")
        
        # Cleanup
        os.unlink(temp_file)
        duckdb_service.close_connection(dataset_id)
        
        return True
        
    except Exception as e:
        print_error(f"DuckDB test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_embedding_service():
    """Test Embedding service"""
    print_section("TEST 2: Embedding Service")
    
    try:
        # Check if API key is configured
        if not settings.OPENAI_API_KEY:
            print_error("OpenAI API key not configured. Skipping embedding test.")
            return False
        
        # Test single embedding
        text = "Customer revenue by product category"
        embedding = embedding_service.generate_embedding(text)
        
        if embedding:
            print_success(f"Generated embedding: {len(embedding)} dimensions")
            print_info(f"First 5 values: {embedding[:5]}")
        else:
            print_error("Failed to generate embedding")
            return False
        
        # Test batch embeddings
        texts = [
            "Total sales by region",
            "Monthly revenue trend",
            "Top 10 customers"
        ]
        embeddings = embedding_service.generate_embeddings_batch(texts)
        print_success(f"Generated {len(embeddings)} batch embeddings")
        
        # Test similarity
        query_emb = embedding_service.generate_embedding("Revenue by region")
        similarity = embedding_service.cosine_similarity(query_emb, embeddings[0])
        print_success(f"Cosine similarity: {similarity:.4f}")
        
        return True
        
    except Exception as e:
        print_error(f"Embedding test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_schema_extraction():
    """Test Schema Extraction service"""
    print_section("TEST 3: Schema Extraction Service")
    
    try:
        # Create test data
        import pandas as pd
        import tempfile
        
        data = {
            'customer_id': [1, 2, 3, 4, 5],
            'customer_name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
            'total_revenue': [5000, 3000, 8000, 2000, 6000],
            'order_count': [10, 5, 15, 3, 12],
            'signup_date': ['2023-01-01', '2023-02-15', '2023-03-20', '2023-04-10', '2023-05-05'],
            'status': ['Active', 'Active', 'Inactive', 'Active', 'Active']
        }
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            temp_file = f.name
        
        print_info(f"Created test dataset with {len(df)} rows, {len(df.columns)} columns")
        
        # Create a test dataset in database
        db = SessionLocal()
        
        # Create test user if not exists
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            from app.services.auth_service import hash_password
            test_user = User(
                email="test@example.com",
                username="testuser",
                hashed_password=hash_password("testpass123")
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
        
        # Create test dataset
        dataset = Dataset(
            name="Test Dataset",
            filename="test.csv",
            file_path=temp_file,
            file_type="csv",
            user_id=test_user.id,
            status="processing"
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        print_info(f"Created dataset with ID: {dataset.id}")
        
        # Test schema extraction
        result = await schema_extraction_service.extract_and_store_schema(
            dataset_id=dataset.id,
            file_path=temp_file,
            db=db
        )
        
        if result['success']:
            print_success(f"Schema extracted: {result['column_count']} columns, {result['row_count']} rows")
            print_info(f"Sample schema: {json.dumps(result['schema'][:2], indent=2)}")
        else:
            print_error("Schema extraction failed")
            return False
        
        # Cleanup
        os.unlink(temp_file)
        db.delete(dataset)
        db.commit()
        db.close()
        
        return True
        
    except Exception as e:
        print_error(f"Schema extraction test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_analytics_pipeline():
    """Test complete Analytics V4 pipeline"""
    print_section("TEST 4: Analytics Service V4 Pipeline")
    
    try:
        # Check if required API keys are configured
        if not settings.ANTHROPIC_API_KEY:
            print_error("Anthropic API key not configured. Skipping pipeline test.")
            print_info("Set ANTHROPIC_API_KEY in .env to test the complete pipeline")
            return False
        
        if not settings.OPENAI_API_KEY:
            print_error("OpenAI API key not configured. Skipping pipeline test.")
            print_info("Set OPENAI_API_KEY in .env to test the complete pipeline")
            return False
        
        # Create comprehensive test data
        import pandas as pd
        import tempfile
        
        data = {
            'Order Date': ['2024-01-15', '2024-01-20', '2024-02-10', '2024-02-25', '2024-03-05',
                          '2024-03-15', '2024-04-01', '2024-04-20', '2024-05-10', '2024-05-25'],
            'Product Name': ['Widget A', 'Widget B', 'Widget A', 'Widget C', 'Widget B',
                           'Widget A', 'Widget C', 'Widget B', 'Widget A', 'Widget C'],
            'Product Category': ['Electronics', 'Electronics', 'Electronics', 'Furniture', 'Electronics',
                               'Electronics', 'Furniture', 'Electronics', 'Electronics', 'Furniture'],
            'Revenue': [1000, 1500, 1200, 2000, 1800, 1100, 2200, 1600, 1300, 2100],
            'Quantity': [10, 15, 12, 20, 18, 11, 22, 16, 13, 21],
            'Customer Name': ['Alice', 'Bob', 'Alice', 'Charlie', 'Bob',
                            'David', 'Charlie', 'Eve', 'Alice', 'David'],
            'Region': ['North', 'South', 'North', 'East', 'South',
                      'West', 'East', 'South', 'North', 'West']
        }
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            temp_file = f.name
        
        print_info(f"Created test dataset: {len(df)} rows, {len(df.columns)} columns")
        
        # Setup database
        db = SessionLocal()
        
        # Get or create test user
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            from app.services.auth_service import hash_password
            test_user = User(
                email="test@example.com",
                username="testuser",
                hashed_password=hash_password("testpass123")
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
        
        # Create dataset
        dataset = Dataset(
            name="Sales Test Dataset",
            filename="sales_test.csv",
            file_path=temp_file,
            file_type="csv",
            user_id=test_user.id,
            status="processing"
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        print_info(f"Dataset ID: {dataset.id}")
        
        # Extract schema first
        print_info("Extracting schema...")
        schema_result = await schema_extraction_service.extract_and_store_schema(
            dataset_id=dataset.id,
            file_path=temp_file,
            db=db
        )
        print_success(f"Schema extracted: {schema_result['column_count']} columns")
        
        # Test queries
        test_questions = [
            "What are the top 3 products by revenue?",
            "Show me monthly revenue trend",
            "What is the total revenue by category?"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n--- Test Query {i}: {question} ---")
            
            result = await analytics_service_v4.analyze_query(
                user_question=question,
                dataset_id=dataset.id,
                db=db
            )
            
            if result.get('success'):
                print_success("Analysis completed successfully!")
                print_info(f"Intent: {result.get('intent')}")
                print_info(f"SQL: {result.get('sql', 'N/A')[:200]}...")
                print_info(f"Rows returned: {result.get('row_count', 0)}")
                print_info(f"Execution time: {result.get('execution_time')}ms")
                print_info(f"Visualization: {result.get('visualization', {}).get('chart_type', 'N/A')}")
                
                if result.get('insights'):
                    print_info(f"Insights preview: {result['insights'][:200]}...")
                
                if result.get('metadata'):
                    meta = result['metadata']
                    print_info(f"Metadata: Columns retrieved: {meta.get('rag_context_summary', {}).get('columns_retrieved', 0)}, "
                             f"SQL attempts: {meta.get('sql_attempts', 1)}")
            else:
                print_error(f"Analysis failed: {result.get('error', 'Unknown error')}")
        
        # Cleanup
        os.unlink(temp_file)
        duckdb_service.close_connection(dataset.id)
        db.delete(dataset)
        db.commit()
        db.close()
        
        return True
        
    except Exception as e:
        print_error(f"Analytics pipeline test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "🧪 " * 40)
    print("  PROFESSIONAL BACKEND V4 - COMPREHENSIVE TEST SUITE")
    print("🧪 " * 40)
    
    results = {}
    
    # Test 1: DuckDB Service
    results['duckdb'] = await test_duckdb_service()
    
    # Test 2: Embedding Service
    results['embedding'] = await test_embedding_service()
    
    # Test 3: Schema Extraction
    results['schema_extraction'] = await test_schema_extraction()
    
    # Test 4: Complete Pipeline
    results['analytics_pipeline'] = await test_analytics_pipeline()
    
    # Summary
    print_section("TEST SUMMARY")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    print(f"\n{'='*80}")
    print(f"  Total: {total} | Passed: {passed} | Failed: {failed}")
    print(f"  Success Rate: {(passed/total*100):.1f}%")
    print(f"{'='*80}\n")
    
    if failed == 0:
        print("🎉 All tests passed! The V4 backend is ready to use.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
