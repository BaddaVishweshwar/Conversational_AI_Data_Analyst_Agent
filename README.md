# Business Analytics AI Platform

> **Free, open-source AI-powered business analytics platform** that democratizes data analysis through natural language queries.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## 🚀 Features

- **Natural Language Queries**: Ask questions about your data in plain English
- **AI-Powered Insights**: Automatic SQL generation and business insights using Ollama
- **Beautiful Visualizations**: Interactive charts (line, bar, pie, scatter)
- **Multi-Format Support**: Upload CSV and Excel files
- **100% Free**: No paid APIs, fully self-hostable
- **Modern UI**: Built with React, TypeScript, and Tailwind CSS

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** and **Docker Compose** (v2.0+)
- **Ollama** with a model installed (recommended: `llama3.1:8b` or `mistral:7b`)

### Installing Ollama

1. Install Ollama from [ollama.ai](https://ollama.ai)
2. Pull a model:
   ```bash
   ollama pull llama3.1:8b
   # or
   ollama pull mistral:7b
   ```
3. Verify Ollama is running:
   ```bash
   ollama list
   ```

## 🛠️ Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd AI\ Data
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and update the following:
- `SECRET_KEY`: Generate a secure random string
- `OLLAMA_MODEL`: Set to your installed model (e.g., `llama3.1:8b`)

### 3. Start the Application

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database (port 5432)
- Redis (port 6379)
- FastAPI backend (port 8000)
- React frontend (port 3000)

### 4. Access the Application

Open your browser and navigate to:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs (Swagger UI)

### 5. Create an Account

1. Click "Sign up" on the login page
2. Enter your email, username, and password
3. You'll be automatically logged in

## 📊 Usage Guide

### Uploading Data

1. Navigate to **Datasets** page
2. Drag and drop a CSV or Excel file (or click to browse)
3. Wait for the file to be processed
4. View dataset details (rows, columns, schema)

### Asking Questions

1. Go to **Analytics** page
2. Select a dataset from the dropdown
3. Type a natural language question, for example:
   - "What are the top 10 rows?"
   - "Show me summary statistics"
   - "What are the trends over time?"
   - "Which products have the highest revenue?"
4. View the generated SQL, results, and AI insights

### Example Queries

```
- "What are the top 5 products by sales?"
- "Show me revenue trends by month"
- "Which customers made the most purchases?"
- "What's the average order value?"
- "Show me all orders above $1000"
```

## 🏗️ Architecture

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  React Frontend │
│  (TypeScript)   │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│   FastAPI       │
│   Backend       │
└────┬────────┬───┘
     │        │
     ▼        ▼
┌────────┐  ┌──────────┐
│Postgres│  │  Ollama  │
│        │  │  (LLM)   │
└────────┘  └──────────┘
```

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for database operations
- **Pandas**: Data processing and analysis
- **DuckDB**: In-memory SQL execution
- **Ollama**: Local LLM integration

### Frontend
- **React 18**: UI framework
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **shadcn/ui**: UI components
- **Recharts**: Data visualization
- **Zustand**: State management

### Infrastructure
- **PostgreSQL**: Metadata storage
- **Redis**: Caching (future use)
- **Docker**: Containerization
- **Nginx**: Reverse proxy

## 🔧 Development

### Running Locally (Without Docker)

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Project Structure

```
AI Data/
├── backend/
│   ├── app/
│   │   ├── routes/          # API endpoints
│   │   ├── services/        # Business logic
│   │   ├── models.py        # Database models
│   │   ├── config.py        # Configuration
│   │   └── database.py      # Database setup
│   ├── main.py              # FastAPI app
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/           # React pages
│   │   ├── components/      # UI components
│   │   ├── lib/             # Utilities
│   │   └── store/           # State management
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

## 🐛 Troubleshooting

### Ollama Connection Issues

If you see "Ollama not available" errors:

1. Ensure Ollama is running: `ollama list`
2. Check the model is installed: `ollama pull llama3.1:8b`
3. Verify `OLLAMA_HOST` in `.env` is correct
4. For Docker on Mac/Windows, use `http://host.docker.internal:11434`

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps

# View logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Frontend Not Loading

```bash
# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend

# Check logs
docker-compose logs frontend
```

## 📝 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 Security Notes

- Change the `SECRET_KEY` in production
- Use strong passwords for database
- Enable HTTPS in production
- Implement rate limiting for API endpoints
- Regularly update dependencies

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai) for local LLM support
- [FastAPI](https://fastapi.tiangolo.com) for the amazing Python framework
- [shadcn/ui](https://ui.shadcn.com) for beautiful UI components
- [Recharts](https://recharts.org) for data visualization

## 📧 Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section

---

**Built with ❤️ for the open-source community**
