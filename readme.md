# OECD Transfer Pricing Guidelines Paragraph Extractor

This repository automatically extracts numbered paragraphs from OECD Transfer Pricing Guidelines PDFs and converts them into individual JSON files for easy processing and annotation.

## 🚀 Quick Start

1. **Upload a PDF**: Simply upload any OECD TPG PDF file to this repository
2. **Automatic Processing**: The GitHub Action will automatically trigger and extract all paragraphs
3. **Download Results**: Individual JSON files will be created for each paragraph

## 📋 Output Format

Each paragraph is saved as a separate JSON file with this structure:

```json
{
  "id": "10.19",
  "title": "",
  "text": "Independent enterprises, when considering whether to enter into a particular financial transaction...",
  "explanation": ""
}
```

- `id`: The paragraph number (e.g., "10.19", "1.38.2")
- `title`: Empty string (to be filled manually)
- `text`: The extracted paragraph content
- `explanation`: Empty string (to be filled manually)

## 🔧 How It Works

### Automatic Triggers
The extraction process runs automatically when:
- A PDF file is pushed to the repository
- A pull request contains PDF files
- Manually triggered via GitHub Actions

### Manual Trigger
You can also manually trigger the extraction:
1. Go to the "Actions" tab
2. Select "Extract OECD TPG Paragraphs"
3. Click "Run workflow"
4. Specify the path to your PDF file

## 📁 File Structure

After processing, you'll find:

```
extracted_paragraphs/
├── your-pdf-name/
│   ├── paragraph_1_1.json
│   ├── paragraph_1_2.json
│   ├── paragraph_10_19.json
│   ├── ...
│   └── extraction_summary.json
└── extraction_report.md
```

## 🛠️ Technical Details

### Dependencies
- **PyMuPDF**: Primary PDF text extraction (high quality)
- **PyPDF2**: Fallback PDF extraction method
- **Python 3.11**: Runtime environment

### Paragraph Detection
The extractor uses regex patterns to identify numbered paragraphs in formats like:
- `1.1` Simple numbering
- `10.19` Chapter.paragraph
- `1.38.2` Multi-level numbering

### Text Cleaning
The extracted text is automatically cleaned by:
- Removing excessive whitespace
- Eliminating page numbers and headers
- Fixing hyphenation across line breaks
- Filtering out very short paragraphs (likely extraction errors)

## 📝 Usage Examples

### Processing a Single PDF
```bash
python extract_paragraphs.py oecd-tpg-2022.pdf --output my_paragraphs
```

### Custom Output Directory
The output directory structure will be:
```
my_paragraphs/
├── paragraph_1_1.json
├── paragraph_1_2.json
└── extraction_summary.json
```

## 🎯 Next Steps After Extraction

1. **Review Extraction Quality**: Check the `extraction_summary.json` for paragraph counts
2. **Add Titles**: Fill in the empty `title` fields for each paragraph
3. **Add Explanations**: Provide context and analysis in the `explanation` fields
4. **Quality Control**: Review paragraphs for extraction accuracy

## 📊 Extraction Statistics

The system generates:
- Individual JSON files for each paragraph
- Summary file with extraction metadata
- Detailed report with processing information
- Artifact uploads for easy download

## 🔍 Troubleshooting

### No Paragraphs Found
- Check if the PDF contains numbered paragraphs
- Verify the numbering format matches expected patterns
- Review the PDF text extraction quality

### Poor Text Quality
- Try different PDF sources (some scanned PDFs may have poor OCR)
- Check if the PDF is text-based rather than image-based

### Large Files
- The system can handle large PDFs (1500+ paragraphs)
- Processing time scales with document size
- Artifacts are retained for 90 days

## 🤝 Contributing

1. Fork the repository
2. Add your PDF improvements or processing enhancements
3. Submit a pull request
4. The extraction will run automatically on your PR

## 📄 License

This tool is designed for processing public OECD documents. Please ensure compliance with OECD usage terms and copyright requirements.