#!/usr/bin/env python3
"""
OECD TPG PDF Paragraph Extractor
Extracts numbered paragraphs from PDF and creates individual JSON files
"""

import os
import re
import json
import argparse
from pathlib import Path
import PyPDF2
import fitz  # PyMuPDF
from typing import List, Dict


class TPGParagraphExtractor:
    def __init__(self):
        self.paragraph_pattern = re.compile(
            r'(\d+\.\d+)\s*\.?\s*(.*?)(?=\d+\.\d+\s*\.?\s*|$)',
            re.DOTALL | re.MULTILINE
        )
        self.annex_paragraph_pattern = re.compile(
            r'([A-Z]+\.\d+|[IVXLCDM]+\.\d+)\s*\.?\s*(.*?)(?=[A-Z]+\.\d+|[IVXLCDM]+\.\d+\s*\.?\s*|$)',
            re.DOTALL | re.MULTILINE
        )
        self.section_pattern = re.compile(
            r'(PREFACE|CHAPTER\s+[IVXLCDM]+|ANNEX(?:\s+[IVXLCDM]*)?(?:\s+TO\s+CHAPTER\s+[IVXLCDM]+)?)\s*[:\-]?\s*(.*?)(?=PREFACE|CHAPTER\s+[IVXLCDM]+|ANNEX|$)',
            re.DOTALL | re.MULTILINE | re.IGNORECASE
        )

    def clean_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'OECD.*?GUIDELINES.*?\d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Page \d+ of \d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'-\s+', '', text)
        return text.strip()

    def extract_with_pymupdf(self, pdf_path: str) -> str:
        try:
            doc = fitz.open(pdf_path)
            full_text = ""
            for page_num in range(doc.page_count):
                page = doc.page(page_num)
                full_text += page.get_text() + "\n"
            doc.close()
            return self.clean_text(full_text)
        except Exception as e:
            print(f"PyMuPDF extraction failed: {e}")
            return None

    def extract_with_pypdf2(self, pdf_path: str) -> str:
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                full_text = ""
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
                return self.clean_text(full_text)
        except Exception as e:
            print(f"PyPDF2 extraction failed: {e}")
            return None

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        text = self.extract_with_pymupdf(pdf_path)
        if not text:
            text = self.extract_with_pypdf2(pdf_path)
        if not text:
            raise Exception("Failed to extract text from PDF with both methods")
        return text

    def roman_to_int(self, roman: str) -> int:
        roman_values = {'I': 1, 'V': 5, 'X': 10, 'L': 50,
                        'C': 100, 'D': 500, 'M': 1000}
        total = 0
        prev_value = 0
        for char in reversed(roman):
            value = roman_values.get(char, 0)
            if value < prev_value:
                total -= value
            else:
                total += value
            prev_value = value
        return total

    def identify_section_type(self, text_section: str) -> str:
        text_upper = text_section.upper()

        if "PREFACE" in text_upper:
            return "preface"

        if "CHAPTER" in text_upper:
            match = re.search(r'CHAPTER\s+([IVXLCDM]+)', text_upper)
            if match:
                chapter_num = self.roman_to_int(match.group(1))
                return f"chapter_{chapter_num}"
            return "chapter_unknown"

        if "ANNEX" in text_upper:
            match = re.search(r'ANNEX\s+([IVXLCDM]+)?\s*TO\s+CHAPTER\s+([IVXLCDM]+)', text_upper)
            if match:
                annex_id = match.group(1) or ""
                chapter_num = self.roman_to_int(match.group(2))
                annex_part = f"_{annex_id.lower()}" if annex_id else ""
                return f"annex{annex_part}_to_chapter_{chapter_num}"

            match = re.search(r'ANNEX\s+([IVXLCDM]+)', text_upper)
            if match:
                return f"annex_{match.group(1).lower()}"

            return "annex_general"

        return "unknown"

    def extract_paragraphs(self, text: str) -> Dict[str, List[Dict]]:
        chapters = {}
        sections = self.section_pattern.findall(text)

        if sections:
            for section_header, section_content in sections:
                section_type = self.identify_section_type(section_header)
                self.extract_paragraphs_from_section(section_content, section_type, chapters)
        else:
            self.extract_paragraphs_from_section(text, "unknown", chapters)

        return chapters

    def extract_paragraphs_from_section(self, text: str, section_type: str, chapters: Dict[str, List[Dict]]):
        matches = self.paragraph_pattern.findall(text)
        if not matches:
            matches = self.annex_paragraph_pattern.findall(text)

        for paragraph_id, content in matches:
            content = self.clean_text(content)
            if len(content.strip()) < 20:
                continue

            if section_type != "unknown":
                chapter_key = section_type
            else:
                chapter_prefix = paragraph_id.split('.')[0]
                if chapter_prefix == "0":
                    chapter_key = "preface"
                elif chapter_prefix.isdigit():
                    chapter_key = f"chapter_{chapter_prefix}"
                else:
                    chapter_key = f"annex_{chapter_prefix.lower()}"

            if chapter_key not in chapters:
                chapters[chapter_key] = []

            chapters[chapter_key].append({
                "id": paragraph_id.strip(),
                "title": "",
                "text": content,
                "explanation": ""
            })

    def save_chapters_as_json(self, chapters: Dict[str, List[Dict]], output_dir: str):
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        total_paragraphs = 0
        chapter_summary = {}

        for chapter_key, paragraphs in chapters.items():
            file_path = output_path / f"{chapter_key}.json"
            chapter_data = {
                "chapter": chapter_key,
                "total_paragraphs": len(paragraphs),
                "paragraphs": paragraphs
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(chapter_data, f, indent=2, ensure_ascii=False)

            total_paragraphs += len(paragraphs)
            chapter_summary[chapter_key] = len(paragraphs)
            print(f"Saved {len(paragraphs)} paragraphs to {file_path.name}")

        return total_paragraphs, chapter_summary

    def process_pdf(self, pdf_path: str, output_dir: str = "extracted_chapters"):
        print(f"Processing PDF: {pdf_path}")

        text = self.extract_text_from_pdf(pdf_path)
        print(f"Extracted {len(text)} characters from PDF")

        chapters = self.extract_paragraphs(text)
        total_paragraphs = sum(len(p) for p in chapters.values())
        print(f"Found {total_paragraphs} paragraphs across {len(chapters)} chapters")

        if chapters:
            total_saved, summary = self.save_chapters_as_json(chapters, output_dir)
            full_summary = {
                "source_file": os.path.basename(pdf_path),
                "total_chapters": len(chapters),
                "total_paragraphs": total_saved,
                "chapters": summary,
                "chapter_files": [f"{chapter}.json" for chapter in chapters]
            }

            with open(Path(output_dir) / "extraction_summary.json", 'w') as f:
                json.dump(full_summary, f, indent=2)

            print("Extraction completed successfully.")
            print("Created chapter files:")
            for chapter in chapters:
                print(f"  - {chapter}.json")
        else:
            print("No paragraphs found. Check the PDF format and numbering.")


def main():
    parser = argparse.ArgumentParser(description='Extract OECD TPG paragraphs from PDF')
    parser.add_argument('pdf_path', help='Path to the PDF file')
    parser.add_argument('--output', '-o', default='extracted_chapters', help='Output directory for JSON files')

    args = parser.parse_args()

    if not os.path.exists(args.pdf_path):
        print(f"Error: PDF file not found: {args.pdf_path}")
        return 1

    try:
        extractor = TPGParagraphExtractor()
        extractor.process_pdf(args.pdf_path, args.output)
        return 0
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
