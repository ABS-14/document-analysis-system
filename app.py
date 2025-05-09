import streamlit as st
import pandas as pd
import io
import os
from utils.document_processor import process_document, get_summary, extract_bullet_points, classify_intent
from utils.file_handler import extract_text_from_file, supported_file_types
from utils.export_utils import create_analysis_pdf

# Set page configuration
st.set_page_config(
    page_title="Multi-Language Document Analysis System",
    page_icon="📄",
    layout="wide",
)

# App title and description
st.title("Multi-Language Document Analysis System")
st.markdown("""
This system processes and analyzes government and legal documents in multiple Indian languages and English.
It provides document summarization, bullet point extraction, and intent classification capabilities.
""")

# Sidebar with instructions
with st.sidebar:
    st.header("About the System")
    st.markdown("""
    ### Features
    - **Multi-language Support**: English, Hindi, Marathi, and Tamil
    - **Document Summarization**: Generates concise summaries
    - **Bullet Point Generation**: Extracts key points
    - **Intent Classification**: Categorizes document intent
    - **Explanation**: Provides reasoning for classification
    - **File Support**: Process text, PDF, DOCX files
    - **High Character Limit**: Up to 500,000 characters
    - **Result Export**: Export as CSV
    """)
    
    st.header("Instructions")
    st.markdown("""
    1. Upload a document or paste text directly
    2. Select the document language
    3. Choose analysis options
    4. View and export results
    """)

# Main content area - Two columns
col1, col2 = st.columns([1, 1])

with col1:
    st.header("Document Input")
    
    # Initialize text variable at the start
    text = ""
    
    # Input method selection
    input_method = st.radio("Choose input method:", ["Upload File", "Paste Text"])
    
    if input_method == "Upload File":
        uploaded_file = st.file_uploader("Upload a document", type=list(supported_file_types.keys()))
        
        if uploaded_file is not None:
            # Display file details
            file_details = {
                "Filename": uploaded_file.name,
                "File size": f"{uploaded_file.size / 1024:.2f} KB"
            }
            st.write(file_details)
            
            try:
                # Extract text from file
                text = extract_text_from_file(uploaded_file)
                
                # Show character count
                char_count = len(text)
                if char_count > 500000:
                    st.warning(f"Document has {char_count} characters, which exceeds the limit of 500,000. Only the first 500,000 characters will be processed.")
                    text = text[:500000]
                else:
                    st.info(f"Document has {char_count} characters.")
                
                # Show preview
                with st.expander("Document Preview (first 500 characters)"):
                    st.text(text[:500] + "...")
                    
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
                text = ""
    else:
        text = st.text_area("Paste your text here:", height=300)
        
        # Only process if text was entered
        if text:
            char_count = len(text)
            if char_count > 500000:
                st.warning(f"Text has {char_count} characters, which exceeds the limit of 500,000. Only the first 500,000 characters will be processed.")
                text = text[:500000]
            else:
                st.info(f"Text has {char_count} characters.")
    
    # Language selection
    language = st.selectbox(
        "Select document language:",
        ["English", "Hindi", "Marathi", "Tamil"]
    )
    
    # Analysis options
    st.subheader("Analysis Options")
    generate_summary = st.checkbox("Generate Summary", value=True)
    generate_bullets = st.checkbox("Extract Bullet Points", value=True)
    classify_document = st.checkbox("Classify Document Intent", value=True)
    
    # Process button
    process_btn = st.button("Process Document")

# Results column
with col2:
    st.header("Analysis Results")
    
    # We've already initialized text in col1, so it should be defined here
    
    # Process the document when the button is clicked and there's text to process
    if process_btn and text and len(text.strip()) > 0:
        with st.spinner("Processing document..."):
            try:
                # Process the document
                processed_doc = process_document(text, language)
                
                # Store results in session state
                st.session_state.processed = True
                st.session_state.text = text
                st.session_state.language = language
                
                # Display results based on selected options
                if generate_summary:
                    st.subheader("Document Summary")
                    summary = get_summary(processed_doc, language)
                    st.write(summary)
                    st.session_state.summary = summary
                
                if generate_bullets:
                    st.subheader("Key Points")
                    bullets = extract_bullet_points(processed_doc, language)
                    for point in bullets:
                        st.markdown(f"• {point}")
                    st.session_state.bullets = bullets
                
                if classify_document:
                    st.subheader("Document Intent")
                    intent, explanation = classify_intent(processed_doc, language)
                    
                    # Display intent with appropriate color
                    intent_colors = {
                        "Complaint": "🔴 Complaint",
                        "Request": "🔵 Request",
                        "Update/Notification": "🟢 Update/Notification",
                        "Appreciation": "🟡 Appreciation"
                    }
                    
                    st.markdown(f"**Intent:** {intent_colors.get(intent, intent)}")
                    st.markdown(f"**Explanation:** {explanation}")
                    
                    st.session_state.intent = intent
                    st.session_state.explanation = explanation
                
                # Export options
                st.subheader("Export Results")
                
                # Create DataFrame for export (outside the button click)
                export_data = {
                    "Document Language": [language],
                    "Character Count": [len(text)]
                }
                
                if generate_summary and 'summary' in st.session_state:
                    export_data["Summary"] = [st.session_state.summary]
                    
                if generate_bullets and 'bullets' in st.session_state:
                    export_data["Key Points"] = ["\n".join([f"• {point}" for point in st.session_state.bullets])]
                    
                if classify_document and 'intent' in st.session_state:
                    export_data["Intent"] = [st.session_state.intent]
                    export_data["Explanation"] = [st.session_state.explanation]
                
                # Convert to DataFrame
                export_df = pd.DataFrame(export_data)
                
                # Create export buttons in two columns for better UI
                export_col1, export_col2 = st.columns(2)
                
                with export_col1:
                    # CSV Export option
                    csv_data = export_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📊 Download as CSV",
                        data=csv_data,
                        file_name=f"document_analysis_results_{language.lower()}.csv",
                        mime="text/csv",
                        help="Download raw data in CSV format"
                    )
                
                with export_col2:
                    # PDF Export option with formatted template
                    try:
                        # Gather data for PDF export
                        summary_text = st.session_state.summary if 'summary' in st.session_state else None
                        bullet_points = st.session_state.bullets if 'bullets' in st.session_state else []
                        intent_text = st.session_state.intent if 'intent' in st.session_state else None
                        explanation_text = st.session_state.explanation if 'explanation' in st.session_state else None
                        
                        # Create PDF
                        pdf_data = create_analysis_pdf(
                            text_sample=text,
                            language=language,
                            summary=summary_text,
                            bullet_points=bullet_points,
                            intent=intent_text,
                            explanation=explanation_text
                        )
                        
                        # Offer PDF download
                        st.download_button(
                            label="📄 Download as PDF Report",
                            data=pdf_data,
                            file_name=f"document_analysis_report_{language.lower()}.pdf",
                            mime="application/pdf",
                            help="Download a professionally formatted PDF report"
                        )
                    except Exception as e:
                        st.error(f"Error creating PDF: {str(e)}")
                    
            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")
    else:
        st.info("Upload a document or paste text and click 'Process Document' to see analysis results here.")

# Footer
st.markdown("---")
st.markdown("© 2025 Multi-Language Document Analysis System | Government/Legal Document Analysis")
