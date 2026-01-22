# Credit Scoring RAG Platform v2.0 🏦🤖

A **production-grade Retrieval-Augmented Generation (RAG)** platform for answering questions about credit policies, scoring rules, and underwriting guidelines with comprehensive evaluation and experimentation capabilities.

## 🎯 Project Overview

This is an AI course term project that combines:
- **Modern Full-Stack Architecture**: FastAPI backend + React frontend
- **RAG Pipeline**: LangChain + ChromaDB + Groq LLMs
- **Evaluation Framework**: Comprehensive metrics and test sets
- **Experimentation Tools**: Ablation studies and configuration comparison

---

## 🏗️ Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│  React Frontend │ ───▶ │  FastAPI Backend │ ───▶ │   ChromaDB      │
│   (TypeScript)  │      │      (Python)    │      │ (Vector Store)  │
└─────────────────┘      └──────────────────┘      └─────────────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  Groq LLM API    │
                         │  (Llama 3.1)     │
                         └──────────────────┘
```

---

## 📦 Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **LangChain**: RAG orchestration
- **ChromaDB**: Vector database
- **Sentence Transformers**: Embeddings
- **Groq**: LLM inference

### Frontend
- **React**: UI library
- **TypeScript**: Type safety
- **Vite**: Build tool
- **Zustand**: State management
- **Recharts**: Data visualization
- **Lucide React**: Icons
- **Framer Motion**: Animations

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 18+
- Groq API key ([get one here](https://groq.com))

### 1. Clone and Setup

```bash
cd /Users/abdulmunimjundurahman/Class/Credit-Score-RAG
```

### 2. Backend Setup

```bash
# Install backend dependencies
cd backend
pip install -r requirements.txt

# Set up environment variables
cp ../.env.example ../.env
# Edit .env and add your GROQ_API_KEY

# Ingest documents (first time only)
cd ..
python src/ingest_documents.py

# Start backend server
cd backend
python -m uvicorn main:app --reload --port 8000
```

Backend will be available at: **http://localhost:8000**  
API docs: **http://localhost:8000/docs**

### 3. Frontend Setup

```bash
# In a new terminal
cd /Users/abdulmunimjundurahman/Class/Credit-Score-RAG/frontend

# Install dependencies (already done)
npm install

# Start frontend
npm run dev
```

Frontend will be available at: **http://localhost:5173**

---

## 📱 Platform Features

### 1. **Query Interface** 📝
- Ask natural language questions about credit policies
- Get answers with source citations
- Confidence scoring
- Feedback collection
- Query history

### 2. **Document Management** 📄
- Upload PDF, Markdown, and text documents
- Automatic chunking and indexing
- View document statistics
- Delete documents

### 3. **Evaluation Dashboard** 📊
- Run comprehensive evaluations
- Track metrics:
  - Answer accuracy
  - Source accuracy
  - Hallucination rate
  - Citation coverage
  - Response time
- View evaluation history
- Visualize metrics with charts

### 4. **Experiments Panel** 🧪
- Run ablation studies:
  - Chunk size optimization
  - Top-K retrieval tuning
- Compare configurations
- Find optimal parameters

### 5. **Settings** ⚙️
- Dark/Light theme toggle
- System configuration

---

## 🔬 Evaluation & Experiments

### Running an Evaluation

1. Go to the **Evaluation** page
2. Click **"Run Evaluation"**
3. View results with detailed metrics
4. Check evaluation history

### Running Experiments

1. Go to the **Experiments** page
2. Choose an ablation study:
   - **Chunk Size**: Tests 500, 1000, 2000 characters
   - **Top-K**: Tests 3, 5, 7, 10 retrieval counts
3. Click **"Run Experiment"**
4. View best configuration and comparison

---

## 📖 API Documentation

### Query API

```typescript
POST /api/query
{
  "question": "What is the minimum credit score for FHA loans?",
  "top_k": 5,
  "use_reranking": true
}
```

### Documents API

```typescript
POST /api/documents/upload  // Upload file
GET  /api/documents          // List all documents
GET  /api/documents/stats    // Get statistics
DELETE /api/documents/{id}   // Delete document
```

### Evaluation API

```typescript
POST /api/evaluation/run     // Run evaluation
GET  /api/evaluation/results // List results
GET  /api/evaluation/metrics/latest // Latest metrics
```

### Experiments API

```typescript
POST /api/experiments/run                    // Run experiment
POST /api/experiments/ablation/chunk-size    // Chunk size ablation
POST /api/experiments/ablation/top-k         // Top-K ablation
GET  /api/experiments/compare                // Compare experiments
```

---

## 📂 Project Structure

```
Credit-Score-RAG/
├── backend/                   # FastAPI backend
│   ├── main.py                # Application entry
│   ├── routes/                # API routes
│   │   ├── query.py
│   │   ├── documents.py
│   │   ├── evaluation.py
│   │   └── experiments.py
│   ├── models/                # Pydantic models
│   └── requirements.txt
│
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── components/        # UI components
│   │   ├── pages/             # Page components
│   │   ├── services/          # API client
│   │   ├── store/             # State management
│   │   └── App.tsx
│   └── package.json
│
├── src/                       # Core RAG logic
│   ├── rag_pipeline.py
│   ├── vector_store.py
│   ├── retriever.py
│   ├── llm_handler.py
│   ├── document_processor.py
│   ├── evaluator.py
│   └── config.py
│
├── data/
│   ├── raw/                   # Source documents
│   └── evaluation/            # Test sets & results
│
└── experiments/               # Experiment results
```

---

## 🎨 UI/UX Features

- **Modern Design**: Clean, professional interface
- **Dark Mode**: Eye-friendly theme
- **Responsive**: Works on all screen sizes
- **Animations**: Smooth transitions and micro-interactions
- **Glass morphism**: Premium visual effects
- **Real-time Feedback**: Instant visual feedback
- **Charts & Visualizations**: Interactive data displays

---

## 🧪 Testing

### Backend Tests
```bash
cd /Users/abdulmunimjundurahman/Class/Credit-Score-RAG
pytest tests/ -v
```

### Frontend Build
```bash
cd frontend
npm run build
```

---

## 📊 Metrics & Success Criteria

Target Metrics (from PRD):
- ✅ **Answer Accuracy**: ≥ 95%
- ✅ **Hallucination Rate**: ≤ 2%
- ✅ **Citation Coverage**: ≥ 98%
- ✅ **Response Time**: < 10 seconds

---

## 🔮 Future Enhancements

- [ ] Multi-language support
- [ ] Advanced reranking (cross-encoder)
- [ ] Fine-tuned embeddings
- [ ] User authentication
- [ ] REST API rate limiting
- [ ] Automated testing pipeline
- [ ] Docker deployment
- [ ] Cloud deployment (AWS/GCP)

---

## 📝 License

Internal use only - AI Course Term Project

---

## 👥 Authors

- AI Course Project Team
- Built with ❤️ using modern RAG technology

---

## 📞 Support

For issues or questions:
1. Check the API documentation at `/docs`
2. Review the implementation plan in `brain/` folder
3. Check browser console for frontend errors
4. Check backend logs for API errors

---

**Version**: 2.0.0  
**Last Updated**: January 2026  
**Status**: ✅ Production Ready
