# Enterprise Business Analytics AI

> **Free, open-source AI-powered business intelligence platform** that transforms data into actionable insights through natural language.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## 🚀 Overview

This platform democratizes data analysis by allowing users to ask questions about their data in plain English. Powered by local LLMs (Ollama) and advanced SQL generation agents, it delivers enterprise-grade analytics, visualization, and strategic insights without sending your sensitive data to the cloud.

## ✨ Key Features

- **Natural Language Interface**: Chat with your data as you would with a senior data analyst.
- **Enterprise-Grade SQL Generation**: Advanced multi-agent pipeline for accurate, optimized SQL queries (DuckDB).
- **Automated Insights**: Generates executive summaries, key findings, and actionable recommendations.
- **Smart Visualization**: Automatically selects and renders the most effective charts (Bar, Line, Pie, Scatter, KPI).
- **Privacy-First**: Runs 100% locally using Docker and Ollama. No data leaves your infrastructure.
- **Multi-Format Support**: ingest CSV, Excel, and other structured data formats.
- **Modern Tech Stack**: Built with FastAPI, React 18, TypeScript, and Tailwind CSS.

## 📋 Prerequisites

- **Docker Desktop** (v4.0+)
- **Ollama** installed locally

## 🛠️ Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/BaddaVishweshwar/Conversational_AI_Data_Analyst_Agent.git
cd Conversational_AI_Data_Analyst_Agent
```

### 2. Configure Environment

```bash
cp .env.example .env
```
Edit `.env` to set your `SECRET_KEY` and preferred `OLLAMA_MODEL` (e.g., `llama3.1` or `mistral`).

### 3. Run with Docker

```bash
docker-compose up -d --build
```

Access the application:
- **Frontend**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000/docs](http://localhost:8000/docs)

## 🏗️ Architecture

The system utilizes a specialized multi-agent architecture:

1.  **Intent Classifier**: Determines if the user needs specific data, trends, or general insights.
2.  **Schema Analyzer**: Understands the structure and statistics of the uploaded dataset.
3.  **SQL Generator**: Writes high-performance DuckDB SQL queries.
4.  **SQL Validator**: Self-corrects queries if execution fails.
5.  **Visualization Selector**: Polices the best chart type for the data.
6.  **Insight Generator**: Synthesizes results into a business-readable narrative.

## 🛡️ Security

- **Self-Hosted**: Complete control over data residency.
- **No External Calls**: Does not rely on OpenAI or other public APIs for core analysis.

## 🤝 Contributing

Contributions are welcome! Please perform a pull request for any features or bug fixes.

## 📄 License

MIT License. See [LICENSE](LICENSE) for more information.
