# ApexIQ-Automotive-Intelligence

A full-stack AI-powered technical assistant and document management platform for automotive brochures, specs, and comparisons. Built with a **FastAPI Python backend**, **PostgreSQL + pgvector** (Supabase or direct PostgreSQL connection), intelligent PDF processing, and a multi-provider RAG pipeline.

---

## 📁 Project Structure

```
.
├── brochures/                               # Add authorized brochure PDFs locally; not committed
├── backend/
│   ├── app/
│   │   ├── api/                             # REST API endpoints
│   │   │   ├── documents.py                 # Brochure upload & batch processing
│   │   │   ├── chat.py                      # RAG Q&A with source citations
│   │   │   ├── compare.py                   # Multi-car & variant comparison
│   │   │   └── vehicles.py                  # Extracted vehicle profiles
│   │   ├── core/
│   │   │   └── config.py                    # App configuration & settings
│   │   ├── db/
│   │   │   ├── supabase_client.py           # Supabase client + local fallback
│   │   │   └── postgres_client.py           # Direct PostgreSQL storage
│   │   ├── services/
│   │   │   ├── pdf_extractor.py             # PDF text, table & metadata extractor
│   │   │   ├── chunker.py                   # Semantic chunking with page metadata
│   │   │   ├── embeddings.py                # Vector embeddings (OpenAI / Gemini / Mock)
│   │   │   ├── rag_service.py               # Cross-brochure RAG and cited comparisons
│   │   │   └── comparison_service.py        # Technical side-by-side comparison engine
│   │   └── main.py                          # FastAPI server entrypoint
│   ├── schema.sql                           # PostgreSQL + pgvector schema
│   ├── requirements.txt                     # Backend Python dependencies
│   ├── .env.example                         # Environment configuration template
│   └── test_*.py                            # Backend regression tests
├── frontend/
│   ├── src/
│   │   └── services/api.js                  # Frontend API client
│   ├── package.json                         # Vite/React dependencies and scripts
│   └── .env.example                         # Frontend API URL template
└── README.md
```

---

## 🗄️ Database Setup (PostgreSQL + pgvector)

1. Connect to your PostgreSQL database using the same role the backend will use, then run [`backend/schema.sql`](backend/schema.sql). It creates the `pgvector` extension, application tables, and cosine-search function. The database server must have pgvector available, and that role must have permission to create extensions/tables.
2. Configure **one** database connection in the ignored local file `backend/.env`:

   For a direct PostgreSQL connection:
   ```ini
   DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require
   ```

   For the Supabase REST API instead:
   ```ini
   SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
   SUPABASE_KEY=YOUR_SERVER_SIDE_SERVICE_ROLE_SECRET
   ```
   `DATABASE_URL` takes precedence when both configurations are present. Keep database credentials out of frontend variables and source control. URL-encode reserved characters in a connection-string password.
3. Keep the existing LLM settings in `backend/.env` and restart the backend. Open `http://127.0.0.1:8000/`; `storage_backend` should report `postgresql` or `supabase`, as configured.

The schema creates:
- `documents` for brochure metadata and processing status
- `vehicles` and `vehicle_variants` for extracted vehicle details
- `document_chunks` for brochure text, metadata, and `vector(1536)` embeddings
- `chat_sessions` and `chat_messages` for conversations and citations
- `match_document_chunks()` and a pgvector HNSW index for similarity search

### Put brochures into the database

If present, `backend/data/vector_cache.json` is only a local retrieval cache; it is not automatically copied to Supabase. After configuring Supabase and confirming `storage_backend: supabase`, run this from the project root to populate it from the PDFs in `brochures\`:

```powershell
python backend\ingest.py
```

This inserts each PDF's document row, vehicle row, chunks, and embeddings into the configured PostgreSQL database, and skips filenames already indexed there. For subsequent brochures, use the Admin page to upload each PDF; the background indexing pipeline writes its extracted records to the database. Using the Admin page to delete a brochure also removes its related database rows.

PDF binary files themselves remain on the backend machine (`brochures\` or `backend\uploads\`). PostgreSQL stores the document record and local `file_path`, not the PDF bytes; Supabase Storage is not configured for PDF binaries.

### View and verify stored data

In the Supabase Dashboard, open **Table Editor** and choose `vehicles`, `documents`, `document_chunks`, `chat_sessions`, or `chat_messages`. You can also use **SQL Editor** to inspect rows:

```sql
select id, brand, model, model_year
from public.vehicles
order by brand, model;

select id, filename, status, page_count, created_at
from public.documents
order by created_at desc;

