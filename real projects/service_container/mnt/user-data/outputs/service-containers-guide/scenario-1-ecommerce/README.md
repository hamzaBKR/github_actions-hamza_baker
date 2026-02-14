# Scenario 1: E-commerce API with PostgreSQL & Redis

## 🎯 Learning Objectives

This scenario teaches you:
- How to use **service containers** in GitHub Actions
- PostgreSQL for data persistence
- Redis for caching
- Integration testing with real services
- The difference between mocking and real service testing

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────┐
│              GitHub Actions Runner                      │
├────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────┐                                   │
│  │  Your Tests     │                                   │
│  │  (pytest)       │                                   │
│  │                 │                                   │
│  │  1. Create      │◄──────┐                          │
│  │  2. Read        │       │                          │
│  │  3. Update      │       │                          │
│  │  4. Delete      │       │                          │
│  └─────────────────┘       │                          │
│         │                   │                          │
│         │                   │                          │
│         ▼                   │                          │
│  ┌─────────────────┐       │                          │
│  │  FastAPI App    │       │                          │
│  │                 │       │                          │
│  │  • Routes       │       │                          │
│  │  • Business     │       │                          │
│  │    Logic        │       │                          │
│  └─────────────────┘       │                          │
│         │                   │                          │
│    ┌────┴────┐             │                          │
│    ▼         ▼             │                          │
│  ┌─────┐  ┌──────┐        │                          │
│  │ DB  │  │Cache │        │                          │
│  │ SQL │  │ Get  │        │                          │
│  │     │  │ Set  │        │                          │
│  └─────┘  └──────┘        │                          │
│     │         │            │                          │
│  ───┼─────────┼────────────┼─── Docker Network        │
│     │         │            │                          │
│     ▼         ▼            │                          │
│  ┌───────────────┐   ┌──────────────┐               │
│  │  PostgreSQL   │   │    Redis     │               │
│  │  (Service)    │   │  (Service)   │               │
│  │               │   │              │               │
│  │  • Port 5432  │   │  • Port 6379 │               │
│  │  • Health ✓   │   │  • Health ✓  │               │
│  └───────────────┘   └──────────────┘               │
│                                                       │
└───────────────────────────────────────────────────────┘
```

---

## 🔑 Key Concepts Demonstrated

### 1. Service Container Configuration

```yaml
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: testpass
      POSTGRES_DB: ecommerce
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
    ports:
      - 5432:5432
```

**What's happening:**
- `image`: Which Docker image to use
- `env`: Environment variables for the container
- `options`: Docker run options (health checks!)
- `ports`: Map container port to host

### 2. Health Checks (Critical!)

```yaml
options: >-
  --health-cmd pg_isready
  --health-interval 10s
  --health-timeout 5s
  --health-retries 5
```

**Why needed:** Your tests might start before PostgreSQL is ready!

Without health checks:
```
❌ Tests start → PostgreSQL still starting → Connection refused → Tests fail
```

With health checks:
```
✅ PostgreSQL starting → Health check fails → Wait → Health check passes → Tests start
```

### 3. Networking

**Connection string in tests:**
```python
DATABASE_URL = "postgresql://postgres:testpass@localhost:5432/ecommerce"
```

**Why `localhost`?**
- Your job runs on the GitHub Actions runner
- Service containers are accessible via `localhost` on mapped ports
- Inside a container, you'd use the service name (`postgres`)

---

## 📊 What This App Does

### E-commerce Product API with Caching

**Features:**
1. **CRUD Operations**: Create, Read, Update, Delete products
2. **PostgreSQL**: Persistent storage for products
3. **Redis Caching**: Cache product data to reduce database queries
4. **Cache Invalidation**: Automatic cache clearing on updates/deletes
5. **Health Checks**: Monitor service connectivity

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/health` | Check PostgreSQL + Redis |
| POST | `/products` | Create product |
| GET | `/products` | List all products (cached) |
| GET | `/products/{id}` | Get single product (cached) |
| PUT | `/products/{id}` | Update product |
| DELETE | `/products/{id}` | Delete product |
| GET | `/cache/stats` | Redis statistics |

---

## 🚀 Running Locally

### Option 1: Docker Compose (Recommended)

```bash
# Start all services
docker-compose up

# Run tests
docker-compose run app pytest test_app.py -v

# View logs
docker-compose logs -f app

# Stop everything
docker-compose down
```

**Access:**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- pgAdmin: http://localhost:5050
- Redis Commander: http://localhost:8081

### Option 2: Manual Setup

```bash
# Start PostgreSQL
docker run -d \
  --name postgres \
  -e POSTGRES_PASSWORD=testpass \
  -e POSTGRES_DB=ecommerce \
  -p 5432:5432 \
  postgres:15

# Start Redis
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7-alpine

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export POSTGRES_HOST=localhost
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=testpass
export POSTGRES_DB=ecommerce
export REDIS_HOST=localhost
export REDIS_PORT=6379

# Run app
python app.py

# Run tests (in another terminal)
pytest test_app.py -v
```

