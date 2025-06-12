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
import fitz  # PyMuPDF - alternative PDF reader
from typing import List, Dict, Optional

class TPGParagraphExtractor:
    def __init__(self):
        # Simplified pattern for paragraphs like 1.1, 10.19, etc. (no sub-paragraphs)
        self.paragraph_pattern = re.compile(
            r'(\d+\.\d+)\s*\.?\s*(.*?)(?=\d+\.\d+\s*\.?\s*|$)', 
            re.DOTALL | re.MULTILINE
        )
        # Pattern to detect chapter titles and preface
        self.chapter_pattern = re.compile(
            r'(CHAPTER\s+[IVX]+|PREFACE|INTRODUCTION)\s*[:\-]?\s*(.*?)(?=CHAPTER\s+[IVX]+|$)',
            re.DOTALL | re.MULTILINE | re.IGNORECASE
        )
        
    def clean_text(self, text: str) -> str:
        """Clean extracted text by removing extra whitespace and formatting artifacts"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove page numbers and headers/footers (common patterns)
        text = re.sub(r'OECD.*?GUIDELINES.*?\d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Page \d+ of \d+', '', text, flags=re.IGNORECASE)
        # Remove hyphenation at line breaks
        text = re.sub(r'-\s+', '', text)
        return text.strip()

    def extract_with_pymupdf(self, pdf_path: str) -> str:
        """Extract text using PyMuPDF (usually better text extraction)"""
        try:
            doc = fitz.open(pdf_path)
            full_text = ""
            
            for page_num in range(doc.page_count):
                page = doc.page(page_num)
                text = page.get_text()
                full_text += text + "\n"
            
            doc.close()
            return self.clean_text(full_text)
        except Exception as e:
            print(f"PyMuPDF extraction failed: {e}")
            return None

    def extract_with_pypdf2(self, pdf_path: str) -> str:
        """Fallback extraction using PyPDF2"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                full_text = ""
                
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    full_text += text + "\n"
                
                return self.clean_text(full_text)
        except Exception as e:
            print(f"PyPDF2 extraction failed: {e}")
            return None

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using the best available method"""
        # Try PyMuPDF first (usually better)
        text = self.extract_with_pymupdf(pdf_path)
        
        # Fallback to PyPDF2 if PyMuPDF fails
        if not text:
            text = self.extract_with_pypdf2(pdf_path)
        
        if not text:
            raise Exception("Failed to extract text from PDF with both methods")
        
        return text

    def extract_paragraphs(self, text: str) -> Dict[str, List[Dict]]:
        """Extract numbered paragraphs from text and group by chapter"""
        chapters = {}
        
        # Find all paragraph matches
        matches = self.paragraph_pattern.findall(text)
        
        for match in matches:
            paragraph_id, content = match
            
            # Clean up the content
            content = self.clean_text(content)
            
            # Skip very short paragraphs (likely extraction errors)
            if len(content.strip()) < 20:
                continue
            
            # Determine chapter from paragraph ID
            chapter_num = paragraph_id.split('.')[0]
            
            # Handle special cases
            if chapter_num == "0" or paragraph_id.startswith("0."):
                chapter_key = "preface"
            else:
                chapter_key = f"chapter_{chapter_num}"
            
            # Initialize chapter if not exists
            if chapter_key not in chapters:
                chapters[chapter_key] = []
            
            # Create paragraph object
            paragraph = {
                "id": paragraph_id.strip(),
                "title": "",  # To be added manually
                "text": content,
                "explanation": ""  # To be added manually
            }
            
            chapters[chapter_key].append(paragraph)
        
        return chapters

    def save_chapters_as_json(self, chapters: Dict[str, List[Dict]], output_dir: str):
        """Save each chapter as a separate JSON file"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        total_paragraphs = 0
        chapter_summary = {}
        
        for chapter_key, paragraphs in chapters.items():
            # Create filename for chapter
            filename = f"{chapter_key}.json"
            file_path = output_path / filename
            
            # Create chapter object
            chapter_data = {
                "chapter": chapter_key,
                "total_paragraphs": len(paragraphs),
                "paragraphs": paragraphs
            }
            
            # Save as formatted JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(chapter_data, f, indent=2, ensure_ascii=False)
            
            total_paragraphs += len(paragraphs)
            chapter_summary[chapter_key] = len(paragraphs)
            print(f"Saved {len(paragraphs)} paragraphs to {filename}")
        
        return total_paragraphs, chapter_summary

    def process_pdf(self, pdf_path: str, output_dir: str = "extracted_chapters"):
        """Main processing function"""
        print(f"Processing PDF: {pdf_path}")
        
        # Extract text from PDF
        text = self.extract_text_from_pdf(pdf_path)
        print(f"Extracted {len(text)} characters from PDF")
        
        # Extract paragraphs grouped by chapter
        chapters = self.extract_paragraphs(text)
        total_paragraphs = sum(len(paragraphs) for paragraphs in chapters.values())
        print(f"Found {total_paragraphs} paragraphs across {len(chapters)} chapters")
        
        if chapters:
            # Save chapters as individual JSON files
            total_saved, chapter_summary = self.save_chapters_as_json(chapters, output_dir)
            
            # Also save a summary file
            summary = {
                "source_file": os.path.basename(pdf_path),
                "total_chapters": len(chapters),
                "total_paragraphs": total_saved,
                "chapters": chapter_summary,
                "chapter_files": [f"{chapter}.json" for chapter in chapters.keys()]
            }
            
            with open(Path(output_dir) / "extraction_summary.json", 'w') as f:
                json.dump(summary, f, indent=2)
            
            print("Extraction completed successfully!")
            print(f"Created {len(chapters)} chapter files:")
            for chapter in chapters.keys():
                print(f"  - {chapter}.json")
        else:
            print("No paragraphs found. Check the PDF format and paragraph numbering.")

def main():
    parser = argparse.ArgumentParser(description='Extract OECD TPG paragraphs from PDF')
    parser.add_argument('pdf_path', help='Path to the PDF file')
    parser.add_argument('--output', '-o', default='extracted_chapters', 
                       help='Output directory for JSON files')
    
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
