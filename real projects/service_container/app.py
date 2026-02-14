"""
E-commerce API with PostgreSQL and Redis
Demonstrates service containers in GitHub Actions
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import json
import os
from typing import List, Optional

app = FastAPI()

# Database connection
def get_db_connection():
    """Get PostgreSQL connection"""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        database=os.getenv("POSTGRES_DB", "ecommerce"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "testpass"),
        cursor_factory=RealDictCursor
    )

# Redis connection
def get_redis_connection():
    """Get Redis connection"""
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        decode_responses=True
    )

# Models
class Product(BaseModel):
    name: str
    description: str
    price: float
    stock: int

class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    stock: int

# Initialize database
def init_db():
    """Create tables if they don't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            price DECIMAL(10, 2) NOT NULL,
            stock INTEGER NOT NULL
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()

# Endpoints
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()

@app.get("/")
def root():
    """Health check endpoint"""
    return {"message": "E-commerce API is running!"}

@app.get("/health")
def health_check():
    """Check if services are healthy"""
    try:
        # Check PostgreSQL
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        
        # Check Redis
        r = get_redis_connection()
        r.ping()
        
        return {
            "status": "healthy",
            "postgres": "connected",
            "redis": "connected"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.post("/products", response_model=ProductResponse)
def create_product(product: Product):
    """Create a new product"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        INSERT INTO products (name, description, price, stock)
        VALUES (%s, %s, %s, %s)
        RETURNING id, name, description, price, stock
        """,
        (product.name, product.description, product.price, product.stock)
    )
    
    new_product = cursor.fetchone()
    conn.commit()
    
    # Invalidate cache
    r = get_redis_connection()
    r.delete("products:all")
    
    cursor.close()
    conn.close()
    
    return dict(new_product)

@app.get("/products", response_model=List[ProductResponse])
def list_products(use_cache: bool = True):
    """List all products (with Redis caching)"""
    r = get_redis_connection()
    
    # Try to get from cache
    if use_cache:
        cached = r.get("products:all")
        if cached:
            return json.loads(cached)
    
    # Get from database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM products ORDER BY id")
    products = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Cache the result (expire in 5 minutes)
    products_list = [dict(p) for p in products]
    r.setex("products:all", 300, json.dumps(products_list))
    
    return products_list

@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int):
    """Get a specific product (with caching)"""
    r = get_redis_connection()
    
    # Try cache first
    cache_key = f"product:{product_id}"
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Get from database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Cache it
    product_dict = dict(product)
    r.setex(cache_key, 300, json.dumps(product_dict))
    
    return product_dict

@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product: Product):
    """Update a product"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        UPDATE products
        SET name = %s, description = %s, price = %s, stock = %s
        WHERE id = %s
        RETURNING id, name, description, price, stock
        """,
        (product.name, product.description, product.price, product.stock, product_id)
    )
    
    updated_product = cursor.fetchone()
    conn.commit()
    
    if not updated_product:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Invalidate cache
    r = get_redis_connection()
    r.delete(f"product:{product_id}")
    r.delete("products:all")
    
    cursor.close()
    conn.close()
    
    return dict(updated_product)

@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    """Delete a product"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM products WHERE id = %s RETURNING id", (product_id,))
    deleted = cursor.fetchone()
    conn.commit()
    
    cursor.close()
    conn.close()
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Invalidate cache
    r = get_redis_connection()
    r.delete(f"product:{product_id}")
    r.delete("products:all")
    
    return {"message": "Product deleted successfully"}

@app.get("/cache/stats")
def cache_stats():
    """Get cache statistics"""
    r = get_redis_connection()
    
    info = r.info("stats")
    
    return {
        "total_commands_processed": info.get("total_commands_processed", 0),
        "keyspace_hits": info.get("keyspace_hits", 0),
        "keyspace_misses": info.get("keyspace_misses", 0),
        "connected_clients": info.get("connected_clients", 0)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
