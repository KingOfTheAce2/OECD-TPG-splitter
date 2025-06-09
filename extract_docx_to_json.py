import json
import os
import re
from docx import Document
from collections import defaultdict

def extract_paragraphs_by_chapter(docx_path):
    doc = Document(docx_path)
    chapters = defaultdict(list)
    current_chapter = None
    current_id = None

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        # Detect chapter headers
        chapter_match = re.match(r'^CHAPTER\s+([IVXLC]+):\s+(.*)', text, re.IGNORECASE)
        if chapter_match:
            roman = chapter_match.group(1).upper()
            title = chapter_match.group(2).strip()
            current_chapter = f"Chapter_{roman.replace(' ', '_')}"
            continue

        # Extract paragraph IDs like 1.43, 2.1, etc.
        id_match = re.match(r'^(\d+\.\d+)\s+(.*)', text)
        if id_match:
            current_id = id_match.group(1)
            content = id_match.group(2).strip()
            entry = {
                "id": current_id,
                "title": "",
                "text": content,
                "explanation": ""
            }
            if current_chapter:
                chapters[current_chapter].append(entry)

    return chapters

def save_chapters_to_json(chapters, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    for chapter, entries in chapters.items():
        output_path = os.path.join(output_dir, f"{chapter}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    input_docx = "OECD_TPG_EN_2022.docx"  # Adjust if using a different path
    output_folder = "output_json"

    all_chapters = extract_paragraphs_by_chapter(input_docx)
    save_chapters_to_json(all_chapters, output_folder)
    print(f"Processed and saved {len(all_chapters)} chapters to '{output_folder}'")
