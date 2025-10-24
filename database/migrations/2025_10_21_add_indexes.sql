-- UDS3 / Covina - Index Migration (Safe)
-- Date: 2025-10-21
-- Purpose: Create recommended indexes for relational workloads.
-- Safety: Uses IF NOT EXISTS and guards with to_regclass checks to avoid errors when tables are missing.

-- documents
DO $$ BEGIN
  IF to_regclass('public.documents') IS NOT NULL THEN
    CREATE INDEX IF NOT EXISTS idx_documents_classification ON public.documents (classification);
    CREATE INDEX IF NOT EXISTS idx_documents_processing_status ON public.documents (processing_status);
    CREATE INDEX IF NOT EXISTS idx_documents_created_at ON public.documents (created_at);
    -- Optional composite for common queries: classification + created_at desc
    CREATE INDEX IF NOT EXISTS idx_documents_classification_created_at ON public.documents (classification, created_at DESC);
  END IF;
END $$;

-- document_keywords
DO $$ BEGIN
  IF to_regclass('public.document_keywords') IS NOT NULL THEN
    CREATE INDEX IF NOT EXISTS idx_document_keywords_document_id ON public.document_keywords (document_id);
    CREATE INDEX IF NOT EXISTS idx_document_keywords_keyword ON public.document_keywords (keyword);
  END IF;
END $$;

-- job_files (if managed in PostgreSQL)
DO $$ BEGIN
  IF to_regclass('public.job_files') IS NOT NULL THEN
    CREATE INDEX IF NOT EXISTS idx_job_files_job_id ON public.job_files (job_id);
    CREATE INDEX IF NOT EXISTS idx_job_files_status ON public.job_files (status);
    CREATE INDEX IF NOT EXISTS idx_job_files_retry_count ON public.job_files (retry_count);
    -- file_path can be large; index only if queries require it frequently
    -- CREATE INDEX IF NOT EXISTS idx_job_files_file_path ON public.job_files (file_path);
  END IF;
END $$;

-- uds3_sagas (generic saga table name; adjust if prefixed differently)
DO $$ BEGIN
  IF to_regclass('public.uds3_sagas') IS NOT NULL THEN
    CREATE INDEX IF NOT EXISTS idx_uds3_sagas_status ON public.uds3_sagas (status);
    CREATE INDEX IF NOT EXISTS idx_uds3_sagas_updated_at ON public.uds3_sagas (updated_at);
    CREATE INDEX IF NOT EXISTS idx_uds3_sagas_saga_id ON public.uds3_sagas (saga_id);
  END IF;
END $$;
