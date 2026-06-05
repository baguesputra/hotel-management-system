# Hotel Management System

Hotel Management System with background job processing using FastAPI, Celery, and Redis.

## Tech Stack

- **API**: FastAPI
- **Database**: PostgreSQL 16
- **ORM**: SQLAlchemy 2.0 + Alembic
- **Task Queue**: Celery 5
- **Message Broker**: Redis 7
- **Monitoring**: Flower
- **Container**: Docker + docker-compose

## Getting Started

### Prerequisites
- Docker
- Docker Compose

### Setup

1. Clone repository
   \`\`\`bash
   git clone https://github.com/USERNAME/hotel-management-system.git
   cd hotel-management-system
   \`\`\`

2. Copy environment file
   \`\`\`bash
   cp .env.example .env
   \`\`\`

3. Run services
   \`\`\`bash
   docker-compose up --build
   \`\`\`

## Services

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Flower | http://localhost:5555 |