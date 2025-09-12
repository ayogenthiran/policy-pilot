# Policy Pilot

A comprehensive RAG (Retrieval-Augmented Generation) system for policy document analysis and intelligent query answering. Built with FastAPI, OpenSearch, and OpenAI, Policy Pilot enables organizations to efficiently search, analyze, and extract insights from policy documents.

## 🚀 Features

- **Document Processing**: Support for multiple document formats (PDF, DOCX, TXT, images with OCR)
- **Intelligent Search**: Semantic and keyword-based search capabilities
- **RAG Pipeline**: Advanced retrieval-augmented generation for accurate answers
- **Real-time Health Monitoring**: Comprehensive health checks and system monitoring
- **Scalable Architecture**: Docker-based deployment with OpenSearch backend
- **RESTful API**: Well-documented API with OpenAPI/Swagger documentation
- **Modern Frontend**: Next.js-based dashboard with authentication

## 💼 Business Use Cases

### 1. Financial Compliance Document Q&A
**FINTRAC Assessment Manual Analysis**

Policy Pilot excels at helping financial institutions understand complex compliance requirements. The system can process and analyze the [FINTRAC Assessment Manual](https://fintrac-canafe.canada.ca/guidance-directives/exam-examen/cam/cams-eng.pdf) to help banks:

- **Understand Assessment Processes**: Navigate complex compliance assessment procedures
- **Avoid Costly Failures**: Get instant answers about compliance requirements and criteria
- **Multi-layered Analysis**: Handle documents with complex hierarchical structures
- **Risk Mitigation**: Quickly identify potential compliance gaps and requirements

**Example Queries:**
- "What are the key requirements for customer due diligence in the assessment process?"
- "How should banks handle suspicious transaction reporting according to FINTRAC guidelines?"
- "What are the specific criteria for risk assessment in different business sectors?"
- "What documentation is required for high-risk customer assessments?"
- "How should financial institutions handle politically exposed persons (PEPs)?"

**Document Features Showcased:**
- **Complex Hierarchical Structure**: Multi-level document organization with sections, subsections, and appendices
- **Regulatory Language**: Technical compliance terminology requiring precise understanding
- **Cross-references**: Interconnected concepts and requirements throughout the document
- **Visual Elements**: Charts, tables, and diagrams that require OCR processing
- **Real-world Application**: Actual regulatory document used by financial institutions

### 2. Document Image Processing Challenge
**Advanced OCR and Visual Content Analysis**

One of the most challenging aspects of scaling document processing systems is handling images within documents. Policy Pilot addresses this through:

- **OCR Integration**: Extract text from images and diagrams within documents
- **Visual Content Understanding**: Process charts, tables, and graphical elements
- **Multi-modal Analysis**: Combine text and visual information for comprehensive understanding
- **Scalable Image Processing**: Optimized for handling large volumes of image-heavy documents

This capability is particularly valuable for:
- Technical manuals with diagrams and flowcharts
- Financial reports with charts and graphs
- Legal documents with visual evidence
- Compliance documents with complex visual layouts

**Technical Innovation**: Our system demonstrates advanced problem-solving skills by handling the complexity of multi-modal document processing, making it a showcase of technical excellence in the RAG domain.

### 3. Technical Challenges & Solutions

**Image Processing in Documents**

Handling images within documents presents unique challenges that Policy Pilot addresses through innovative solutions:

- **OCR Integration**: Advanced optical character recognition for text extraction from images
- **Layout Analysis**: Understanding document structure and visual hierarchy
- **Multi-modal Embeddings**: Combining text and visual features for comprehensive search
- **Scalable Processing**: Optimized pipelines for handling image-heavy documents at scale

**Why This Matters:**
- Many compliance documents contain critical information in charts, diagrams, and visual formats
- Traditional text-only RAG systems miss important visual context
- Our solution ensures no information is lost, regardless of format
- Demonstrates technical depth and problem-solving capabilities

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   OpenSearch    │
│   (Next.js)     │◄──►│   Backend       │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   OpenAI API    │
                       │   (GPT Models)  │
                       └─────────────────┘
```

## 📋 Prerequisites

- Python 3.9+
- Node.js 18+
- Docker & Docker Compose
- OpenAI API Key

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/policy-pilot.git
cd policy-pilot
```

### 2. Environment Setup

Create a `.env` file in the root directory:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# OpenSearch Configuration
OPENSEARCH_URL=http://localhost:9200

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "http://localhost:3001"]

# Logging
LOG_LEVEL=INFO
```

### 3. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or using pip-tools
pip install -e .
```

### 4. Frontend Setup

```bash
# Install Node.js dependencies
npm install

# Build the frontend
npm run build
```

### 5. Database Setup

```bash
# Start OpenSearch with Docker Compose
docker-compose up -d opensearch opensearch-dashboards

# Wait for OpenSearch to be ready (check health)
curl http://localhost:9200/_cluster/health
```

## 🚀 Quick Start

### Development Mode

```bash
# Start all services
docker-compose up -d

# Or start individual services
docker-compose up -d opensearch
python src/main.py
npm run dev
```

### Testing with Sample Data

The repository includes a sample FINTRAC Assessment Manual document for testing:

