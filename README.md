# Policy Pilot

**Policy Pilot** helps you get information from **company policy documents** without reading every page. Your org's docs live in a **knowledge base**; you ask questions in plain language and get **Q&A-style answers** grounded in that content.

Under the hood it uses **RAG** (retrieval-augmented generation): policy text is indexed in a vector database, and the app retrieves the most relevant passages before generating an answer.

**Tools used:** Python, Weaviate, OpenAI (embeddings + chat), LangChain (`langchain-core`, `langchain-openai`, `langchain-text-splitters`), pypdf, Pydantic / pydantic-settings, FastAPI, Uvicorn, Streamlit, Docker Compose.

## Quick start

```bash
cp .env.example .env   # set OPENAI_API_KEY
python3 -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
docker compose up -d
python scripts/vectordb_cli.py create policy_documents
python scripts/ingest.py data/your-policy.pdf
streamlit run streamlit_app.py
```

Run commands from the **repository root** so `import policy_pilot` works.

MIT — see [LICENSE](LICENSE).
