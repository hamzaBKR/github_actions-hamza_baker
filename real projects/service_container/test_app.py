"""
Integration tests for E-commerce API
Tests database and cache functionality with service containers
"""
import pytest
from fastapi.testclient import TestClient
from app import app, init_db, get_db_connection, get_redis_connection
import time

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Initialize database before tests"""
    init_db()
    yield
    # Cleanup after all tests
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS products")
    conn.commit()
    cursor.close()
    conn.close()

@pytest.fixture(autouse=True)
def cleanup_data():
    """Clean up data before each test"""
    # Clear database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products")
    conn.commit()
    cursor.close()
    conn.close()
    
    # Clear Redis cache
    r = get_redis_connection()
    r.flushdb()
    
    yield

class TestHealthCheck:
    """Test health check endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns success"""
        response = client.get("/")
        assert response.status_code == 200
        assert "E-commerce API" in response.json()["message"]
    
    def test_health_check_postgres_redis(self):
        """Test that both PostgreSQL and Redis are connected"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["postgres"] == "connected"
        assert data["redis"] == "connected"

class TestProductCRUD:
    """Test product CRUD operations"""
    
    def test_create_product(self):
        """Test creating a new product"""
        product_data = {
            "name": "Laptop",
            "description": "Gaming laptop",
            "price": 1299.99,
            "stock": 10
        }
        
        response = client.post("/products", json=product_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Laptop"
        assert data["price"] == 1299.99
        assert "id" in data
    
    def test_list_products(self):
        """Test listing all products"""
        # Create some products
        products = [
            {"name": "Product 1", "description": "Desc 1", "price": 10.0, "stock": 5},
            {"name": "Product 2", "description": "Desc 2", "price": 20.0, "stock": 3},
        ]
        
        for product in products:
            client.post("/products", json=product)
        
        response = client.get("/products")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Product 1"
        assert data[1]["name"] == "Product 2"
    
    def test_get_single_product(self):
        """Test getting a single product by ID"""
        # Create a product
        product_data = {
            "name": "Smartphone",
            "description": "Latest model",
            "price": 799.99,
            "stock": 20
        }
        
        create_response = client.post("/products", json=product_data)
        product_id = create_response.json()["id"]
        
        # Get the product
        response = client.get(f"/products/{product_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Smartphone"
        assert data["price"] == 799.99
    
    def test_get_nonexistent_product(self):
        """Test getting a product that doesn't exist"""
        response = client.get("/products/99999")
        assert response.status_code == 404
    
    def test_update_product(self):
        """Test updating a product"""
        # Create a product
        product_data = {
            "name": "Old Name",
            "description": "Old description",
            "price": 100.0,
            "stock": 5
        }
        
        create_response = client.post("/products", json=product_data)
        product_id = create_response.json()["id"]
        
        # Update the product
        updated_data = {
            "name": "New Name",
            "description": "New description",
            "price": 150.0,
            "stock": 10
        }
        
        response = client.put(f"/products/{product_id}", json=updated_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "New Name"
        assert data["price"] == 150.0
        assert data["stock"] == 10
    
    def test_delete_product(self):
        """Test deleting a product"""
        # Create a product
        product_data = {
            "name": "To Delete",
            "description": "Will be deleted",
            "price": 50.0,
            "stock": 1
        }
        
        create_response = client.post("/products", json=product_data)
        product_id = create_response.json()["id"]
        
        # Delete the product
        response = client.delete(f"/products/{product_id}")
        assert response.status_code == 200
        
        # Verify it's gone
        get_response = client.get(f"/products/{product_id}")
        assert get_response.status_code == 404

class TestCaching:
    """Test Redis caching functionality"""
    
    def test_cache_on_list_products(self):
        """Test that product list is cached"""
        # Create a product
        product_data = {
            "name": "Cached Product",
            "description": "For cache test",
            "price": 25.0,
            "stock": 3
        }
        client.post("/products", json=product_data)
        
        # First request - should hit database
        response1 = client.get("/products")
        assert response1.status_code == 200
        
        # Second request - should hit cache
        response2 = client.get("/products")
        assert response2.status_code == 200
        
        # Results should be identical
        assert response1.json() == response2.json()
    
    def test_cache_on_single_product(self):
        """Test that single product is cached"""
        # Create a product
        product_data = {
            "name": "Single Cached",
            "description": "Cache test",
            "price": 15.0,
            "stock": 2
        }
        
        create_response = client.post("/products", json=product_data)
        product_id = create_response.json()["id"]
        
        # Get product multiple times
        response1 = client.get(f"/products/{product_id}")
        response2 = client.get(f"/products/{product_id}")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json() == response2.json()
    
    def test_cache_invalidation_on_update(self):
        """Test that cache is invalidated when product is updated"""
        # Create a product
        product_data = {
            "name": "Original",
            "description": "Original desc",
            "price": 30.0,
            "stock": 5
        }
        
        create_response = client.post("/products", json=product_data)
        product_id = create_response.json()["id"]
        
        # Get product (this caches it)
        client.get(f"/products/{product_id}")
        
        # Update product
        updated_data = {
            "name": "Updated",
            "description": "Updated desc",
            "price": 40.0,
            "stock": 10
        }
        client.put(f"/products/{product_id}", json=updated_data)
        
        # Get product again - should have new data
        response = client.get(f"/products/{product_id}")
        data = response.json()
        
        assert data["name"] == "Updated"
        assert data["price"] == 40.0
    
    def test_cache_invalidation_on_delete(self):
        """Test that cache is invalidated when product is deleted"""
        # Create and cache a product
        product_data = {
            "name": "To Be Deleted",
            "description": "Delete test",
            "price": 20.0,
            "stock": 1
        }
        
        create_response = client.post("/products", json=product_data)
        product_id = create_response.json()["id"]
        
        # Cache it
        client.get(f"/products/{product_id}")
        
        # Delete it
        client.delete(f"/products/{product_id}")
        
        # Try to get it - should be gone
        response = client.get(f"/products/{product_id}")
        assert response.status_code == 404
    
    def test_cache_stats(self):
        """Test that cache statistics are available"""
        response = client.get("/cache/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_commands_processed" in data
        assert "keyspace_hits" in data
        assert "keyspace_misses" in data

class TestDatabaseIntegrity:
    """Test database integrity and constraints"""
    
    def test_concurrent_operations(self):
        """Test that concurrent operations work correctly"""
        # Create multiple products quickly
        products = []
        for i in range(5):
            product_data = {
                "name": f"Product {i}",
                "description": f"Description {i}",
                "price": float(i * 10),
                "stock": i
            }
            response = client.post("/products", json=product_data)
            products.append(response.json()["id"])
        
        # Verify all were created
        response = client.get("/products")
        assert len(response.json()) == 5
    
    def test_decimal_precision(self):
        """Test that price decimals are handled correctly"""
        product_data = {
            "name": "Precise Price",
            "description": "Test decimals",
            "price": 99.99,
            "stock": 1
        }
        
        response = client.post("/products", json=product_data)
        assert response.json()["price"] == 99.99

class TestServiceContainerConnectivity:
    """Test that service containers are properly connected"""
    
    def test_postgres_connection(self):
        """Test direct PostgreSQL connection"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        cursor.close()
        conn.close()
        
        assert version is not None
        assert "PostgreSQL" in str(version)
    
    def test_redis_connection(self):
        """Test direct Redis connection"""
        r = get_redis_connection()
        
        # Test set/get
        r.set("test_key", "test_value")
        value = r.get("test_key")
        
        assert value == "test_value"
        
        # Cleanup
        r.delete("test_key")
    
    def test_redis_operations(self):
        """Test various Redis operations"""
        r = get_redis_connection()
        
        # String operations
        r.set("str_key", "value")
        assert r.get("str_key") == "value"
        
        # Expiration
        r.setex("exp_key", 1, "expires")
        assert r.get("exp_key") == "expires"
        time.sleep(2)
        assert r.get("exp_key") is None
        
        # List operations
        r.lpush("list_key", "item1", "item2")
        assert r.llen("list_key") == 2
        
        # Cleanup
        r.delete("str_key", "list_key")

# Run tests with: pytest test_app.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
