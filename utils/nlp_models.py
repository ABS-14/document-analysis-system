import os
import re
import random
import warnings
from collections import defaultdict

# Suppress warnings and messages
warnings.filterwarnings('ignore')

# Keep track of loaded models to avoid reloading
_loaded_models = {}

class MockNLPModel:
    """Mock NLP model for demonstration purposes"""
    
    def __init__(self, language):
        self.language = language
        
    def __call__(self, text):
        """Process text and return a mock document object"""
        # Split text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Create a basic structure to represent the processed document
        doc = {
            'text': text,
            'sentences': sentences,
            'language': self.language,
            'tokens': text.split(),
            'entities': self._extract_mock_entities(text)
        }
        
        return doc
        
    def _extract_mock_entities(self, text):
        """Extract mock entities from text for demonstration"""
        entities = []
        
        # Common entity patterns for each language
        entity_patterns = {
            "English": [
                (r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', 'PERSON'),
                (r'\b[A-Z][a-z]+ \d+\b', 'DATE'),
                (r'\b\d+ [A-Z][a-z]+ (Street|Road|Avenue)\b', 'LOCATION'),
                (r'\b[A-Z][A-Za-z]+ (Corporation|Inc|Ltd)\b', 'ORG')
            ],
            "Hindi": [
                (r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', 'PERSON'),
                (r'\b\d+ [A-Za-z]+\b', 'DATE')
            ],
            "Marathi": [
                (r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', 'PERSON'),
                (r'\b\d+ [A-Za-z]+\b', 'DATE')
            ],
            "Tamil": [
                (r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', 'PERSON'),
                (r'\b\d+ [A-Za-z]+\b', 'DATE')
            ]
        }
        
        # Use patterns for the specified language, or fall back to English
        patterns = entity_patterns.get(self.language, entity_patterns["English"])
        
        # Find matches for each pattern
        for pattern, entity_type in patterns:
            for match in re.finditer(pattern, text):
                entities.append({
                    'text': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'type': entity_type
                })
        
        return entities

def load_model_for_language(language):
    """
    Load a mock NLP model for the given language.
    
    Args:
        language (str): The language to load a model for
        
    Returns:
        object: The loaded mock NLP model
    """
    # Check if we already loaded this model
    if language in _loaded_models:
        return _loaded_models[language]
    
    # Create a mock model for the language
    nlp = MockNLPModel(language)
    
    # Save the loaded model for future use
    _loaded_models[language] = nlp
    
    return nlp

class MockTransformerPipeline:
    """Mock implementation of a transformer pipeline"""
    
    def __init__(self, task, language):
        self.task = task
        self.language = language
        
    def __call__(self, text, **kwargs):
        """Process text according to the task"""
        if self.task == "summarization":
            return self._generate_summary(text, **kwargs)
        elif self.task == "zero-shot-classification":
            return self._classify_text(text, **kwargs)
        elif self.task == "translation":
            return self._translate_text(text, **kwargs)
        else:
            return {"error": f"Unsupported task: {self.task}"}
    
    def _generate_summary(self, text, max_length=300, min_length=150, **kwargs):
        """Generate a more detailed mock summary"""
        # Extract some sentences for the summary
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # For more detailed summaries, use more sentences strategically
        if len(sentences) > 10:
            # Get sentences from beginning, middle and end for better coverage
            summary_sentences = [
                sentences[0],
                sentences[1] if len(sentences) > 1 else "",
                sentences[len(sentences)//4],
                sentences[len(sentences)//2],
                sentences[(3*len(sentences))//4],
                sentences[-2] if len(sentences) > 2 else "",
                sentences[-1] if len(sentences) > 1 else ""
            ]
        elif len(sentences) > 5:
            # For medium texts, use first, middle, and last sentences
            summary_sentences = [
                sentences[0],
                sentences[1] if len(sentences) > 1 else "",
                sentences[len(sentences)//2],
                sentences[-2] if len(sentences) > 2 else "",
                sentences[-1] if len(sentences) > 1 else ""
            ]
        else:
            # For short texts, use all sentences
            summary_sentences = sentences
        
        # Join the sentences and add connecting phrases for better flow
        filtered_sentences = [s for s in summary_sentences if s.strip()]
        if len(filtered_sentences) > 2:
            # Add transition phrases to make it read more naturally
            transitions = ["Additionally, ", "Furthermore, ", "Moreover, ", "In addition, ", "Also, "]
            enhanced_sentences = [filtered_sentences[0]]
            
            for i, sentence in enumerate(filtered_sentences[1:-1]):
                transition = transitions[i % len(transitions)]
                enhanced_sentences.append(f"{transition}{sentence.lstrip()}")
            
            enhanced_sentences.append(f"Finally, {filtered_sentences[-1].lstrip()}")
            summary = " ".join(enhanced_sentences)
        else:
            summary = " ".join(filtered_sentences)
        
        # Make sure summary is not too short
        if len(summary) < min_length and len(text) > min_length:
            # Add more content to reach minimum length
            additional_text = ""
            remaining_sentences = [s for s in sentences if s not in filtered_sentences]
            
            for s in remaining_sentences:
                if len(summary + ' ' + additional_text) < min_length:
                    additional_text += ' ' + s
                else:
                    break
                    
            summary += additional_text
        
        # Truncate to max_length if needed
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        
        # Return a list containing a dictionary with summary text    
        return [{"summary_text": summary}]
    
    def _classify_text(self, text, **kwargs):
        """Classify text into categories"""
        # Get candidate labels from kwargs
        candidate_labels = kwargs.get('candidate_labels', ["Complaint", "Request", "Update/Notification", "Appreciation"])
        
        # Simple keyword matching for classification
        keyword_categories = {
            "Complaint": ["issue", "problem", "complaint", "dissatisfied", "disappointed", "poor", "bad", "terrible"],
            "Request": ["please", "request", "kindly", "could you", "would you", "need", "want", "asking"],
            "Update/Notification": ["update", "notify", "inform", "announce", "notice", "advisory", "bulletin", "information"],
            "Appreciation": ["thank", "appreciate", "grateful", "excellent", "good", "well done", "pleased", "happy"]
        }
        
        # Count keywords in each category
        scores = defaultdict(int)
        text_lower = text.lower()
        
        for category, keywords in keyword_categories.items():
            for keyword in keywords:
                if keyword in text_lower:
                    scores[category] += 1
        
        # If no keywords found, assign random scores
        if not scores:
            for category in candidate_labels:
                # Use integers for scores
                scores[category] = 1 + int(random.random() * 9)  # Integer between 1-10
        
        # Sort categories by score
        ordered_labels = sorted(
            candidate_labels,
            key=lambda label: scores.get(label, 0),
            reverse=True
        )
        
        # Calculate normalized scores
        total = sum(float(scores.get(label, 0.1)) for label in ordered_labels)  # Convert to float for division
        normalized_scores = [float(scores.get(label, 0.1))/total for label in ordered_labels]
        
        return {
            "labels": ordered_labels,
            "scores": normalized_scores,
            "sequence": text[:100] + "..." if len(text) > 100 else text
        }
    
    def _translate_text(self, text, **kwargs):
        """Mock translation - just return the original text for demonstration"""
        return f"[Translated from {self.language} to English]: {text[:100]}..." if len(text) > 100 else text

def get_transformer_model(task, language):
    """
    Get a mock transformer model for a specific task and language.
    
    Args:
        task (str): The NLP task ('summarization', 'classification', etc.)
        language (str): The language of the model
        
    Returns:
        MockTransformerPipeline: A mock implementation of the requested pipeline
    """
    return MockTransformerPipeline(task, language)
