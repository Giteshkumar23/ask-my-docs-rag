# 📚 Ask My Docs

> **Turn your documents into an intelligent knowledge base.**

Ask My Docs is a **RAG-based document Q&A application** that allows users to upload documents and ask questions using natural language.

The system uses **hybrid search, reranking, and citation-based answers** to provide relevant and grounded responses.

---

## 🚀 Features

* 📄 Upload PDF, DOCX, TXT, Markdown, and CSV files
* 🔍 Hybrid search using **BM25 + Vector Search**
* 🔄 Reciprocal Rank Fusion (RRF)
* 🧠 Cross-Encoder reranking
* 📌 Citation-based answers
* 🛡️ Context-grounded responses
* 📁 Document collections
* 📊 RAG evaluation metrics
* 🐳 Docker & Docker Compose support
* ⚡ FastAPI backend
* 💻 React + TypeScript frontend

---

## 🔄 How It Works

```text
Upload Documents
       ↓
Document Processing
       ↓
Chunking & Embeddings
       ↓
BM25 + Vector Search
       ↓
RRF Fusion
       ↓
Cross-Encoder Reranking
       ↓
LLM Generation
       ↓
Answer + Citations
```

---

## 🛠️ Tech Stack

**Frontend**

* React
* TypeScript
* Vite
* Tailwind CSS

**Backend**

* Python
* FastAPI
* SQLAlchemy

**AI / RAG**

* BM25
* Vector Search
* Sentence Transformers
* Cross-Encoder
* LLM

**Database & Infrastructure**

* PostgreSQL
* pgvector
* Redis
* Docker
* GitHub Actions

---

## 📂 Project Structure

```text
ask-my-docs/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── rag/
│   │   └── services/
│   └── tests/
│
├── frontend/
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── hooks/
│       └── lib/
│
├── evaluation/
├── docker-compose.yml
├── Makefile
├── .env.example
└── README.md
```

---

## ⚙️ Installation

### Clone the repository

```bash
git clone https://github.com/Giteshkumar23/ask-my-docs-rag.git
cd ask-my-docs-rag
```

### Configure environment

```bash
cp .env.example .env
```

Add your required API keys and database configuration to `.env`.

### Run with Docker

```bash
docker compose up --build
```

---

## 🌐 Local URLs

**Frontend**

```text
http://localhost:3000
```

**Backend API**

```text
http://localhost:8000
```

**API Documentation**

```text
http://localhost:8000/docs
```

---

## 🧪 Testing

Run backend tests:

```bash
cd backend
pytest tests/ -v
```

---

## 📊 Evaluation

The project evaluates RAG quality using metrics such as:

* Recall@K
* Precision@K
* MRR
* Faithfulness
* Answer Relevance
* Citation Accuracy

---

## 🎯 Project Goal

The goal of **Ask My Docs** is to build a reliable document-based AI assistant that can retrieve relevant information from user documents and provide **grounded answers with citations**.

---

## 👨‍💻 Author

**Gitesh Kumar Patel**

B.Tech Information Technology

🐙 GitHub: https://github.com/Giteshkumar23

📧 Email: [giteshp321@gmail.com](mailto:giteshp321@gmail.com)

---

## ⭐ Support

If you like this project, consider giving the repository a ⭐.
