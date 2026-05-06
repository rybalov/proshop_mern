#!/usr/bin/env python3
"""
Markdown chunker for docs/project-data.
Splits markdown files into semantic chunks based on heading structure.
Output: docs/project-data/chunks.jsonl
"""

import json
import re
import os
from pathlib import Path

BASE_DIR = Path("/Users/nikita.rybalov/workspace/proshop_mern/docs/project-data")
OUTPUT_FILE = BASE_DIR / "chunks.jsonl"

TARGET_TOKENS = 400
MAX_TOKENS = 600
MIN_TOKENS = 50


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return len(text) // 4


def detect_language(text: str) -> str:
    """Detect language by checking for Cyrillic characters."""
    cyrillic = len(re.findall(r'[а-яА-ЯёЁ]', text))
    total_alpha = len(re.findall(r'[a-zA-Zа-яА-ЯёЁ]', text))
    if total_alpha == 0:
        return "en"
    return "ru" if cyrillic / total_alpha > 0.3 else "en"


def extract_keywords(text: str) -> list:
    """Extract keywords: function names, component names, tech terms."""
    keywords = set()

    # CamelCase / PascalCase words (component names)
    keywords.update(re.findall(r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)\b', text))

    # camelCase (function/variable names)
    keywords.update(re.findall(r'\b([a-z]+(?:[A-Z][a-z]+)+)\b', text))

    # Backtick-wrapped code terms
    keywords.update(re.findall(r'`([^`]{2,30})`', text))

    # Known tech terms
    tech_terms = [
        'Redux', 'React', 'Express', 'MongoDB', 'Mongoose', 'JWT', 'PayPal',
        'Stripe', 'localStorage', 'axios', 'Node.js', 'REST', 'API',
        'middleware', 'controller', 'reducer', 'action', 'thunk', 'multer',
        'bcrypt', 'Bootstrap', 'Docker', 'nginx', 'PostgreSQL', 'pgvector'
    ]
    for term in tech_terms:
        if term.lower() in text.lower():
            keywords.add(term)

    # Limit to 7 most relevant
    return sorted(list(keywords))[:7]


def generate_summary(text: str, headings: list) -> str:
    """Generate a one-sentence summary from text content."""
    lines = [l.strip() for l in text.split('\n')
             if l.strip() and not l.strip().startswith('#')]
    if not lines:
        return " > ".join(headings) if headings else ""

    first_line = lines[0]
    # If first line is short enough, use it directly
    if len(first_line) <= 150:
        return first_line
    # Otherwise truncate at sentence boundary
    match = re.match(r'^(.{50,150}[.!?])\s', first_line)
    if match:
        return match.group(1)
    return first_line[:150] + "..."


def parse_markdown_sections(content: str) -> list:
    """Parse markdown into sections based on headings."""
    sections = []
    current_headings = {}  # level -> heading text
    current_text_lines = []
    current_level = 0

    lines = content.split('\n')

    for line in lines:
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if heading_match:
            # Save previous section
            if current_text_lines:
                text = '\n'.join(current_text_lines).strip()
                if text:
                    breadcrumbs = []
                    for lvl in sorted(current_headings.keys()):
                        if lvl > 1:
                            breadcrumbs.append(current_headings[lvl])
                    sections.append({
                        'text': text,
                        'headings': breadcrumbs,
                        'level': current_level
                    })
                current_text_lines = []

            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()
            current_level = level
            current_headings[level] = heading_text
            # Clear deeper headings
            for k in list(current_headings.keys()):
                if k > level:
                    del current_headings[k]
        else:
            current_text_lines.append(line)

    # Last section
    if current_text_lines:
        text = '\n'.join(current_text_lines).strip()
        if text:
            breadcrumbs = []
            for lvl in sorted(current_headings.keys()):
                if lvl > 1:
                    breadcrumbs.append(current_headings[lvl])
            sections.append({
                'text': text,
                'headings': breadcrumbs,
                'level': current_level
            })

    return sections


def split_large_section(text: str, target=TARGET_TOKENS) -> list:
    """Split a large section into chunks by paragraphs or table rows."""
    paragraphs = re.split(r'\n\n+', text)
    chunks = []
    current_chunk = []
    current_size = 0

    for para in paragraphs:
        para_tokens = estimate_tokens(para)

        # If a single paragraph (e.g. a table) is too large, split it
        if para_tokens > MAX_TOKENS:
            # Flush current chunk first
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
            # Check if it's a table
            para_lines = para.strip().split('\n')
            if any(re.match(r'^\|.*\|$', l.strip()) for l in para_lines[:3]):
                chunks.extend(split_table(para))
            else:
                # Split by lines into ~target-sized groups
                group = []
                group_size = 0
                for line in para_lines:
                    line_tokens = estimate_tokens(line)
                    if group_size + line_tokens > MAX_TOKENS and group:
                        chunks.append('\n'.join(group))
                        group = [line]
                        group_size = line_tokens
                    else:
                        group.append(line)
                        group_size += line_tokens
                if group:
                    chunks.append('\n'.join(group))
            continue

        if current_size + para_tokens > MAX_TOKENS and current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append(chunk_text)
            # Overlap: keep last sentence of previous chunk
            last_sentences = re.findall(r'[^.!?]*[.!?]', current_chunk[-1])
            if last_sentences and len(last_sentences) > 1:
                overlap = last_sentences[-1].strip()
                current_chunk = [overlap, para]
                current_size = estimate_tokens(overlap) + para_tokens
            else:
                current_chunk = [para]
                current_size = para_tokens
        else:
            current_chunk.append(para)
            current_size += para_tokens

    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))

    return chunks


