# 🐳 Service Containers in GitHub Actions - Complete Guide

## 📚 What Are Service Containers?

**Service containers** are Docker containers that run ALONGSIDE your job to provide services like databases, caches, message queues, etc. They're temporary and automatically cleaned up after the job finishes.

### 🎯 Key Concepts

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions Runner                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐          ┌─────────────────────┐     │
│  │   Your Job       │◄────────►│  Service Container  │     │
│  │                  │  Network │  (PostgreSQL)       │     │
│  │  - Run tests     │          │                     │     │
│  │  - Connect to DB │          │  • Auto-started     │     │
│  │  - Use Redis     │          │  • Auto-cleaned     │     │
│  └──────────────────┘          │  • Networked        │     │
│                                 └─────────────────────┘     │
│                                                              │
│                                 ┌─────────────────────┐     │
│                                 │  Service Container  │     │
│                                 │  (Redis)            │     │
│                                 └─────────────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Job Container vs Service Container

| Aspect | Job Container | Service Container |
|--------|--------------|-------------------|
| **Purpose** | Runs your code | Provides services (DB, cache) |
| **Location** | `container:` key | `services:` key |
| **Count** | One per job | Multiple per job |
| **Your code runs** | Inside | Outside (connects to it) |
| **Example** | Python runtime | PostgreSQL, Redis |

---

## 🎓 Scenarios Covered

I've created **5 real-world scenarios** with complete working examples:

1. **Scenario 1**: Testing with PostgreSQL + Redis (E-commerce API)
2. **Scenario 2**: Integration tests with MySQL + RabbitMQ (Order Processing)
3. **Scenario 3**: Multi-service microservices testing
4. **Scenario 4**: MongoDB + Elasticsearch (Search Service)
5. **Scenario 5**: Full-stack with Frontend + Backend + Database

Each scenario includes:
- Complete application code
- GitHub Actions workflow
- Local development setup (docker-compose)
- Tests that prove it works

---

## 📁 Project Structure

```
service-containers-guide/
├── README.md (this file)
├── scenario-1-ecommerce/         # PostgreSQL + Redis
├── scenario-2-orders/            # MySQL + RabbitMQ
├── scenario-3-microservices/     # Multiple services
├── scenario-4-search/            # MongoDB + Elasticsearch
├── scenario-5-fullstack/         # Complete web app
└── visual-guide.html             # Interactive guide
```

---

## 🔑 Key Differences: Service Containers vs Docker Compose

### In Docker Compose (Local Development)
```yaml
services:
  app:
    build: .
  postgres:
    image: postgres:15
  redis:
    image: redis:7
```
All services are equal, networked together.

### In GitHub Actions (CI)
```yaml
jobs:
  test:
    services:
      postgres:
        image: postgres:15
      redis:
        image: redis:7
    steps:
      - run: python test.py  # Runs on runner, connects to services
```
Services are supporting actors, your job is the main actor.

---

## 🎯 When to Use Service Containers

### ✅ Perfect Use Cases
- **Integration Testing**: Test your app with real databases
- **API Testing**: Test against real Redis, RabbitMQ, etc.
- **Database Migrations**: Test schema changes
- **Multi-service Testing**: Microservices communication
- **Performance Testing**: Test under realistic conditions

### ❌ When NOT to Use
- **Unit Tests**: Mock dependencies instead
- **Production Deployment**: Use actual infrastructure
- **Heavy Services**: GitHub has resource limits
- **State Persistence**: Services are ephemeral

---

## 🚀 Quick Start

### Basic Pattern

```yaml
name: Test with Database

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:testpass@postgres:5432/postgres
        run: python test.py
```

### Key Elements Explained

1. **`services:`** - Defines service containers
2. **`image:`** - Docker image to use
3. **`env:`** - Environment variables for the service
4. **`options:`** - Docker run options (health checks!)
5. **Connection**: Use service name as hostname (`postgres`, `redis`)

---

## 📊 Service Container Networking

### How Services Connect

```
┌─────────────────────────────────────────────────────────┐
│  GitHub Actions Runner                                   │
│                                                          │
│  Your Job: localhost                                    │
│    ↓                                                     │
│    ├─ postgres://postgres:5432  ─────────────┐         │
│    ├─ redis://redis:6379  ──────────────┐    │         │
│    └─ http://nginx:80  ───────────┐     │    │         │
│                                    ↓     ↓    ↓         │
│                              ┌─────────────────────┐    │
│                              │  Docker Network     │    │
│                              │  • postgres:5432    │    │
│                              │  • redis:6379       │    │
│                              │  • nginx:80         │    │
│                              └─────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

**Important**: Use the service name as the hostname!
- ✅ `postgres://postgres:5432`
- ❌ `postgres://localhost:5432`

