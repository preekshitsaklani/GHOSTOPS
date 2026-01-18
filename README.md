# 🎯 ClarityOS - AI-Powered Mentor Matching Platform

<div align="center">

![ClarityOS](https://img.shields.io/badge/ClarityOS-v1.0-2563EB?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Neo4j](https://img.shields.io/badge/Neo4j-5.0+-008CC1?style=for-the-badge&logo=neo4j&logoColor=white)
![NVIDIA](https://img.shields.io/badge/NVIDIA_NIM-LLM-76B900?style=for-the-badge&logo=nvidia&logoColor=white)

**Transform advice into outcomes. Intelligent mentor matching powered by AI.**

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [API Reference](#-api-reference) • [Contributing](#-contributing)

</div>

---

## 🚀 Features

### 🤖 AI-Powered Diagnosis
- **Intelligent Conversation**: AI asks up to 7 focused questions to deeply understand your challenge
- **Category Detection**: Automatically classifies problems into Fundraising, Growth, or Product-Market Fit
- **File Analysis**: Upload PDFs, DOCX, CSV, XLSX for AI to analyze and incorporate insights

### 📄 Addressible Document Generation
- **Mentor Context Pack**: Auto-generates a `.docx` document with:
  - Problem summary
  - Key insights extracted from conversation
  - Metrics and constraints
  - Prepared questions for the mentor
- **Iterative Review**: Review and request changes before finalizing
- **Persistent Storage**: Saves to both Neo4j and local JSON files

### 🎯 Smart Mentor Matching
- **GraphRAG**: Knowledge graph-based retrieval for precise mentor matching
- **Outcome-Based**: Matches based on proven outcomes, not just keywords
- **Why This Mentor**: Hover tooltips explain why each mentor is recommended

### 💬 Embeddable Widget
- **Zero-Config Integration**: Single `<script>` tag to add to any website
- **File Upload UI**: Drag-and-drop or click to upload documents
- **Rich Mentor Cards**: Clickable cards with bio, outcomes, and booking link

---

## 📋 Quick Start

### Prerequisites

- Python 3.9+
- Neo4j Database (local or cloud)
- NVIDIA NIM API key

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/clarityos.git
cd clarityos
```

### 2. Set Up Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env.local
```

Edit `.env.local` with your credentials:

```env
# Neo4j Database
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here

# NVIDIA NIM API
NVIDIA_API_KEY=nvapi-your_api_key_here
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL_ID=openai/gpt-oss-20b
```

### 5. Seed the Database (Optional)

```bash
python scraper.py
```

### 6. Start the Server

```bash
uvicorn backend:app --host 0.0.0.0 --port 8000 --reload
```

### 7. Open the Demo

Open `index.html` in your browser, or navigate to:
```
http://localhost:8000/docs  # API Documentation
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Widget                           │
│                     (widgest_loader.js)                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────────┐ │
│  │  Chat   │  │ Upload  │  │ Mentor  │  │ Document Preview    │ │
│  │   UI    │  │  Files  │  │ Cards   │  │ + Review Buttons    │ │
│  └────┬────┘  └────┬────┘  └────┬────┘  └──────────┬──────────┘ │
└───────┼────────────┼────────────┼───────────────────┼───────────┘
        │            │            │                   │
        ▼            ▼            ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                             │
│                        (backend.py)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ /chat/message│  │   /upload    │  │   /generate-pdf        │ │
│  │   (LLM + RAG)│  │(File Parser) │  │   (DOCX Generator)     │ │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬────────────┘ │
└─────────┼─────────────────┼──────────────────────┼──────────────┘
          │                 │                      │
          ▼                 ▼                      ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐
│   NVIDIA NIM    │  │   Neo4j Graph   │  │ File System         │
│   (LLM API)     │  │   (Mentors +    │  │ (generated_docs/    │
│                 │  │    Documents)   │  │  data_extracted/)   │
└─────────────────┘  └─────────────────┘  └─────────────────────┘
```

### Key Files

| File | Purpose |
|------|---------|
| `backend.py` | FastAPI server with all endpoints |
| `database.py` | Neo4j connection and queries |
| `document_generator.py` | DOCX file creation |
| `file_processor.py` | Text extraction from various file types |
| `widgest_loader.js` | Frontend widget (inject into any site) |
| `scraper.py` | Seed mentor data into the database |
| `index.html` | Demo page for testing |

---

## 📡 API Reference

### `POST /chat/message`

Main conversation endpoint with AI diagnosis and mentor matching.

**Request:**
```json
{
  "history": [
    {"role": "user", "content": "I need help with fundraising"}
  ],
  "file_context": "optional extracted text from uploaded file"
}
```

**Response:**
```json
{
  "reply": "AI response text",
  "cards": [{"name": "Mentor Name", "bio": "...", "outcomes": "...", "why_this_mentor": "..."}],
  "conversation_state": "gathering_info | reviewing_doc | finalized",
  "document_preview": "Text preview of generated document",
  "document_saved": true,
  "document_path": "/path/to/addressible.docx"
}
```

### `POST /upload`

Upload and extract text from files.

**Request:** `multipart/form-data` with file

**Response:**
```json
{
  "filename": "document.pdf",
  "content": "Extracted text...",
  "status": "success",
  "saved_to": {
    "neo4j_doc_id": "abc123",
    "json_path": "/path/to/file.json"
  }
}
```

### `POST /session/analyze`

Analyze meeting transcripts for action items.

**Request:**
```json
{
  "transcript": "Meeting transcript text..."
}
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEO4J_URI` | Neo4j connection URI | `bolt://localhost:7687` |
| `NEO4J_USER` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | (required) |
| `NVIDIA_API_KEY` | NVIDIA NIM API key | (required) |
| `NVIDIA_BASE_URL` | NVIDIA API base URL | `https://integrate.api.nvidia.com/v1` |
| `NVIDIA_MODEL_ID` | LLM model to use | `openai/gpt-oss-20b` |

### Supported File Types

- **Documents**: PDF, DOCX, DOC, TXT, MD
- **Data**: CSV, XLSX, XLS
- **Presentations**: PPT, PPTX

---

## 🧪 Testing

### Run the Demo

1. Start the server: `uvicorn backend:app --reload`
2. Open `index.html` in a browser
3. Click the blue chat widget in the bottom-right
4. Have a conversation about your startup challenge
5. After 3-7 messages, you'll see the document preview
6. Say "looks good" to finalize and see mentor recommendations

### Sample Conversation

```
User: I'm building a D2C skincare brand
AI: What's your current MRR and main challenge?

User: $30k MRR, struggling with 40% churn
AI: What have you tried to reduce churn?

User: Email marketing but it's not working
AI: I have enough information! Here's your Mentor Context Pack...
     [Document Preview]
     Does this look good?

User: Looks good!
AI: ✅ Document saved! Here are your recommended mentors...
     [Mentor Cards with hover tooltips]
```

---

## 📁 Project Structure

```
clarityos/
├── backend.py              # FastAPI server
├── database.py             # Neo4j connection
├── document_generator.py   # DOCX generator
├── file_processor.py       # File text extraction
├── scraper.py              # Mentor data seeder
├── widgest_loader.js       # Frontend widget
├── index.html              # Demo page
├── mentor_knowledge_base.json
├── requirements.txt
├── .env.example            # Template for env vars
├── .env.local              # Your secrets (gitignored)
├── .gitignore
└── generated_documents/    # Saved DOCX files
```

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **NVIDIA NIM** for LLM API access
- **Neo4j** for graph database
- **FastAPI** for the backend framework
- **ExpertBells** for the mentor marketplace concept

---

<div align="center">

**Built with ❤️ for the FOCOS Hackathon**

[⬆ Back to Top](#-clarityos---ai-powered-mentor-matching-platform)

</div>
