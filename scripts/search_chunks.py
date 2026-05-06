#!/usr/bin/env python3
"""
Semantic search over pgvector chunks using OpenAI embeddings.

Usage:
    python3 scripts/search_chunks.py "your query here"
    python3 scripts/search_chunks.py "query" --top_k 10
    python3 scripts/search_chunks.py "query" --source_file incidents
    python3 scripts/search_chunks.py "query" --type adr
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / '.env')

import openai
import psycopg2

EMBEDDING_MODEL = 'text-embedding-3-small'

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', '5432')),
    'dbname': os.getenv('POSTGRES_DB', 'proshop'),
    'user': os.getenv('POSTGRES_USER', 'proshop'),
    'password': os.getenv('POSTGRES_PASSWORD', 'proshop'),
}


def embed_query(text, client):
    """Embed a single query string."""
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=[text])
    return response.data[0].embedding


def search(query, top_k=5, source_file=None, file_type=None):
    """
    Semantic search over chunks.

    Args:
        query: Search query string.
        top_k: Number of results to return.
        source_file: Filter by source_file (substring match).
        file_type: Filter by file_path directory/type (substring match).

    Returns:
        List of dicts with text, score, and metadata.
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print('ERROR: OPENAI_API_KEY not set.')
        sys.exit(1)

    client = openai.OpenAI(api_key=api_key)
    embedding = embed_query(query, client)
    embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'

    # Build query with optional filters
    conditions = []
    params = []

    if source_file:
        conditions.append('source_file ILIKE %s')
        params.append(f'%{source_file}%')

    if file_type:
        conditions.append('file_path ILIKE %s')
        params.append(f'%{file_type}%')

    where_clause = ''
    if conditions:
        where_clause = 'WHERE ' + ' AND '.join(conditions)

    sql = f'''
        SELECT
            text,
            source_file,
            file_path,
            title,
            parent_headings,
            keywords,
            summary,
            1 - (embedding <=> %s::vector) AS similarity
        FROM chunks
        {where_clause}
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    '''
    params = [embedding_str] + params + [embedding_str, top_k]

    # Fix: params order for WHERE between the two embedding refs
    # Rebuild properly
    if conditions:
        sql = f'''
            SELECT
                text,
                source_file,
                file_path,
                title,
                parent_headings,
                keywords,
                summary,
                1 - (embedding <=> %s::vector) AS similarity
            FROM chunks
            {where_clause}
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        '''
        params = [embedding_str] + [f'%{source_file}%'] * (1 if source_file else 0) + \
                 [f'%{file_type}%'] * (1 if file_type else 0) + [embedding_str, top_k]
    else:
        sql = '''
            SELECT
                text,
                source_file,
                file_path,
                title,
                parent_headings,
                keywords,
                summary,
                1 - (embedding <=> %s::vector) AS similarity
            FROM chunks
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        '''
        params = [embedding_str, embedding_str, top_k]

    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            'text': row[0][:300] + ('...' if len(row[0]) > 300 else ''),
            'full_text': row[0],
            'source_file': row[1],
            'file_path': row[2],
            'title': row[3],
            'parent_headings': row[4],
            'keywords': row[5],
            'summary': row[6],
            'similarity': round(float(row[7]), 4),
        })

    return results


def main():
    parser = argparse.ArgumentParser(description='Semantic search over project chunks')
    parser.add_argument('query', help='Search query')
    parser.add_argument('--top_k', type=int, default=5, help='Number of results (default: 5)')
    parser.add_argument('--source_file', type=str, default=None, help='Filter by source_file substring')
    parser.add_argument('--type', type=str, default=None, dest='file_type', help='Filter by file_path substring (e.g. incidents, adr)')
    args = parser.parse_args()

    results = search(args.query, top_k=args.top_k, source_file=args.source_file, file_type=args.file_type)

    print(f'\n{"="*60}')
    print(f'Query: "{args.query}"')
    if args.source_file:
        print(f'Filter: source_file ~ "{args.source_file}"')
    if args.file_type:
        print(f'Filter: file_path ~ "{args.file_type}"')
    print(f'Results: {len(results)}')
    print(f'{"="*60}\n')

    for i, r in enumerate(results, 1):
        print(f'--- Result {i} (score: {r["similarity"]}) ---')
        print(f'  Source: {r["source_file"]}')
        print(f'  Path:   {r["file_path"]}')
        print(f'  Title:  {r["title"]}')
        if r["parent_headings"]:
            print(f'  Section: {" > ".join(r["parent_headings"])}')
        print(f'  Text:   {r["text"][:200]}...')
        print()


if __name__ == '__main__':
    main()
