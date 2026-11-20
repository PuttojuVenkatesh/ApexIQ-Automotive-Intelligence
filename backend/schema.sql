-- ==============================================================================
-- Supabase Schema: Automotive AI Assistant (PostgreSQL + pgvector)
-- ==============================================================================

-- 1. Enable pgvector and UUID extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Documents table (Tracks uploaded brochure PDFs and extraction status)
CREATE TABLE IF NOT EXISTS public.documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL,
    file_path TEXT, -- Server-local path; PDF binaries are not stored in PostgreSQL.
    file_size_bytes BIGINT,
    page_count INT DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'uploaded' CHECK (status IN ('uploaded', 'processing', 'indexed', 'failed')),
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Vehicles table (Stores recognized car models)
CREATE TABLE IF NOT EXISTS public.vehicles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES public.documents(id) ON DELETE CASCADE,
    brand TEXT NOT NULL,                  -- e.g., Hyundai, Kia, Tata
    model TEXT NOT NULL,                  -- e.g., Creta, Alcazar, Seltos, Nexon
    model_year INT,                       -- e.g., 2024, 2025
    body_type TEXT,                       -- e.g., SUV, Compact SUV, Sedans
    summary TEXT,                         -- Vehicle overview/tagline
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Vehicle Variants table (Stores individual trim/variant specs)
CREATE TABLE IF NOT EXISTS public.vehicle_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id UUID NOT NULL REFERENCES public.vehicles(id) ON DELETE CASCADE,
    variant_name TEXT NOT NULL,           -- e.g., E, EX, S, SX, SX(O), HTX, Fearless+
    fuel_type TEXT,                       -- Petrol, Diesel, EV, Turbo-Petrol
    transmission TEXT,                    -- MT, IVT, DCT, AT, AMT
    engine_specs JSONB DEFAULT '{}'::jsonb, -- displacement, power_bhp, torque_nm, mileage
    key_features JSONB DEFAULT '[]'::jsonb, -- array of prominent features
    safety_features JSONB DEFAULT '[]'::jsonb, -- airbags, ESC, ADAS Level
    price_range TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Document Chunks table (Stores text chunks with vector embeddings)
CREATE TABLE IF NOT EXISTS public.document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    vehicle_id UUID REFERENCES public.vehicles(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb, -- {"page": 5, "section": "Engine Specs", "vehicle": "Creta"}
    embedding VECTOR(1536),                      -- Vector embedding (1536 for OpenAI / Gemini 004 padded or 768)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. Chat Sessions & Messages (Stores conversation history)
CREATE TABLE IF NOT EXISTS public.chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT DEFAULT 'New Conversation',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES public.chat_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    sources JSONB DEFAULT '[]'::jsonb,           -- [{"document": "Creta", "page": 4, "excerpt": "..."}]
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. High-Performance Indexes
CREATE INDEX IF NOT EXISTS idx_documents_status ON public.documents(status);
CREATE INDEX IF NOT EXISTS idx_vehicles_brand_model ON public.vehicles(brand, model);
CREATE INDEX IF NOT EXISTS idx_variants_vehicle_id ON public.vehicle_variants(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON public.document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_vehicle_id ON public.document_chunks(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON public.chat_messages(session_id);

-- HNSW Vector Index for ultra-fast Cosine Similarity searches
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw
ON public.document_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 8. Stored Procedure for Cosine Similarity Search with pgvector
CREATE OR REPLACE FUNCTION public.match_document_chunks(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.2,
    match_count INT DEFAULT 6,
    filter_vehicle_id UUID DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    document_id UUID,
    vehicle_id UUID,
    chunk_index INT,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id,
        dc.document_id,
        dc.vehicle_id,
        dc.chunk_index,
        dc.content,
        dc.metadata,
        1 - (dc.embedding <=> query_embedding) AS similarity
    FROM public.document_chunks dc
    WHERE (filter_vehicle_id IS NULL OR dc.vehicle_id = filter_vehicle_id)
      AND (1 - (dc.embedding <=> query_embedding)) >= match_threshold
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Backend access uses the Supabase service_role key. Keep these tables closed
-- to browser-facing anon/authenticated roles; service_role bypasses RLS.
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vehicles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vehicle_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE
    public.documents,
    public.vehicles,
    public.vehicle_variants,
    public.document_chunks,
    public.chat_sessions,
    public.chat_messages
FROM anon, authenticated;
GRANT USAGE ON SCHEMA public TO service_role;
GRANT ALL PRIVILEGES ON TABLE
    public.documents,
    public.vehicles,
    public.vehicle_variants,
    public.document_chunks,
    public.chat_sessions,
    public.chat_messages
TO service_role;

REVOKE ALL ON FUNCTION public.match_document_chunks(VECTOR, FLOAT, INT, UUID)
FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.match_document_chunks(VECTOR, FLOAT, INT, UUID)
TO service_role;
