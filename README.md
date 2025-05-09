# Multi-Language Document Analysis System

A comprehensive NLP-based system for processing and analyzing government/legal documents in multiple Indian languages (English, Hindi, Marathi, Tamil) with summarization and intent classification capabilities.

## Features

- **Multi-language Support**: Process documents in English, Hindi, Marathi, and Tamil
- **Document Summarization**: Generate concise summaries of lengthy documents
- **Bullet Point Generation**: Extract key points from documents with proper formatting
- **Intent Classification**: Classify documents into categories (Complaint, Request, Update/Notification, Appreciation)
- **Format Support**: Process various document formats (PDF, DOCX, TXT, RTF)
- **High Volume Processing**: Support for documents up to 500,000 characters
- **Export Options**: Export analysis results as CSV or formatted PDF reports

## Getting Started

### Prerequisites

- Python 3.8+
- Streamlit
- Required libraries (requirements.txt)

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/document-analysis-system.git
cd document-analysis-system
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Run the application
```bash
streamlit run app.py
```

## Usage

1. Upload a document or paste text directly
2. Select the document language
3. Choose analysis options (summary, bullet points, intent classification)
4. Process the document
5. View the analysis results
6. Export results as CSV or PDF

## Project Structure

- `app.py`: Main Streamlit application
- `utils/`: 
  - `document_processor.py`: Core document processing functions
  - `file_handler.py`: File upload and text extraction utilities
  - `nlp_models.py`: NLP model implementations
  - `export_utils.py`: Export functionality (CSV/PDF)

## Future Enhancements

- Integration with real transformer models
- Support for additional languages
- Enhanced document structure analysis
- Batch processing capability
- API integration

## License

This project is licensed under the MIT License - see the LICENSE file for details.