def split_table(text: str) -> list:
    """Split a markdown table into chunks of rows, preserving header."""
    lines = text.split('\n')
    header_lines = []
    data_lines = []
    in_header = True

    for line in lines:
        if in_header:
            header_lines.append(line)
            if re.match(r'^\|[-:\s|]+\|$', line.strip()):
                in_header = False
        else:
            if line.strip():
                data_lines.append(line)

    if not data_lines:
        return [text]

    header = '\n'.join(header_lines)
    header_tokens = estimate_tokens(header)
    chunks = []
    current_rows = []
    current_size = header_tokens

    for row in data_lines:
        row_tokens = estimate_tokens(row)
        if current_size + row_tokens > MAX_TOKENS and current_rows:
            chunks.append(header + '\n' + '\n'.join(current_rows))
            current_rows = [row]
            current_size = header_tokens + row_tokens
        else:
            current_rows.append(row)
            current_size += row_tokens

    if current_rows:
        chunks.append(header + '\n' + '\n'.join(current_rows))

    return chunks


def get_title(content: str) -> str:
    """Extract title from first H1 heading."""
    match = re.match(r'^#\s+(.+)', content, re.MULTILINE)
    return match.group(1).strip() if match else ""


def process_file(filepath: Path) -> list:
    """Process a single markdown file into chunks."""
    content = filepath.read_text(encoding='utf-8')
    relative_path = str(filepath.relative_to(BASE_DIR.parent.parent))
    source_file = str(filepath.relative_to(BASE_DIR))
    title = get_title(content)

    sections = parse_markdown_sections(content)
    chunks = []

    # Merge tiny sections with next sibling
    merged_sections = []
    i = 0
    while i < len(sections):
        section = sections[i]
        tokens = estimate_tokens(section['text'])

        if tokens < MIN_TOKENS and i + 1 < len(sections):
            # Keep merging until we have enough
            merged_text = section['text']
            headings = section['headings']
            level = section['level']
            i += 1
            while i < len(sections) and estimate_tokens(merged_text) < MIN_TOKENS:
                merged_text += '\n\n' + sections[i]['text']
                if not headings:
                    headings = sections[i]['headings']
                i += 1
            merged_sections.append({
                'text': merged_text,
                'headings': headings,
                'level': level
            })
        else:
            merged_sections.append(section)
            i += 1

    for section in merged_sections:
        tokens = estimate_tokens(section['text'])

        if tokens <= MAX_TOKENS:
            chunks.append({
                'text': section['text'],
                'metadata': {
                    'source_file': source_file,
                    'file_path': relative_path,
                    'title': title,
                    'parent_headings': section['headings'],
                    'keywords': extract_keywords(section['text']),
                    'summary': generate_summary(section['text'], section['headings']),
                    'language': detect_language(section['text'])
                }
            })
        else:
            sub_chunks = split_large_section(section['text'])
            for chunk_text in sub_chunks:
                chunks.append({
                    'text': chunk_text,
                    'metadata': {
                        'source_file': source_file,
                        'file_path': relative_path,
                        'title': title,
                        'parent_headings': section['headings'],
                        'keywords': extract_keywords(chunk_text),
                        'summary': generate_summary(chunk_text, section['headings']),
                        'language': detect_language(chunk_text)
                    }
                })

    return chunks


def main():
    all_chunks = []
    md_files = sorted(BASE_DIR.rglob("*.md"))

    print(f"Processing {len(md_files)} markdown files...")

    for filepath in md_files:
        file_chunks = process_file(filepath)
        all_chunks.extend(file_chunks)
        print(f"  {filepath.relative_to(BASE_DIR)}: {len(file_chunks)} chunks")

    # Write JSONL
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + '\n')

    # Stats
    token_counts = [estimate_tokens(c['text']) for c in all_chunks]
    print(f"\n--- Results ---")
    print(f"Total chunks: {len(all_chunks)}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Token stats: min={min(token_counts)}, max={max(token_counts)}, "
          f"avg={sum(token_counts)//len(token_counts)}, "
          f"median={sorted(token_counts)[len(token_counts)//2]}")

    langs = {}
    for c in all_chunks:
        lang = c['metadata']['language']
        langs[lang] = langs.get(lang, 0) + 1
    print(f"Languages: {langs}")


if __name__ == "__main__":
    main()
