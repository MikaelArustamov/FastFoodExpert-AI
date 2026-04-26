# Secure RAG Expert System (Fast Food Industry Analytics)

A modular RAG (Retrieval-Augmented Generation) prototype designed for secure industry data analysis. The system features a multi-layer semantic firewall and automated red-teaming to prevent prompt injections and system instructions leakage.

## Project Architecture

The system is decoupled into independent modules for scalability and maintainability:
* `main.py`: Core application logic, session management, and chat history persistence.
* `shield.py`: Security layer providing input normalization, de-obfuscation, and LLM-as-a-Judge auditing.
* `database.py`: Vector storage abstraction (ChromaDB) and embedding generation.
* `updater.py`: Autonomous data ingestion agent with anti-blocking mechanisms and timeout handling.
* `autotests.py`: Regression testing suite featuring 16+ pre-defined attack vectors.
* `hacker_bot.py`: AI-driven Red Teaming module for dynamic attack generation and stress-testing.

## Key Features

### 1. Semantic Firewall (LLM-as-a-Judge)
Unlike keyword-based filters, this system utilizes a local LLM to evaluate user intent. It effectively mitigates advanced threats including roleplay attacks, jailbreaking attempts, and secret instruction exfiltration.

### 2. Obfuscation Defense
Pre-processing pipeline designed to neutralize evasion techniques:
* Automatic Base64 payload detection and decoding.
* Zero-width character removal and Unicode normalization (NFKC).
* Pattern-based reconstruction of fragmented keywords (e.g., `H.a.c.k.`).

### 3. Resilient Ingestion
The ingestion agent (`updater.py`) implements request rotation and strict connection timeouts (via `requests`), ensuring stability when crawling high-latency or protected sources.

## Tech Stack
* **LLM Engine:** Ollama (Dolphin-Llama3:8b)
* **Embedding Model:** hf.co/CompendiumLabs/bge-base-en-v1.5-gguf
* **Vector DB:** ChromaDB
* **Data Extraction:** Trafilatura, Requests, DuckDuckGo Search

## Installation & Setup

1. **Clone and install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure Ollama is running and pull the models:**
   ```bash
   ollama pull dolphin-llama3:8b
   ```

3. **Initialize and Chat:**
   ```bash
   python main.py
   ```

## Security Benchmarking
To verify the integrity of the firewall, run the automated security suite:
```bash
python autotests.py
```
For dynamic stress-testing, use the Red Teaming module:
```bash
python hacker_bot.py
```

## Docker Deployment
Deploy the full stack using Docker Compose:
```bash
docker-compose up --build
```
