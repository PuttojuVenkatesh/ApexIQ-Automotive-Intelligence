# ApexIQ Automotive Intelligence

ApexIQ is a web application for exploring and comparing SUVs using information retrieved from vehicle brochures. Ask GearGuide a question, compare models, and review the brochure pages used to support an answer.

## Try ApexIQ

| Service | Link |
|---|---|
| **Live application** | [https://apex-iq-automotive-intelligence.vercel.app/](https://apex-iq-automotive-intelligence.vercel.app/) |
| **Backend health** | [https://apexiq-automotive-intelligence.onrender.com/](https://apexiq-automotive-intelligence.onrender.com/) |
| **Interactive API documentation** | [https://apexiq-automotive-intelligence.onrender.com/docs](https://apexiq-automotive-intelligence.onrender.com/docs) |
| **Source code** | [GitHub repository](https://github.com/PuttojuVenkatesh/ApexIQ-Automotive-Intelligence) |

The frontend is hosted on Vercel. The API runs on Render and uses Supabase for its production database. The first request to a sleeping backend may take longer to respond.

## What it does

- **GearGuide chat:** Ask questions about a model or compare vehicles in everyday language.
- **Brochure-grounded answers:** The backend searches indexed brochure passages and returns source details, including document names and page numbers.
- **Vehicle comparison:** Compare available models and ask about particular areas such as space, safety, comfort, or powertrain.
- **Vehicle catalogue:** Browse the currently indexed vehicles. The production database currently includes Hyundai Alcazar, Hyundai Creta, Kia Seltos, and Tata Nexon.
- **Brochure administration:** Authorized administrators can upload, process, list, and delete brochure documents.

Feature availability can differ by trim. Answers should be checked against the cited brochure pages, especially when comparing trims or specifications.

## How an answer is produced

1. The frontend sends a question to the FastAPI backend.
2. The backend searches vectorized text chunks from the indexed brochures in PostgreSQL.
3. Relevant passages are sent to the configured language model to form a response.
4. The API returns the answer together with source references and related vehicles.
5. Chat messages and citations are stored in the configured database.

This retrieval-augmented generation (RAG) flow is intended to keep answers grounded in brochure content. If a detail is not in the retrieved passages, the assistant should not treat it as verified.

## Technology

- **Frontend:** React 18, Vite, JavaScript, and Tailwind CSS
- **Backend:** Python, FastAPI, and Uvicorn
- **Database and vector search:** PostgreSQL with `pgvector`; Supabase is the current hosted provider
- **AI providers:** Gemini or OpenAI for chat and embeddings
- **Hosting:** Vercel for the frontend and Render for the API

## Repository layout

```text
.
├── backend/
│   ├── app/
│   │   ├── api/                 # Chat, comparison, vehicle, and document routes
│   │   ├── core/config.py       # Environment-based application settings
│   │   ├── db/                  # Supabase and direct PostgreSQL clients
│   │   ├── services/            # PDF extraction, chunking, embeddings, and RAG
│   │   └── main.py              # FastAPI application
│   ├── schema.sql               # PostgreSQL and pgvector schema
│   ├── requirements.txt         # Python dependencies
│   └── test_*.py                # Backend regression tests
├── brochures/                   # Local PDF input; brochure files are not committed
├── frontend/
│   ├── src/                     # React application and API client
│   ├── package.json             # Frontend dependencies and scripts
│   └── .env.example             # Frontend API URL example
└── README.md
```

## Run locally

### Get the source code

```bash
git clone https://github.com/PuttojuVenkatesh/ApexIQ-Automotive-Intelligence.git
cd ApexIQ-Automotive-Intelligence
```

### Prerequisites

- Python 3.10 or newer
- Node.js 18 or newer and npm
- A PostgreSQL database with `pgvector` (Supabase is supported)
- An API key for the selected AI provider if you want live AI responses

### 1. Configure the backend

From the repository root, copy `backend/.env.example` to `backend/.env` and set your values. For example:

```ini
SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
SUPABASE_KEY=YOUR_SERVER_SIDE_SERVICE_ROLE_KEY

LLM_PROVIDER=gemini
GEMINI_API_KEY=YOUR_GEMINI_API_KEY

ADMIN_USERNAME=your-admin-name
ADMIN_PASSWORD=use-a-long-unique-password
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Alternatively, use a direct PostgreSQL connection instead of the Supabase REST client:

```ini
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require
```

`DATABASE_URL` takes precedence if both database configurations are set. URL-encode reserved characters in a connection-string password.

**Keep secrets private.** Do not commit `backend/.env`, put the Supabase service-role key in the frontend, or add secret values to a `VITE_*` variable. The repository ignores local `.env` files; use the `.env.example` files as templates only.

### 2. Create the database schema

For a new database, run [`backend/schema.sql`](backend/schema.sql) once using a database role with permission to enable `pgvector` and create the schema objects. In Supabase, open **SQL Editor**, create a query, paste the file contents, and run it. It defines:

- `documents` — brochure metadata and processing status
- `vehicles` and `vehicle_variants` — vehicle records
- `document_chunks` — extracted passages, page metadata, and vector embeddings
- `chat_sessions` and `chat_messages` — conversations and citations
- `match_document_chunks()` — the vector similarity search function

If you are using the already configured production Supabase project, its schema and indexed data are already in place; do not rerun the schema just to deploy the frontend.

### Inspect stored data in Supabase

Open **Table Editor** to browse the `vehicles`, `documents`, `document_chunks`, `chat_sessions`, and `chat_messages` tables. To inspect them with SQL:

```sql
select id, brand, model, model_year
from public.vehicles
order by brand, model;

select id, filename, status, page_count, created_at
from public.documents
order by created_at desc;

select d.filename, c.vehicle_id, c.chunk_index,
       c.metadata ->> 'page' as page, left(c.content, 200) as text_preview
from public.document_chunks c
join public.documents d on d.id = c.document_id
order by d.filename, c.chunk_index;

select s.id as session_id, s.title, m.role, m.content, m.sources, m.created_at
from public.chat_sessions s
join public.chat_messages m on m.session_id = s.id
order by m.created_at desc;
```

`document_chunks` contains the searchable brochure passages and embeddings. Chat rows contain conversation messages and the source references returned with answers.

### 3. Install and start the backend

Create and activate a virtual environment, then install the Python requirements:

**Windows PowerShell**

```powershell
py -m venv backend\venv
backend\venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

**macOS or Linux**

```bash
python3 -m venv backend/venv
source backend/venv/bin/activate
python -m pip install -r backend/requirements.txt
```

From the repository root, start the API:

```bash
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

The local API is at `http://localhost:8000/`; interactive API documentation is at `http://localhost:8000/docs`.

### 4. Install and start the frontend

In a second terminal:

```bash
cd frontend
npm install
```

Copy `frontend/.env.example` to `frontend/.env.local` if you need to change the API URL. For local development, it should point to:

```ini
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Then start Vite:

```bash
npm run dev
```

Open the local URL printed by Vite (normally `http://localhost:5173/`). The API client removes trailing slashes from the configured backend URL.

## Add and index brochures

1. Put authorized PDF brochures in the local `brochures/` directory, or use the authenticated Admin page to upload a PDF.
2. To index local PDFs from the repository root, configure the database first, then run:

   ```powershell
   python backend\ingest.py
   ```

   On macOS or Linux, use `python backend/ingest.py`.
3. The ingestion pipeline extracts text and page metadata, creates chunks and embeddings, then stores searchable records in PostgreSQL. Files already indexed by filename are skipped.
4. Ask GearGuide a question and check its source references to see which brochure and page supported the response.

The PDF binaries are not stored in PostgreSQL by this application. The database holds document metadata, extracted passages, and embeddings; uploaded files remain on the backend filesystem. Render filesystems are not durable by default, so configure persistent or object storage before relying on hosted PDF uploads or downloads across restarts.

## API endpoints

The complete request and response schemas are available in the live [Swagger UI](https://apexiq-automotive-intelligence.onrender.com/docs).

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Service health and active storage provider |
| `GET` | `/api/vehicles` | List indexed vehicles |
| `POST` | `/api/chat` | Ask a brochure-grounded question |
| `GET` | `/api/chat/sessions/{session_id}/messages` | Retrieve a saved conversation |
| `POST` | `/api/compare/cars` | Compare two vehicles |
| `POST` | `/api/compare/variants` | Compare vehicle variants |
| `POST` | `/api/documents/auth/login` | Sign in to brochure administration |
| `POST` | `/api/documents/auth/logout` | Sign out of brochure administration |
| `GET` | `/api/documents` | List documents (admin authentication required) |
| `POST` | `/api/documents/upload` | Upload a brochure (admin authentication required) |
| `POST` | `/api/documents/process-local` | Index PDFs in the configured local folder (admin authentication required) |
| `GET` | `/api/documents/{doc_id}/file` | Download a brochure (admin authentication required) |
| `DELETE` | `/api/documents/{doc_id}` | Delete a brochure record (admin authentication required) |

### Example chat request

```bash
curl -X POST "https://apexiq-automotive-intelligence.onrender.com/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"query":"Compare Kia Seltos and Tata Nexon by safety features","conversation_history":[]}'
```

The response includes an `answer`, a `sources` array with brochure/page details, a `session_id`, and the number of retrieved chunks. Use the live Swagger UI to try other endpoints and inspect their full schemas.

## Production deployment

The production frontend and API are deployed separately. The frontend calls the Render API using `VITE_API_BASE_URL`; AI and database credentials belong only in the Render environment.

### Render — FastAPI backend

Create a **Web Service** from this repository and set:

| Setting | Value |
|---|---|
| Root Directory | `backend` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/` |

Do not add `--app-dir backend` or `--reload` when the Root Directory is `backend`. The start command must bind to `0.0.0.0` and use Render's `$PORT`.

Set these variables in the Render dashboard:

- `SUPABASE_URL` and `SUPABASE_KEY` for the existing Supabase project, or use `DATABASE_URL` instead for direct PostgreSQL. `DATABASE_URL` takes precedence if set.
- `LLM_PROVIDER=gemini` and `GEMINI_API_KEY`, or `LLM_PROVIDER=openai` and `OPENAI_API_KEY`.
- `ADMIN_USERNAME` and a strong `ADMIN_PASSWORD`.
- `CORS_ORIGINS=https://apex-iq-automotive-intelligence.vercel.app`

After deployment, the backend root should report `status: online` and `storage_backend: supabase` (or `postgresql` if using `DATABASE_URL`). If it reports `local_fallback`, the backend is not connected to the configured database.

### Vercel — React frontend

Import the same GitHub repository as a Vercel project and set:

| Setting | Value |
|---|---|
| Root Directory | `frontend` |
| Framework | Vite |
| Build Command | `npm run build` |
| Output Directory | `dist` |

Set this Vercel environment variable:

```ini
VITE_API_BASE_URL=https://apexiq-automotive-intelligence.onrender.com
```

Use the Render URL without a trailing slash. The frontend also normalizes trailing slashes, but using the clean URL avoids confusion. Redeploy Vercel after changing an environment variable because Vite embeds it at build time.

## Troubleshooting

- **The page loads but chat fails:** Check that `VITE_API_BASE_URL` points to the Render service, then check the Render logs and confirm `LLM_PROVIDER` and the matching AI API key are configured.
- **Browser reports a CORS error:** Set Render's `CORS_ORIGINS` to the exact Vercel origin, including `https://` and excluding any path or trailing slash. The application reads `CORS_ORIGINS`, not `ALLOWED_ORIGINS`.
- **Render says `No open ports detected`:** Use the Start Command shown above. A process bound only to `127.0.0.1` or a fixed port will not receive Render traffic.
- **Render says `No module named 'app'`:** Set Root Directory to `backend` and remove `--app-dir backend` from the Start Command.
- **Storage reports `local_fallback`:** Recheck the Render database variables and verify the schema exists. Never copy the Supabase service-role key into Vercel.
- **Hosted brochure downloads or uploads disappear:** Configure persistent/object storage for PDF files. Supabase currently stores the extracted text and vectors, not the PDF binaries.