---

## 🧪 Tests Explained

### Test Categories

1. **Health Check Tests**
   - Verify API is running
   - Check PostgreSQL connection
   - Check Redis connection

2. **CRUD Tests**
   - Create products
   - List products
   - Get single product
   - Update products
   - Delete products

3. **Caching Tests**
   - Verify data is cached
   - Test cache invalidation on update
   - Test cache invalidation on delete
   - Cache statistics

4. **Database Integrity Tests**
   - Concurrent operations
   - Decimal precision
   - Data consistency

5. **Service Container Tests**
   - Direct PostgreSQL connection
   - Direct Redis connection
   - Redis operations (set/get/expire)

### Running Specific Tests

```bash
# All tests
pytest test_app.py -v

# Specific test class
pytest test_app.py::TestCaching -v

# Specific test
pytest test_app.py::TestCaching::test_cache_on_list_products -v

# With coverage
pytest test_app.py --cov=app --cov-report=html
```

---

## 🔍 GitHub Actions Workflow Breakdown

### Job 1: test-with-services

**Purpose:** Run integration tests with real services

**Key steps:**
1. Start service containers (PostgreSQL + Redis)
2. Wait for services to be healthy
3. Install dependencies
4. Run pytest
5. Verify service connectivity

**Environment variables:**
```yaml
env:
  POSTGRES_HOST: localhost  # Use localhost (running on runner)
  REDIS_HOST: localhost
```

### Job 2: test-with-mocks

**Purpose:** Show the limitations of mocking (educational)

**Demonstrates:**
- What you'd miss without service containers
- Why integration tests are valuable

### Job 3: performance-test

**Purpose:** Performance testing with services

**Shows:**
- Service containers can be reused across jobs
- Same setup as integration tests

---

## 💡 Key Learnings

### 1. Service Containers vs Mocks

| Aspect | Mocks | Service Containers |
|--------|-------|-------------------|
| Database Queries | ❌ Simulated | ✅ Real SQL executed |
| Cache Behavior | ❌ Fake | ✅ Actual Redis |
| Integration | ❌ Limited | ✅ Full coverage |
| Confidence | ⚠️ Medium | ✅ High |
| Speed | ✅ Fast | ⚠️ Slightly slower |

### 2. When to Use Service Containers

**✅ Use them for:**
- Integration tests
- API endpoint tests
- Database migration tests
- Multi-service tests
- Performance tests

**❌ Don't use them for:**
- Unit tests (use mocks)
- Simple logic tests
- Tests that don't need I/O

### 3. Health Checks Are Critical

```yaml
# Without health checks
services:
  postgres:
    image: postgres:15
# Tests might fail randomly! ❌

# With health checks
services:
  postgres:
    image: postgres:15
    options: >-
      --health-cmd pg_isready
# Tests wait for ready state ✅
```

### 4. Same Setup Locally and CI

**docker-compose.yml** mirrors GitHub Actions:
- Same PostgreSQL version
- Same Redis version
- Same environment variables
- Same network setup

**Benefit:** If it works locally, it works in CI!

---

## 🎓 Practice Exercises

### Beginner
1. Add a new endpoint to get products by price range
2. Add tests for the new endpoint
3. Add a cache for the new endpoint

### Intermediate
1. Add pagination to the product list
2. Implement search functionality
3. Add a second Redis instance for sessions

### Advanced
1. Add Elasticsearch for full-text search
2. Implement database connection pooling
3. Add distributed caching with Redis Cluster

---

## 🐛 Troubleshooting

### Issue: "Connection refused" to PostgreSQL
**Solution:**
- Add health check to service container
- Add wait script before running tests
- Check port mapping (5432:5432)

### Issue: Tests fail randomly
**Solution:**
- Health checks might be too aggressive
- Increase intervals and retries

### Issue: Cache not working
**Solution:**
- Check Redis connection string
- Verify Redis port is mapped
- Check cache key naming

### Issue: "Database already exists" error
**Solution:**
- Tests should clean up after themselves
- Add `@pytest.fixture(autouse=True)` for cleanup

---

## 📚 Additional Resources

- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)
- [Redis Docker Hub](https://hub.docker.com/_/redis)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [pytest Documentation](https://docs.pytest.org/)

---

## ✅ Checklist

After completing this scenario, you should be able to:
- [ ] Configure service containers in GitHub Actions
- [ ] Add health checks to services
- [ ] Connect to services from tests
- [ ] Understand port mapping
- [ ] Write integration tests
- [ ] Use Redis for caching
- [ ] Run the same setup locally and in CI

---

## 🎉 Next Steps

Once you're comfortable with this scenario:
1. Move to **Scenario 2**: MySQL + RabbitMQ
2. Try combining multiple service patterns
3. Apply this to your own projects

---

## 🤝 Contributing

Found a bug or have a suggestion? Improve this scenario and share!
