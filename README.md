# Secure RAG Expert System (Fast Food Industry Analytics)

A modular RAG (Retrieval-Augmented Generation) prototype designed for secure industry data analysis. The system features a multi-layer semantic firewall and automated red-teaming to prevent prompt injections and system instructions leakage.

## ⛓️ The Philosophy: Taming the Wild LLM

At the core of this system is a **Dolphin-Llama3 (Uncensored)** model. By its nature, such a model is "wild" and unpredictable—it possesses vast knowledge but lacks corporate boundaries. 

My software acts as **"Logical Shackles"**:
*   **The Constraint:** Instead of letting the model roam free, we lock it within a strict professional framework.
*   **The Transformation:** Through the Semantic Firewall and RAG-grounding, we transform a volatile, uncensored AI into a precise, reliable corporate analyst. 
*   **The Result:** The system maintains the intelligence of an uncensored model while ensuring the safety and predictability required for enterprise use.


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
# Install dependencies and sync the virtual environment
uv sync
```


2. **Ensure Ollama is running and pull the models:**
   ```bash
   ollama pull dolphin-llama3:8b
   ```

3. **Initialize and Chat:**
   ```bash
   uv run main.py
   ```

## Security Benchmarking
To verify the integrity of the firewall, run the automated security suite:
```bash
uv run autotests.py
```
For dynamic stress-testing, use the Red Teaming module:
```bash
uv run hacker_bot.py
```

## Docker Deployment
Deploy the full stack using Docker Compose:
```bash
docker-compose up --build
```
