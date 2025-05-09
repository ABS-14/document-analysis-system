"""
Utilities for exporting document analysis results to different formats.
"""
import io
import textwrap
from fpdf import FPDF
import pandas as pd

class DocumentAnalysisReport(FPDF):
    """
    Custom PDF document for analysis reports with proper formatting.
    """
    def __init__(self):
        super().__init__()
        self.WIDTH = 210
        self.HEIGHT = 297
        
    def header(self):
        # Set up the header with logo and title
        self.set_font('Arial', 'B', 15)
        # Move to the right
        self.cell(80)
        # Add header graphics
        self.set_fill_color(230, 230, 230)
        self.cell(30, 10, 'Document Analysis', 0, 0, 'C')
        # Line break
        self.ln(20)
        
    def footer(self):
        # Set footer with page numbers
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    def chapter_title(self, title):
        # Add a chapter title with blue background
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 9, title, 0, 1, 'L', True)  # Use True instead of 1 for fill parameter
        self.ln(4)
        
    def chapter_body(self, body, bullet_point=False):
        # Add regular text with word wrapping
        self.set_font('Arial', '', 11)
        
        # Handle different types of content
        if isinstance(body, str):
            # For regular text paragraphs
            # Replace any non-latin1 characters with their closest equivalents
            text = self._clean_text_for_pdf(body)
            self.multi_cell(0, 5, text)
        elif isinstance(body, list) and bullet_point:
            # For bullet points
            for item in body:
                # Clean the item text to ensure it's PDF compatible
                item_text = self._clean_text_for_pdf(item)
                
                # Remove any prefixes that might contain special characters 
                # (the bullet points we added in the document_processor)
                if item_text and ': ' in item_text and item_text.split(': ', 1)[0] in [
                    'Key Point', 'Conclusion', 'Example', 'Statistic', 
                    'Question', 'Introduction', 'Summary', 'Point'
                ]:
                    # Extract just the content after the prefix
                    item_text = item_text.split(': ', 1)[1]
                
                wrapped_lines = textwrap.wrap(item_text, width=80)
                
                # Print the first line with bullet (using a standard dash instead of bullet char)
                if wrapped_lines:
                    self.cell(10, 6, '-', 0, 0, 'R')  # Using dash instead of bullet
                    self.cell(0, 6, wrapped_lines[0], 0, 1)
                    
                    # Print any additional wrapped lines with proper indentation
                    for line in wrapped_lines[1:]:
                        self.cell(10, 6, '', 0, 0)
                        self.cell(0, 6, line, 0, 1)
                        
                self.ln(1)
        self.ln(4)
    
    def _clean_text_for_pdf(self, text):
        """
        Clean text to ensure it's compatible with PDF output (latin-1 encoding)
        """
        if text is None:
            return ""
            
        # Replace common unicode characters with ASCII equivalents
        replacements = {
            '\u2022': '-',  # Bullet point
            '\u2192': '->',  # Right arrow
            '\u2190': '<-',  # Left arrow
            '\u2713': 'v',  # Check mark
            '\u2717': 'x',  # Cross mark
            '\u2019': "'",  # Curly quote (right single)
            '\u2018': "'",  # Curly quote (left single)
            '\u201C': '"',  # Curly quote (left double)
            '\u201D': '"',  # Curly quote (right double)
            '\u2026': '...',  # Ellipsis
            '\u2014': '-',  # Em dash
            '\u2013': '-',  # En dash
            '\u00B4': "'",  # Accent mark
            '`': "'"  # Backtick
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        # Final encoding to latin-1 with replacement of any remaining problematic chars
        return text.encode('latin-1', 'replace').decode('latin-1')
        
    def info_row(self, label, value):
        # Add a label-value pair row
        self.set_font('Arial', 'B', 10)
        self.cell(40, 6, label, 0, 0)
        self.set_font('Arial', '', 10)
        
        # Handle multiline values
        if "\n" in str(value):
            self.ln()
            self.cell(5, 6, "", 0, 0)  # Indent
            self.multi_cell(0, 6, str(value))
        else:
            self.cell(0, 6, str(value), 0, 1)
            
    def horizontal_line(self):
        # Add a horizontal separator line
        self.ln(1)
        self.line(10, self.get_y(), self.WIDTH - 10, self.get_y())
        self.ln(3)


def create_analysis_pdf(
    text_sample, 
    language, 
    summary=None, 
    bullet_points=None, 
    intent=None, 
    explanation=None
):
    """
    Create a well-formatted PDF report of the document analysis.
    
    Args:
        text_sample (str): A sample of the analyzed text
        language (str): The language of the document
        summary (str, optional): Document summary
        bullet_points (list, optional): List of extracted bullet points
        intent (str, optional): Classified intent
        explanation (str, optional): Intent explanation
    
    Returns:
        bytes: PDF file as bytes object
    """
    # Create PDF object
    pdf = DocumentAnalysisReport()
    pdf.add_page()
    
    # Title and basic info
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Multi-Language Document Analysis Report', 0, 1, 'C')
    pdf.ln(5)
    
    # Document Information Section
    pdf.chapter_title("Document Information")
    pdf.info_row("Language:", language)
    pdf.info_row("Character Count:", str(len(text_sample)))
    
    # Document Preview Section (truncated)
    pdf.horizontal_line()
    pdf.chapter_title("Document Preview")
    preview_text = text_sample[:300] + "..." if len(text_sample) > 300 else text_sample
    pdf.chapter_body(preview_text)
    
    # Summary Section
    if summary:
        pdf.horizontal_line()
        pdf.chapter_title("Document Summary")
        pdf.chapter_body(summary)
    
    # Bullet Points Section
    if bullet_points and len(bullet_points) > 0:
        pdf.horizontal_line()
        pdf.chapter_title("Key Points")
        pdf.chapter_body(bullet_points, bullet_point=True)
    
    # Intent Classification Section
    if intent and explanation:
        pdf.horizontal_line()
        pdf.chapter_title("Document Intent Analysis")
        pdf.info_row("Classified Intent:", intent)
        pdf.ln(5)
        
        # Format the explanation - replace bullet points for PDF compatibility
        formatted_explanation = explanation
        if explanation:
            # Replace bullet points with dashes for PDF compatibility
            formatted_explanation = explanation.replace('\u2022', '-')
            
        # Add the explanation text to the PDF
        pdf.chapter_body(formatted_explanation)
    
    # Footer info
    pdf.horizontal_line()
    pdf.set_font('Arial', 'I', 8)
    pdf.cell(0, 10, "© 2025 Multi-Language Document Analysis System | Government/Legal Document Analysis", 0, 1, 'C')
    
    # Get the PDF as bytes - avoiding the encode issues with different fpdf versions
    pdf_output = pdf.output(dest='S')
    
    # Handle different return types from different fpdf versions
    if isinstance(pdf_output, str):
        # String output from older versions
        pdf_bytes = pdf_output.encode('latin-1')
    elif isinstance(pdf_output, bytes):
        # Already bytes from some versions
        pdf_bytes = pdf_output
    else:
        # For any other type, try direct conversion or use a safe fallback
        try:
            pdf_bytes = bytes(pdf_output)
        except:
            # Last resort fallback to ensure we return something
            pdf_bytes = b"PDF generation failed, please try CSV export instead."
    
    return pdf_bytes