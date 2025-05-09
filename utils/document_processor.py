from utils.nlp_models import load_model_for_language, get_transformer_model
import re

def process_document(text, language):
    """
    Process the document text based on the language.
    
    Args:
        text (str): The document text
        language (str): The language of the document
    
    Returns:
        dict: The processed document with NLP features
    """
    # Load the appropriate model for the language
    nlp = load_model_for_language(language)
    
    # Process the text with the model
    # For long texts, we process in chunks to avoid memory issues
    max_chunk_size = 100000  # Characters
    
    if len(text) <= max_chunk_size:
        doc = nlp(text)
        return {"doc": doc, "text": text, "language": language}
    else:
        # Process in chunks and combine the results
        chunks = []
        for i in range(0, len(text), max_chunk_size):
            chunk = text[i:i + max_chunk_size]
            chunks.append(nlp(chunk))
        
        # Create a result object with the chunks
        return {
            "chunks": chunks,
            "text": text,
            "language": language,
            "is_chunked": True
        }

def get_summary(processed_doc, language):
    """
    Generate a summary of the document.
    
    Args:
        processed_doc (dict): The processed document
        language (str): The language of the document
    
    Returns:
        str: The summary text
    """
    # Get the summarizer model
    summarizer = get_transformer_model("summarization", language)
    
    text = processed_doc["text"]
    
    # Determine the max length based on document size
    text_length = len(text)
    max_length = min(150, text_length // 4)  # Summary should be at most 1/4 of the original
    min_length = min(30, max_length // 2)    # And at least half of max_length
    
    # For very long texts, we summarize each paragraph and combine
    if text_length > 1000:
        paragraphs = re.split(r'\n\s*\n', text)
        summaries = []
        
        # Summarize each substantial paragraph
        for para in paragraphs:
            if len(para.strip()) > 200:  # Only summarize paragraphs of significant length
                try:
                    result = summarizer(para, max_length=max_length // 2, 
                                        min_length=min_length // 2, 
                                        do_sample=False)
                    # Extract summary text from result
                    if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
                        para_summary = result[0].get('summary_text', para[:100] + "...")
                    else:
                        para_summary = para[:100] + "..."
                    summaries.append(para_summary)
                except Exception:
                    # If summarization fails, add a portion of the original text
                    summaries.append(para[:100] + "...")
        
        # If we have multiple summaries, summarize them again for coherence
        if len(summaries) > 1:
            combined_summary = " ".join(summaries)
            if len(combined_summary) > 1000:
                try:
                    result = summarizer(combined_summary, max_length=max_length, 
                                        min_length=min_length, 
                                        do_sample=False)
                    # Extract summary text from result
                    if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
                        final_summary = result[0].get('summary_text', combined_summary[:200] + "...")
                    else:
                        final_summary = combined_summary[:200] + "..."
                    return final_summary
                except Exception:
                    return combined_summary
            return combined_summary
        elif len(summaries) == 1:
            return summaries[0]
        else:
            return text[:max_length] + "..."  # Fallback
    else:
        # For shorter texts, summarize directly
        try:
            result = summarizer(text, max_length=max_length, 
                              min_length=min_length, 
                              do_sample=False)
            # Extract summary text from result
            if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
                summary = result[0].get('summary_text', text[:150] + "...")
            else:
                summary = text[:150] + "..."
            return summary
        except Exception:
            # Fallback to extractive summarization if model fails
            sentences = re.split(r'(?<=[.!?])\s+', text)
            return " ".join(sentences[:3]) + "..."

def extract_bullet_points(processed_doc, language):
    """
    Extract key points from the document as bullet points with enhanced detail.
    
    Args:
        processed_doc (dict): The processed document
        language (str): The language of the document
    
    Returns:
        list: List of bullet points
    """
    # Extract text from the processed document
    text = processed_doc["text"]
    
    # Use keyword extraction or sentence importance to identify key points
    bullets = []
    
    # Split into paragraphs
    paragraphs = re.split(r'\n\s*\n', text)
    
    # Expanded list of indicator phrases that suggest important information
    indicators = [
        # Original indicators
        "important", "significant", "key", "main", "primary",
        "essential", "crucial", "critical", "fundamental",
        "therefore", "thus", "hence", "accordingly", "consequently",
        "as a result", "in conclusion", "to summarize",
        "must", "should", "shall", "will", "required",
        # Additional indicators
        "noteworthy", "notably", "particularly", "especially", "specifically",
        "primarily", "chiefly", "mainly", "predominantly", "principally",
        "significantly", "markedly", "substantially", "considerably",
        "undoubtedly", "unquestionably", "indisputably", "indubitably",
        "evidently", "obviously", "plainly", "patently", "manifestly",
        "firstly", "secondly", "thirdly", "finally", "lastly",
        "in summary", "in brief", "in short", "overall"
    ]
    
    # Expanded triggers for topic sentences
    topic_sentence_indicators = [
        "this", "these", "such", "the", "our", "their", "we", "they", 
        "according", "research", "study", "analysis", "evidence", "data", 
        "report", "survey", "investigation", "findings", "results"
    ]
    
    # PHASE 1: Extract sentences with explicit indicators
    for para in paragraphs:
        if len(para.strip()) < 20:  # Skip very short paragraphs
            continue
            
        # Split paragraph into sentences
        sentences = re.split(r'(?<=[.!?])\s+', para)
        
        # Select sentences that might contain key information
        for sentence in sentences:
            # Skip very short sentences
            if len(sentence.strip()) < 15:
                continue
                
            # Add sentences with indicators or those that start with numbers/bullets
            if (any(indicator in sentence.lower() for indicator in indicators) or 
                re.match(r'^\s*\d+[\.\)]', sentence) or
                re.match(r'^\s*[•\-\*]', sentence)):
                # Clean up the sentence
                clean_sentence = re.sub(r'^\s*[•\-\*\d+[\.\)]]\s*', '', sentence).strip()
                if clean_sentence and clean_sentence not in bullets:
                    bullets.append(clean_sentence)
    
    # PHASE 2: Extract topic sentences from each paragraph
    if len(bullets) < 15:  # We want more bullet points now for detailed analysis
        for para in paragraphs:
            if len(para.strip()) < 20:  # Skip very short paragraphs
                continue
                
            sentences = re.split(r'(?<=[.!?])\s+', para)
            
            # Add first sentence of paragraph (often a topic sentence)
            if sentences and len(sentences[0]) > 15:
                if sentences[0] not in bullets:
                    bullets.append(sentences[0])
            
            # Look for sentences with topic indicators
            for sentence in sentences[1:]:  # Skip first sentence which we already added
                if len(sentence.strip()) < 15:
                    continue
                    
                # Look for topic sentence indicators
                if any(indicator in sentence.lower() for indicator in topic_sentence_indicators):
                    if sentence not in bullets:
                        bullets.append(sentence)
    
    # PHASE 3: Extract sentences with quantifiable information or specific entities
    for para in paragraphs:
        sentences = re.split(r'(?<=[.!?])\s+', para)
        for sentence in sentences:
            # Look for sentences with numbers, percentages, dates, etc.
            if (re.search(r'\d+(\.\d+)?%', sentence) or  # Percentage
                re.search(r'\$\d+', sentence) or         # Money
                re.search(r'\d{4}', sentence) or         # Year
                re.search(r'\d+\s*(million|billion|trillion)', sentence.lower())):  # Large numbers
                if sentence not in bullets:
                    bullets.append(sentence)
    
    # PHASE 4: Extract questions which often highlight key areas
    for para in paragraphs:
        sentences = re.split(r'(?<=[.!?])\s+', para)
        for sentence in sentences:
            if '?' in sentence and len(sentence) > 20:
                if sentence not in bullets:
                    bullets.append(sentence)
    
    # Enhance the bullet points with clarifying prefixes where appropriate
    enhanced_bullets = []
    for i, bullet in enumerate(bullets):
        bullet_lower = bullet.lower()
        
        # Add category prefixes based on content to make bullet points more meaningful
        if any(word in bullet_lower for word in ["therefore", "thus", "hence", "result", "consequently"]):
            prefix = "Conclusion: "
        elif any(word in bullet_lower for word in ["example", "instance", "illustrate", "case"]):
            prefix = "Example: "
        elif any(word in bullet_lower for word in ["important", "crucial", "critical", "essential"]):
            prefix = "Key Point: "
        elif re.search(r'\d+%|\d+\.\d+%', bullet):
            prefix = "Statistic: "
        elif '?' in bullet:
            prefix = "Question: "
        elif i < len(bullets) * 0.2:  # First 20% of bullets - likely introduction
            prefix = "Introduction: "
        elif i > len(bullets) * 0.8:  # Last 20% of bullets - likely conclusion
            prefix = "Summary: "
        else:
            prefix = "Point: "
            
        enhanced_bullets.append(f"{prefix}{bullet}")
    
    # Increase the limit for more detailed analysis
    bullets = enhanced_bullets[:20]  # Allow up to 20 bullet points now
    
    return bullets

def classify_intent(processed_doc, language):
    """
    Classify the intent of the document.
    
    Args:
        processed_doc (dict): The processed document
        language (str): The language of the document
    
    Returns:
        tuple: (intent_category, explanation)
    """
    # Extract text from the processed document
    text = processed_doc["text"]
    
    # Get the classifier model
    classifier = get_transformer_model("zero-shot-classification", language)
    
    # Define the intent categories
    categories = ["Complaint", "Request", "Update/Notification", "Appreciation"]
    
    # Use the first 1000 characters for classification to avoid token limits
    sample_text = text[:1000]
    
    # Classify the intent
    try:
        result = classifier(sample_text, candidate_labels=categories)
        
        # Check if result is a dictionary with labels and scores
        if isinstance(result, dict) and 'labels' in result and 'scores' in result:
            # Get the top intent and its score
            intent = result['labels'][0] if len(result['labels']) > 0 else categories[0]
            score = float(result['scores'][0]) if len(result['scores']) > 0 else 0.5
        else:
            # Fallback if result doesn't have expected format
            intent = categories[0]
            score = 0.5
    except Exception:
        # Fallback in case of any error
        intent = categories[0]
        score = 0.5
    
    # Generate a detailed explanation based on the classification
    explanations = {
        "Complaint": {
            "main": "The document contains expressions of dissatisfaction or descriptions of problems that need to be addressed.",
            "details": [
                "The text includes language that indicates dissatisfaction, frustration, or concerns.",
                "There may be descriptions of issues, problems, or negative experiences.",
                "The author appears to be seeking resolution, correction, or acknowledgment of a problem.",
                "The document likely uses words with negative connotations to describe a situation or experience.",
                "There may be explicit requests for corrective action or compensation."
            ]
        },
        "Request": {
            "main": "The document is primarily asking for information, action, or consideration of a specific matter.",
            "details": [
                "The text contains explicit requests for action, information, or assistance.",
                "There is a clear expectation of a response or action from the recipient.",
                "The language is typically polite and formal, using phrases like 'kindly', 'please', or 'would you'.",
                "The document specifies what is being requested and often includes timeframes or deadlines.",
                "There may be references to previous communications or established processes."
            ]
        },
        "Update/Notification": {
            "main": "The document provides information, updates, or notifications about policies, procedures, or events.",
            "details": [
                "The text focuses on delivering information rather than requesting action.",
                "There are statements of fact, announcements, or updates on specific topics.",
                "The document may include dates, times, locations, or other specific details about events or changes.",
                "The language is generally neutral and informative, rather than persuasive or emotional.",
                "There may be references to attachments, additional resources, or follow-up communications."
            ]
        },
        "Appreciation": {
            "main": "The document expresses gratitude, acknowledgment, or positive feedback.",
            "details": [
                "The text contains expressions of thanks, gratitude, or appreciation.",
                "There are positive descriptions of actions, services, or assistance received.",
                "The document may acknowledge specific individuals, teams, or organizations.",
                "The language is warm, appreciative, and uses positive adjectives.",
                "There may be mentions of the positive impact of the actions being acknowledged."
            ]
        }
    }
    
    # Add confidence information to the explanation
    confidence_phrases = {
        "high": "with high confidence",
        "medium": "with moderate confidence", 
        "low": "with low confidence"
    }
    
    if isinstance(score, (int, float)):
        if score > 0.8:
            confidence_level = "high"
        elif score > 0.6:
            confidence_level = "medium"
        else:
            confidence_level = "low"
    else:
        confidence_level = "low"
    
    confidence_phrase = confidence_phrases[confidence_level]
    
    # Create a detailed multi-paragraph explanation
    explanation_parts = [
        f"{explanations[intent]['main']} The document has been classified {confidence_phrase} ({score:.2f}).",
        "\nDetailed analysis:"
    ]
    
    # Add bullet points for more detailed explanation
    for detail in explanations[intent]['details']:
        explanation_parts.append(f"\n• {detail}")
    
    # Add keyword analysis if available from the classifier
    keyword_list = []
    
    # Identify common keywords associated with the intent category
    intent_keywords = {
        "Complaint": ["issue", "problem", "concerned", "dissatisfied", "disappointed", "fix", "resolve", "failing"],
        "Request": ["please", "request", "kindly", "would you", "could you", "need", "require", "provide"],
        "Update/Notification": ["inform", "announce", "update", "notification", "advise", "reminder", "schedule", "upcoming"],
        "Appreciation": ["thank", "appreciate", "grateful", "excellent", "outstanding", "wonderful", "helpful", "generous"]
    }
    
    # Check if any of the keywords for the identified intent are present in the text
    text_sample = text[:2000].lower()  # Take a larger sample for keyword analysis
    found_keywords = [word for word in intent_keywords[intent] if word in text_sample]
    
    if found_keywords:
        keyword_list = found_keywords[:5]  # Limit to 5 keywords for conciseness
        explanation_parts.append(f"\nKeywords detected: {', '.join(keyword_list)}")
    
    # Add confidence explanation
    confidence_explanations = {
        "high": "The confidence level is high, suggesting strong indicators of this intent in the text.",
        "medium": "The moderate confidence level indicates some clear indicators of this intent, though some aspects may be ambiguous.",
        "low": "The low confidence level suggests the intent classification is tentative, as the text may contain mixed signals or limited clear indicators."
    }
    
    explanation_parts.append(f"\n{confidence_explanations[confidence_level]}")
    
    # Combine all parts into a complete explanation
    explanation = "".join(explanation_parts)
    
    return intent, explanation