---

## 💡 Pro Tips

### 1. Always Use Health Checks
```yaml
services:
  postgres:
    image: postgres:15
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```
Without health checks, your job might start before the service is ready!

### 2. Use Specific Versions
```yaml
services:
  postgres:
    image: postgres:15.3  # ✅ Specific version
    # image: postgres     # ❌ Might change unexpectedly
```

### 3. Map Ports (When Needed)
```yaml
services:
  postgres:
    image: postgres:15
    ports:
      - 5432:5432  # Only needed if job runs on runner directly
```
Not needed if your job runs in a container!

### 4. Environment Variables
```yaml
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_USER: testuser
      POSTGRES_PASSWORD: testpass
      POSTGRES_DB: testdb
```

### 5. Credentials Management
```yaml
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_PASSWORD: ${{ secrets.TEST_DB_PASSWORD }}
```
Use secrets for sensitive data!

---

## 🔍 Common Patterns

### Pattern 1: Database Testing
```yaml
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_PASSWORD: test
    options: --health-cmd pg_isready
```

### Pattern 2: Cache Testing
```yaml
services:
  redis:
    image: redis:7-alpine
    options: --health-cmd "redis-cli ping"
```

### Pattern 3: Message Queue Testing
```yaml
services:
  rabbitmq:
    image: rabbitmq:3-management
    env:
      RABBITMQ_DEFAULT_USER: guest
      RABBITMQ_DEFAULT_PASS: guest
```

### Pattern 4: Multi-Service Stack
```yaml
services:
  postgres:
    image: postgres:15
  redis:
    image: redis:7
  elasticsearch:
    image: elasticsearch:8.11.0
    env:
      discovery.type: single-node
```

---

## 🎨 Visual Learning

Open `visual-guide.html` for an interactive visual guide with:
- Animated diagrams
- Side-by-side comparisons
- Interactive examples
- Common pitfalls

---

## 📖 Learn Each Scenario

### Scenario 1: E-commerce API (PostgreSQL + Redis)
**What you'll learn:**
- Basic service container setup
- Database connection pooling
- Redis caching strategies
- Health check configuration

**Technologies**: FastAPI, PostgreSQL, Redis, pytest

### Scenario 2: Order Processing (MySQL + RabbitMQ)
**What you'll learn:**
- Message queue integration
- Async task processing
- Multiple service coordination
- Transaction testing

**Technologies**: Flask, MySQL, RabbitMQ, Celery

### Scenario 3: Microservices Architecture
**What you'll learn:**
- Service-to-service communication
- API gateway patterns
- Load balancing with Nginx
- Distributed testing

**Technologies**: Node.js, Express, MongoDB, Nginx

### Scenario 4: Search Service (MongoDB + Elasticsearch)
**What you'll learn:**
- Full-text search testing
- NoSQL + search engine combo
- Data indexing workflows
- Complex query testing

**Technologies**: Python, MongoDB, Elasticsearch

### Scenario 5: Full-Stack Application
**What you'll learn:**
- Frontend + Backend + Database testing
- E2E test automation
- Complete CI pipeline
- Production-like environment

**Technologies**: React, Node.js, PostgreSQL, Nginx

---

## 🐛 Troubleshooting

### Issue: "Connection refused"
**Cause**: Service not ready yet
**Solution**: Add health checks!

### Issue: "Can't resolve hostname"
**Cause**: Using `localhost` instead of service name
**Solution**: Use `postgres`, `redis`, etc. as hostname

### Issue: "Service container failed to start"
**Cause**: Port conflict or missing environment variables
**Solution**: Check logs, ensure required env vars are set

### Issue: "Tests pass locally but fail in CI"
**Cause**: Different network setup
**Solution**: Use same hostnames in both environments

---

## 📚 Additional Resources

- [GitHub Actions Service Containers Docs](https://docs.github.com/en/actions/using-containerized-services)
- [Docker Hub](https://hub.docker.com/) - Find service images
- Each scenario has its own detailed README

---

## 🎯 Next Steps

1. **Start with Scenario 1** (easiest)
2. **Try each scenario locally** with docker-compose
3. **Push to GitHub** and watch the workflow
4. **Experiment**: Add your own services
5. **Build your own**: Apply to your projects

---

## 💪 Practice Exercises

After completing the scenarios, try:

1. Add a caching layer to Scenario 1
2. Replace MySQL with PostgreSQL in Scenario 2
3. Add a second microservice to Scenario 3
4. Implement real-time updates in Scenario 4
5. Add authentication to Scenario 5

---

Ready to dive in? Start with Scenario 1! 🚀
