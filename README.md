# Local AI Newsletter Agent 🤖📰

A fully autonomous, privacy-first AI agent that runs locally on Windows. It wakes up daily, scrapes global AI news, clusters stories using machine learning, and uses a local LLM (Llama 3 via Ollama) to write and email a curated briefing.

## 🏗 Architecture

**Status:** Production (V3.6)  
**License:** MIT  

### The "Edge AI" Pipeline
This project avoids cloud APIs completely. All inference happens on the "Edge" (my local laptop) using the following pipeline:

1.  **Ingest:** `fetcher_v3.py` scrapes RSS feeds (TechCrunch, ArXiv, Reddit/LocalLlama).
2.  **Cluster:** `ai_processor_v3.py` uses `Sentence-Transformers` (all-MiniLM-L6-v2) to generate embeddings and Agglomerative Clustering to group duplicate stories.
3.  **Generate:** `writer_v3.py` sends clusters to **Ollama (Llama 3.1)** with strict system prompts to generate HTML summaries.
    * *Features:* Context-aware deduplication, Hallucination checks, and strict HTML formatting.
4.  **Dispatch:** `emailer_v3.py` handles SMTP delivery.

![Pipeline Visualization](https://mermaid.ink/img/pako:eNp1UktvwjAM_itWp24S-wA57DA2Tdo04tBceIhNoyZSkzhQG-K_L20pI3qJ7efnZzt5sFZZwQyWtb5VbA0HC8_SRF4XmziJ0_k8XsTTPJnm02S2iOMkTV9eF9N5lBbpZLGMcTqL0yR63iR4-T1w4ODg1sBf0EPHwR082K2D_eCOwQ-wVfAKm1qJ0kGl0Fp7lFwYl8J6v1E2oI8KjYYj0K-wV7D5f2tQO7iA1rZgB7R5e-O8Q63h2qB2UP8XfIRW2aOQk1L5uHAlO6m8D3Q0lFIIr-FwOFqJSttGudI2XFta9z_d4WwF2j1Mti41C1c7Jd3W0i3R_0x5U-hK25XW_V0z5Y1wJ2VbWvdyFcpW2I22S1f6H1PeKHeibEvrvv4H5c1g_wGkIsJ5?type=png)

## 🛠 Tech Stack

* **Core:** Python 3.11, PowerShell
* **ML & AI:** `sentence-transformers`, `scikit-learn`, `ollama` (Llama 3.1 8B)
* **Data:** SQLite, Feedparser
* **Orchestration:** Custom Python Daemon (`scheduler_service.py`)

## 🚀 How to Run

### Prerequisites
* Windows 10/11 (Wake Timers enabled)
* [Ollama](https://ollama.com/) installed and running (`ollama serve`)
* Python 3.11+

### Installation
1.  Clone the repo:
    ```bash
    git clone [https://github.com/BRRBlore/local-ai-newsletter.git](https://github.com/BRRBlore/local-ai-newsletter.git)
    cd local-ai-newsletter
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Configure Environment:
    Create a `.env` file (not shared) with:
    ```ini
    EMAIL_USER=your_email@gmail.com
    EMAIL_PASS=your_app_password
    EMAIL_RECIPIENT=target_email@gmail.com
    ```

### Usage
Run the persistent scheduler service:
```powershell
python src/scheduler_service.py