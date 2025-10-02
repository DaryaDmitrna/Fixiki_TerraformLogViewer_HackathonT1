-- PostgreSQL schema for Terraform LogViewer
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS log_record (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  raw jsonb NOT NULL,
  ts timestamptz,
  level text,
  section text, -- plan|apply|http|other
  tf_req_id text,
  parent_req_id text,
  tf_resource_type text,
  is_read boolean NOT NULL DEFAULT false,
  has_req_body boolean DEFAULT false,
  has_res_body boolean DEFAULT false,
  message text
);

-- Full-text search
ALTER TABLE log_record ADD COLUMN IF NOT EXISTS fts tsvector;
CREATE INDEX IF NOT EXISTS idx_log_fts ON log_record USING GIN (fts);
CREATE INDEX IF NOT EXISTS idx_log_ts ON log_record (ts);
CREATE INDEX IF NOT EXISTS idx_log_req ON log_record (tf_req_id);
CREATE INDEX IF NOT EXISTS idx_log_level ON log_record (level);
CREATE INDEX IF NOT EXISTS idx_log_section ON log_record (section);

-- Trigger for FTS (message + json string)
CREATE OR REPLACE FUNCTION log_fts_update() RETURNS trigger AS $$
BEGIN
  NEW.fts := to_tsvector('simple',
               coalesce(NEW.message,'') || ' ' ||
               coalesce(NEW.raw::text,''));
  RETURN NEW;
END; $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_log_fts ON log_record;
CREATE TRIGGER trg_log_fts BEFORE INSERT OR UPDATE ON log_record
FOR EACH ROW EXECUTE FUNCTION log_fts_update();