select c.document_id, d.filename, c.vehicle_id, c.chunk_index,
       c.metadata ->> 'page' as page, left(c.content, 200) as text_preview,
       vector_dims(c.embedding) as embedding_dimensions
from public.document_chunks c
join public.documents d on d.id = c.document_id
order by d.filename, c.chunk_index;

select s.id as session_id, s.title, m.role, m.content, m.sources, m.created_at
from public.chat_sessions s
join public.chat_messages m on m.session_id = s.id
order by m.created_at desc;
```

Each GearGuide conversation creates a session and stores its user/assistant messages and citations in these tables. `document_chunks.embedding` is the pgvector value used by `match_document_chunks()` during retrieval.

### Local fallback

When the backend root endpoint reports `storage_backend: local_fallback`, requests are not being stored in PostgreSQL. The backend uses `backend/data/vector_cache.json` when that local cache exists; data created while disconnected may be in `backend/uploads/local_store.json`. Local fallback chat history is held in memory and is lost on backend restart. Configure Supabase and ingest the brochure PDFs to persist and retrieve data from PostgreSQL.

---

## ⚙️ Backend Setup & Configuration

1. Copy `backend/.env.example` to `backend/.env` if the local file does not already exist. Then configure:
   ```ini
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-supabase-service-role-secret
   
   # LLM Provider: "gemini", "openai", or "mock" (offline test mode)
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=your-gemini-api-key
   OPENAI_API_KEY=your-openai-api-key
   ```
2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --app-dir backend --reload --port 8000
   ```
4. View interactive Swagger API documentation at:
   `http://localhost:8000/docs`

---

## 🚀 Deploy with Render and Vercel

Deploy the FastAPI backend to Render and the Vite frontend to Vercel. The frontend
uses `VITE_API_BASE_URL` to reach the backend; the Supabase and LLM credentials
must remain server-side in Render.

### Render backend

1. Push the repository to GitHub and create a **Web Service** in Render from it.
2. Set **Root Directory** to `backend`.
3. Use these commands:

   ```text
   Build: pip install -r requirements.txt
   Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

4. Add these environment variables in Render:
   - `SUPABASE_URL` and `SUPABASE_KEY` for the existing Supabase project. Use
     the server-side service-role key; do not put it in Vercel.
   - `LLM_PROVIDER=gemini` and `GEMINI_API_KEY`, or configure the OpenAI
     provider and `OPENAI_API_KEY`.
   - `ADMIN_USERNAME` and a strong `ADMIN_PASSWORD`.
   - `CORS_ORIGINS` with the Vercel site origin, for example
     `https://your-project.vercel.app`. Add multiple origins as a
     comma-separated list if needed.
5. After deployment, check the service root (`/`). It should report
   `storage_backend` as `supabase` (or `postgresql` if `DATABASE_URL` is used),
   not `local_fallback`. `/api/vehicles` and `/docs` are useful smoke checks.

### Vercel frontend

1. Import the same GitHub repository as a Vercel project.
2. Set **Root Directory** to `frontend`; use `npm run build` and output directory
   `dist` (Vercel usually detects these for Vite).
3. Set the Vercel environment variable:

   ```text
   VITE_API_BASE_URL=https://your-render-service.onrender.com
   ```

   Use the actual Render service URL, without a trailing slash. Redeploy after
   changing this variable because Vite embeds it during the build.

The existing brochure metadata, chunks, and embeddings are already in Supabase,
so chat retrieval can use those records after deployment without running the
schema or ingestion again. PDF files themselves are not stored in Supabase
Storage; Render's local filesystem is not a durable location for uploaded
brochures. Configure persistent/object storage before relying on brochure
uploads or PDF downloads across service restarts.

---

## 🔌 API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/documents/upload` | Upload a brochure PDF file for background extraction & vector indexing |
| `POST` | `/api/documents/process-local` | Automatically scans and indexes all PDFs in the `brochures/` folder |
| `GET` | `/api/documents` | Lists all uploaded brochures and their processing status |
| `POST` | `/api/chat` | AI conversational endpoint with RAG and page-level source citations |
| `GET` | `/api/chat/sessions/{id}/messages` | Retrieves conversation history and citations for a session |
| `POST` | `/api/compare/cars` | Side-by-side comparison between two car models (e.g. Creta vs Alcazar) |
| `POST` | `/api/compare/variants` | Detailed trim comparison (e.g. Creta S vs SX(O)) |
| `GET` | `/api/vehicles` | Returns all recognized vehicles and extracted variant matrices |
