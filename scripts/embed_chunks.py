#!/usr/bin/env python3
"""
Embed chunks from chunks.jsonl using OpenAI text-embedding-3-small
and load them into pgvector (PostgreSQL).

Requirements:
    pip install openai psycopg2-binary

Environment variables (from .env):
    OPENAI_API_KEY   — OpenAI API key
    POSTGRES_USER    — default: proshop
    POSTGRES_PASSWORD— default: proshop
    POSTGRES_DB      — default: proshop
    POSTGRES_HOST    — default: localhost
    POSTGRES_PORT    — default: 5432
"""

import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

import openai
import psycopg2
from psycopg2.extras import execute_values

# --- Configuration ---
CHUNKS_FILE = Path(__file__).resolve().parent.parent / 'docs' / 'project-data' / 'chunks.jsonl'
EMBEDDING_MODEL = 'text-embedding-3-small'
EMBEDDING_DIM = 1536
BATCH_SIZE = 100  # OpenAI allows up to 2048 inputs per request

# --- Database connection ---
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', '5432')),
    'dbname': os.getenv('POSTGRES_DB', 'proshop'),
    'user': os.getenv('POSTGRES_USER', 'proshop'),
    'password': os.getenv('POSTGRES_PASSWORD', 'proshop'),
}


def init_db(conn):
    """Create pgvector extension and chunks table if not exists."""
    with conn.cursor() as cur:
        cur.execute('CREATE EXTENSION IF NOT EXISTS vector;')
        cur.execute(f'''
            CREATE TABLE IF NOT EXISTS chunks (
                id SERIAL PRIMARY KEY,
                text TEXT NOT NULL,
                source_file TEXT,
                file_path TEXT,
                title TEXT,
                parent_headings TEXT[],
                keywords TEXT[],
                summary TEXT,
                language TEXT,
                embedding vector({EMBEDDING_DIM})
            );
        ''')
        cur.execute('''
            CREATE INDEX IF NOT EXISTS chunks_embedding_idx
            ON chunks USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 20);
        ''')
    conn.commit()


def load_chunks(path):
    """Load chunks from JSONL file."""
    chunks = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return chunks


def get_embeddings(texts, client):
    """Get embeddings from OpenAI API in batches."""
    all_embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=batch
        )
        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)
        if i + BATCH_SIZE < len(texts):
            time.sleep(0.5)  # rate limiting courtesy
        print(f'  Embedded {min(i + BATCH_SIZE, len(texts))}/{len(texts)} chunks')
    return all_embeddings


def insert_chunks(conn, chunks, embeddings):
    """Insert chunks with embeddings into PostgreSQL."""
    rows = []
    for chunk, emb in zip(chunks, embeddings):
        meta = chunk.get('metadata', {})
        rows.append((
            chunk['text'],
            meta.get('source_file'),
            meta.get('file_path'),
            meta.get('title'),
            meta.get('parent_headings', []),
            meta.get('keywords', []),
            meta.get('summary'),
            meta.get('language'),
            emb,
        ))

    with conn.cursor() as cur:
        execute_values(
            cur,
            '''INSERT INTO chunks
               (text, source_file, file_path, title, parent_headings,
                keywords, summary, language, embedding)
               VALUES %s''',
            rows,
            template='(%s, %s, %s, %s, %s, %s, %s, %s, %s::vector)',
            page_size=100
        )
    conn.commit()


def main():
    # Check API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print('ERROR: OPENAI_API_KEY not set. Add it to .env or export it.')
        sys.exit(1)

    # Load chunks
    print(f'Loading chunks from {CHUNKS_FILE}...')
    chunks = load_chunks(CHUNKS_FILE)
    print(f'  Loaded {len(chunks)} chunks')

    # Connect to PostgreSQL
    print(f'Connecting to PostgreSQL at {DB_CONFIG["host"]}:{DB_CONFIG["port"]}...')
    conn = psycopg2.connect(**DB_CONFIG)
    init_db(conn)
    print('  Database initialized (pgvector extension + chunks table)')

    # Generate embeddings
    print(f'Generating embeddings with {EMBEDDING_MODEL}...')
    client = openai.OpenAI(api_key=api_key)
    texts = [c['text'] for c in chunks]
    embeddings = get_embeddings(texts, client)
    print(f'  Got {len(embeddings)} embeddings ({EMBEDDING_DIM} dimensions each)')

    # Insert into DB
    print('Inserting into PostgreSQL...')
    insert_chunks(conn, chunks, embeddings)
    print(f'  Inserted {len(chunks)} rows into chunks table')

    conn.close()
    print('Done!')


if __name__ == '__main__':
    main()