```bash
# Upload the sample document
curl -X POST "http://localhost:8000/api/upload-document" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/cams-eng.pdf"

# Test compliance queries
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the key requirements for customer due diligence in the FINTRAC assessment process?",
    "use_rag": true,
    "search_type": "semantic",
    "top_k": 5
  }'
```

### Production Mode

```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d

# Or use the deployment script
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

## 📚 API Documentation

### Base URL
- Development: `http://localhost:8000`
- Production: `https://api.policypilot.ai`

### Interactive Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Endpoints

#### Health Check
```bash
GET /api/health
```

#### Document Upload
```bash
POST /api/upload-document
Content-Type: multipart/form-data

# Form data:
# file: [document file]
```

#### Query Documents
```bash
POST /api/query
Content-Type: application/json

{
  "question": "What is the company's remote work policy?",
  "use_rag": true,
  "search_type": "semantic",
  "top_k": 5
}
```

#### Search Documents
```bash
POST /api/search
Content-Type: application/json

{
  "query": "remote work policy",
  "search_type": "semantic",
  "top_k": 10,
  "min_score": 0.7
}
```

### Example Requests

#### Upload a Document
```bash
curl -X POST "http://localhost:8000/api/upload-document" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@policy_document.pdf"
```

#### Query the System
```bash
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the key points about data privacy?",
    "use_rag": true,
    "search_type": "semantic",
    "top_k": 5
  }'
```

#### Simple Query (GET)
```bash
curl "http://localhost:8000/api/query/simple?q=What is the refund policy?&use_rag=true&top_k=3"
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key | - | Yes |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4o-mini` | No |
| `OPENSEARCH_URL` | OpenSearch connection URL | `http://localhost:9200` | No |
| `API_HOST` | API server host | `0.0.0.0` | No |
| `API_PORT` | API server port | `8000` | No |
| `ENVIRONMENT` | Environment (development/production) | `development` | No |
| `CORS_ORIGINS` | Allowed CORS origins | `["http://localhost:3000"]` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |

### OpenSearch Configuration

The system uses OpenSearch for document storage and retrieval. Key configuration:

- **Index Name**: `policy_documents`
- **Embedding Field**: `content_embedding`
- **Text Field**: `content`
- **Metadata Fields**: `document_name`, `page_number`, `chunk_id`

## 🐳 Docker Deployment

### Development
```bash
docker-compose up -d
```

### Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Services

- **policy-pilot-api**: Main FastAPI application
- **opensearch**: OpenSearch database
- **opensearch-dashboards**: OpenSearch management UI
- **redis**: Caching service (optional)

### Volumes

- `opensearch_data`: OpenSearch data persistence
- `redis_data`: Redis data persistence
- `./uploads`: Document uploads
- `./logs`: Application logs

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_rag_service.py
```

### Test Coverage
```bash
# Generate coverage report
pytest --cov=src --cov-report=html --cov-report=xml

# View coverage report
open htmlcov/index.html
```

## 📊 Monitoring

### Health Checks

- **Liveness**: `GET /api/health/live`
- **Readiness**: `GET /api/health/ready`
- **System Health**: `GET /api/health`
- **OpenSearch Health**: `GET /api/health/opensearch`

### Logging

Logs are written to:
- Console output (development)
- `logs/policy_pilot.log` (production)
- Docker logs: `docker-compose logs policy-pilot-api`

### Metrics

- Document processing statistics
- Query response times
- System resource usage
- Error rates and types

## 🔍 Troubleshooting

### Common Issues

#### 1. OpenSearch Connection Failed
```bash
# Check if OpenSearch is running
docker-compose ps opensearch

# Check OpenSearch health
curl http://localhost:9200/_cluster/health

# Restart OpenSearch
docker-compose restart opensearch
```

#### 2. OpenAI API Errors
```bash
# Check API key
echo $OPENAI_API_KEY

# Test API connection
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

#### 3. Document Upload Fails
```bash
# Check file permissions
ls -la uploads/

# Check disk space
df -h

# Check logs
docker-compose logs policy-pilot-api
```

#### 4. Frontend Not Loading
```bash
# Check if frontend is built
ls -la .next/

# Rebuild frontend
npm run build

# Check CORS configuration
curl -H "Origin: http://localhost:3000" \
  http://localhost:8000/api/health
```

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python src/main.py
```

### Performance Issues

1. **Slow Query Response**:
   - Check OpenSearch performance
   - Monitor OpenAI API rate limits
   - Optimize embedding model

2. **High Memory Usage**:
   - Reduce batch sizes
   - Optimize document chunking
   - Monitor OpenSearch heap usage

3. **Slow Document Processing**:
   - Check file I/O performance
   - Monitor CPU usage
   - Optimize text extraction

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run tests: `pytest`
5. Commit your changes: `git commit -m "Add feature"`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

### Development Guidelines

- Follow PEP 8 for Python code
- Use type hints
- Write comprehensive tests
- Update documentation
- Follow conventional commits

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-username/policy-pilot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/policy-pilot/discussions)
- **Email**: support@policypilot.ai

## 🗺️ Roadmap

- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] API rate limiting
- [ ] User authentication and authorization
- [ ] Document versioning
- [ ] Advanced search filters
- [ ] Export functionality
- [ ] Mobile app

## 🙏 Acknowledgments

- OpenAI for GPT models
- OpenSearch for search capabilities
- FastAPI for the web framework
- Next.js for the frontend framework
- The open-source community for various libraries and tools