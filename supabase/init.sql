-- Initialize database for Policy Pilot
-- This script sets up the basic table structure for the application

-- Enable the pgvector extension for vector operations
CREATE EXTENSION IF NOT EXISTS vector;

-- Create embeddings table for storing document chunks and their vector embeddings
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    metadata JSONB,
    embedding vector(1536), -- OpenAI text-embedding-3-small dimension
    file_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS embeddings_vector_idx ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create index for file name filtering
CREATE INDEX IF NOT EXISTS embeddings_file_name_idx ON embeddings(file_name);

-- Create function for vector similarity search
CREATE OR REPLACE FUNCTION match_embeddings(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 5,
    filter_file_name text DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    metadata JSONB,
    file_name TEXT,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        embeddings.id,
        embeddings.content,
        embeddings.metadata,
        embeddings.file_name,
        1 - (embeddings.embedding <=> query_embedding) AS similarity
    FROM embeddings
    WHERE 
        embeddings.embedding IS NOT NULL
        AND (filter_file_name IS NULL OR embeddings.file_name = filter_file_name)
        AND 1 - (embeddings.embedding <=> query_embedding) > match_threshold
    ORDER BY embeddings.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_embeddings_updated_at 
    BEFORE UPDATE ON embeddings 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert some sample data for testing (optional)
-- INSERT INTO embeddings (content, file_name, embedding) VALUES 
-- ('Sample policy document content for testing vector search functionality.', 'sample-policy.pdf', '[0.1, 0.2, 0.3, ...]'::vector); 