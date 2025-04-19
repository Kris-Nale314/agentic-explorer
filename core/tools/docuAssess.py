"""
Document Assessment Tools

This module provides analysis functions for earnings call transcripts and other textual documents,
focusing on language patterns, topic categorization, and change detection to support signal intelligence.
"""

import re
import pandas as pd
import numpy as np
from collections import Counter
import plotly.graph_objects as go
from typing import List, Dict, Any, Tuple, Optional, Union

# ==================== TEXT PREPROCESSING FUNCTIONS ====================

def clean_text(text: str) -> str:
    """
    Clean and normalize text for analysis.
    
    Args:
        text: Raw text string
        
    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,?!:;()-]', '', text)
    
    return text.strip()

def extract_qa_section(transcript: str) -> str:
    """
    Extract the Q&A section from an earnings call transcript.
    
    Args:
        transcript: Full earnings call transcript
        
    Returns:
        Q&A section of the transcript
    """
    # Common patterns indicating start of Q&A
    qa_indicators = [
        "QUESTIONS AND ANSWERS",
        "Question-and-Answer",
        "Q&A SESSION",
        "Q & A",
        "Q and A"
    ]
    
    # Look for Q&A section
    lower_text = transcript.lower()
    
    for indicator in qa_indicators:
        if indicator.lower() in lower_text:
            # Split at the indicator
            parts = transcript.split(indicator, 1)
            if len(parts) > 1:
                return parts[1].strip()
    
    # If no clear indicator, try to detect based on Q: and A: pattern
    if re.search(r'\b[QA]\s*:', transcript):
        # Find the first occurrence of Q: or A:
        match = re.search(r'\b[QA]\s*:', transcript)
        if match:
            return transcript[match.start():].strip()
    
    # If no Q&A section detected, return empty string
    return ""

def extract_questions(qa_text: str) -> List[str]:
    """
    Extract analyst questions from the Q&A section.
    
    Args:
        qa_text: Q&A section text
        
    Returns:
        List of extracted questions
    """
    questions = []
    
    # Look for patterns like "Q:" or "Question:" or analyst names followed by question
    question_pattern = r'(?:Q\s*:|Question\s*:|(?:[A-Z][a-z]+\s+){1,3}(?:from|of)\s+(?:[A-Z][a-z]+\s+){1,3}:)(.+?)(?=(?:A\s*:|Answer\s*:|Q\s*:|Question\s*:|$))'
    
    matches = re.findall(question_pattern, qa_text, re.DOTALL)
    
    for match in matches:
        # Clean up the extracted question
        question = match.strip()
        if question:
            questions.append(question)
    
    # If the pattern matching didn't work, try simpler approach
    if not questions:
        # Split by line breaks and look for lines starting with Q:
        lines = qa_text.split('\n')
        current_question = ""
        
        for line in lines:
            if line.strip().startswith('Q:'):
                if current_question:
                    questions.append(current_question.strip())
                current_question = line.strip()[2:].strip()
            elif current_question and not line.strip().startswith('A:'):
                current_question += " " + line.strip()
        
        # Add the last question if it exists
        if current_question:
            questions.append(current_question.strip())
    
    return questions

def extract_answers(qa_text: str) -> List[str]:
    """
    Extract management answers from the Q&A section.
    
    Args:
        qa_text: Q&A section text
        
    Returns:
        List of extracted answers
    """
    answers = []
    
    # Look for patterns like "A:" or "Answer:" followed by text
    answer_pattern = r'(?:A\s*:|Answer\s*:)(.+?)(?=(?:Q\s*:|Question\s*:|A\s*:|Answer\s*:|$))'
    
    matches = re.findall(answer_pattern, qa_text, re.DOTALL)
    
    for match in matches:
        # Clean up the extracted answer
        answer = match.strip()
        if answer:
            answers.append(answer)
    
    # If the pattern matching didn't work, try simpler approach
    if not answers:
        # Split by line breaks and look for lines starting with A:
        lines = qa_text.split('\n')
        current_answer = ""
        
        for line in lines:
            if line.strip().startswith('A:'):
                if current_answer:
                    answers.append(current_answer.strip())
                current_answer = line.strip()[2:].strip()
            elif current_answer and not line.strip().startswith('Q:'):
                current_answer += " " + line.strip()
        
        # Add the last answer if it exists
        if current_answer:
            answers.append(current_answer.strip())
    
    return answers

def extract_speakers(transcript: str) -> Dict[str, List[str]]:
    """
    Extract passages by speaker from the transcript.
    
    Args:
        transcript: Full earnings call transcript
        
    Returns:
        Dictionary mapping speakers to their statements
    """
    speakers = {}
    
    # Look for speaker patterns (names followed by colon)
    speaker_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\s*:'
    
    # Find all potential speakers
    potential_speakers = re.findall(speaker_pattern, transcript)
    
    # For each potential speaker, extract their statements
    for speaker in set(potential_speakers):
        # Pattern to extract this speaker's statements
        pattern = f'{re.escape(speaker)}\\s*:(.+?)(?=(?:[A-Z][a-z]+(?:\\s+[A-Z][a-z]+){{1,2}}\\s*:|$))'
        
        statements = re.findall(pattern, transcript, re.DOTALL)
        
        if statements:
            speakers[speaker] = [stmt.strip() for stmt in statements]
    
    return speakers

# ==================== LANGUAGE PATTERN ANALYSIS FUNCTIONS ====================

def detect_uncertainty(text: str) -> Dict[str, Any]:
    """
    Detect uncertainty language in text and return a score and key phrases.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary with uncertainty score and found terms
    """
    # Dictionary of uncertainty terms with weights
    uncertainty_terms = {
        'may': 0.7, 'might': 0.7, 'could': 0.6, 'possibly': 0.8, 
        'uncertain': 1.0, 'unclear': 0.9, 'not sure': 0.9,
        'potential': 0.6, 'risk': 0.7, 'doubt': 0.9,
        'unpredictable': 1.0, 'volatility': 0.8, 'assumption': 0.7,
        'dependent': 0.6, 'if': 0.5, 'contingent': 0.8, 'tentative': 0.9,
        'speculative': 0.9, 'outlook': 0.5, 'expect': 0.4, 
        'anticipate': 0.5, 'believe': 0.4, 'estimate': 0.6,
        'seems': 0.7, 'appears': 0.6, 'approximately': 0.5,
        'around': 0.4, 'roughly': 0.5, 'about': 0.4
    }
    
    # Uncertainty phrases (with higher weights)
    uncertainty_phrases = {
        'not certain': 1.0, 'don\'t know': 1.0, 'hard to predict': 0.9,
        'difficult to estimate': 0.9, 'too early to tell': 0.9,
        'no clarity': 1.0, 'cannot predict': 1.0, 'subject to change': 0.8,
        'impossible to determine': 1.0, 'yet to be determined': 0.9,
        'still evaluating': 0.8, 'under consideration': 0.7,
        'no guarantee': 0.9, 'not guaranteed': 0.9, 'not confident': 0.9
    }
    
    # Simple implementation without complex NLP
    text_lower = text.lower()
    found_terms = []
    uncertainty_score = 0
    
    # Check for individual terms
    for term, weight in uncertainty_terms.items():
        # Use word boundaries to avoid partial matches
        matches = re.findall(r'\b' + re.escape(term) + r'\b', text_lower)
        count = len(matches)
        
        if count > 0:
            found_terms.append({'term': term, 'count': count, 'weight': weight})
            uncertainty_score += count * weight
    
    # Check for phrases
    for phrase, weight in uncertainty_phrases.items():
        count = text_lower.count(phrase)
        if count > 0:
            found_terms.append({'term': phrase, 'count': count, 'weight': weight})
            uncertainty_score += count * weight
    
    # Normalize by text length
    words = len(text.split())
    normalized_score = (uncertainty_score / words) * 1000 if words > 0 else 0
    
    # Sort terms by count * weight (importance)
    found_terms.sort(key=lambda x: x['count'] * x['weight'], reverse=True)
    
    return {
        'score': normalized_score,
        'found_terms': found_terms[:10],  # Return top 10 terms
        'interpretation': interpret_uncertainty_score(normalized_score)
    }

def interpret_uncertainty_score(score: float) -> str:
    """
    Interpret the uncertainty score.
    
    Args:
        score: Normalized uncertainty score
        
    Returns:
        Interpretation string
    """
    if score < 5:
        return "Very Low: Communication shows high confidence with minimal uncertainty language."
    elif score < 10:
        return "Low: Communication shows confidence with little hedging or uncertainty."
    elif score < 20:
        return "Moderate: Some uncertainty language present, typical for forward-looking statements."
    elif score < 30:
        return "High: Significant uncertainty language, suggesting caution or limited visibility."
    else:
        return "Very High: Extensive uncertainty language, indicating potential concerns or limited confidence."

def categorize_topics(text: str, custom_topics: Optional[Dict[str, List[str]]] = None) -> Dict[str, float]:
    """
    Categorize text by predefined business topics.
    
    Args:
        text: Text to analyze
        custom_topics: Optional dictionary of custom topics and their associated terms
        
    Returns:
        Dictionary mapping topics to their scores
    """
    # Default topic categories and associated terms
    default_topics = {
        'revenue': ['revenue', 'sales', 'growth', 'top line', 'demand', 'orders', 'bookings'],
        'margins': ['margin', 'profitability', 'cost', 'expense', 'pricing', 'efficiency'],
        'competition': ['competition', 'competitor', 'market share', 'landscape', 'differentiation'],
        'products': ['product', 'pipeline', 'launch', 'innovation', 'r&d', 'development', 'release'],
        'operations': ['operations', 'production', 'supply chain', 'manufacturing', 'logistics'],
        'guidance': ['guidance', 'outlook', 'forecast', 'expect', 'next quarter', 'next year'],
        'risks': ['risk', 'challenge', 'headwind', 'concern', 'issue', 'problem', 'difficulty'],
        'opportunities': ['opportunity', 'tailwind', 'potential', 'upside', 'advantage', 'benefit'],
        'strategy': ['strategy', 'strategic', 'long-term', 'initiative', 'transformation', 'vision'],
        'investment': ['investment', 'capital', 'spend', 'allocation', 'return', 'roi']
    }
    
    # Use custom topics if provided, otherwise use defaults
    topics = custom_topics if custom_topics else default_topics
    
    # Prepare text
    text_lower = text.lower()
    words = len(text.split())
    
    # Score each topic based on term frequency
    topic_scores = {}
    
    for topic, terms in topics.items():
        score = 0
        for term in terms:
            # Use word boundaries for more accurate matching
            matches = re.findall(r'\b' + re.escape(term) + r'\b', text_lower)
            score += len(matches)
        
        # Normalize by text length
        topic_scores[topic] = (score / words) * 1000 if words > 0 else 0
    
    return topic_scores

def detect_emphasis_changes(current_text: str, previous_text: str) -> List[Dict[str, Any]]:
    """
    Detect shifts in emphasis compared to previous text.
    
    Args:
        current_text: Current text document
        previous_text: Previous text document for comparison
        
    Returns:
        List of terms with their frequency changes
    """
    # Get topic scores for both texts
    current_topics = categorize_topics(current_text)
    previous_topics = categorize_topics(previous_text)
    
    # Calculate changes
    changes = []
    
    for topic, current_score in current_topics.items():
        previous_score = previous_topics.get(topic, 0)
        
        # Calculate absolute and percentage change
        abs_change = current_score - previous_score
        if previous_score > 0:
            pct_change = (abs_change / previous_score) * 100
        else:
            pct_change = float('inf') if current_score > 0 else 0
        
        changes.append({
            'topic': topic,
            'current_score': current_score,
            'previous_score': previous_score,
            'abs_change': abs_change,
            'pct_change': pct_change
        })
    
    # Sort by absolute percentage change (descending)
    changes.sort(key=lambda x: abs(x['pct_change']), reverse=True)
    
    return changes

def analyze_comparative_language(text: str) -> Dict[str, Any]:
    """
    Analyze comparative language patterns (year-over-year, quarter-over-quarter references).
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary with comparative language analysis
    """
    # Regular expressions for different types of comparisons
    patterns = {
        'year_over_year': [
            r'\byear[\s-]*over[\s-]*year\b', r'\by[\s-]*o[\s-]*y\b',
            r'\bversus last year\b', r'\bcompared to last year\b',
            r'\bfrom a year ago\b', r'\byear[-\s]on[-\s]year\b',
            r'\bannual\s+growth\b', r'\bgrew\s+.*\s+from last year\b'
        ],
        'quarter_over_quarter': [
            r'\bquarter[\s-]*over[\s-]*quarter\b', r'\bq[\s-]*o[\s-]*q\b',
            r'\bsequential\b', r'\bversus last quarter\b',
            r'\bcompared to last quarter\b', r'\bfrom the previous quarter\b',
            r'\bquarter[-\s]on[-\s]quarter\b', r'\bsequentially\b'
        ],
        'guidance': [
            r'\bguidance\b', r'\boutlook\b', r'\bforecast\b', r'\bprojection\b',
            r'\banticipate\b', r'\bexpect\b', r'\bnext quarter\b', r'\bnext year\b',
            r'\bfuture\b', r'\bupcoming\b', r'\blong[\s-]*term\b'
        ],
        'trend': [
            r'\btrend\b', r'\btrends\b', r'\btrending\b', r'\bcontinued\b',
            r'\bcontinuing\b', r'\bmomentum\b', r'\btrajectory\b',
            r'\bpattern\b', r'\bhistorical\b', r'\bhistorically\b'
        ]
    }
    
    results = {}
    
    # Check for matches
    for category, expressions in patterns.items():
        matches = []
        
        for pattern in expressions:
            for match in re.finditer(pattern, text.lower()):
                # Get context (words around the match)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                
                matches.append({
                    'term': match.group(0),
                    'context': context
                })
        
        results[category] = {
            'count': len(matches),
            'examples': matches[:5]  # Limit to 5 examples
        }
    
    # Calculate overall comparative language score
    total_matches = sum(result['count'] for result in results.values())
    words = len(text.split())
    comparative_score = (total_matches / words) * 1000 if words > 0 else 0
    
    return {
        'categories': results,
        'total_count': total_matches,
        'comparative_score': comparative_score
    }

# ==================== EARNINGS CALL ANALYSIS FUNCTIONS ====================

def categorize_analyst_questions(qa_text: str) -> List[Dict[str, Any]]:
    """
    Identify and categorize analyst questions by topic.
    
    Args:
        qa_text: Q&A section text
        
    Returns:
        List of dictionaries with questions and their categories
    """
    # Extract questions
    questions = extract_questions(qa_text)
    
    # Categorize each question
    categorized_questions = []
    
    for question in questions:
        # Get topics for this question
        topic_scores = categorize_topics(question)
        
        # Filter to topics that score above threshold
        relevant_topics = {topic: score for topic, score in topic_scores.items() if score > 5}
        
        # Sort topics by score (descending)
        sorted_topics = sorted(relevant_topics.items(), key=lambda x: x[1], reverse=True)
        
        # Detect uncertainty in the question
        uncertainty = detect_uncertainty(question)
        
        categorized_questions.append({
            'text': question,
            'topics': sorted_topics[:3],  # Top 3 topics
            'uncertainty_score': uncertainty['score'],
            'length': len(question.split())
        })
    
    return categorized_questions

def analyze_management_language(text: str) -> Dict[str, Any]:
    """
    Analyze management language patterns in earnings call.
    
    Args:
        text: Management presentation or answers
        
    Returns:
        Dictionary with language pattern analysis
    """
    # Analyze several language aspects
    results = {}
    
    # Uncertainty analysis
    results['uncertainty'] = detect_uncertainty(text)
    
    # Topic analysis
    results['topics'] = categorize_topics(text)
    
    # Comparative language
    results['comparative'] = analyze_comparative_language(text)
    
    # Additional patterns specific to management language
    accomplishment_terms = [
        'achieved', 'delivered', 'exceeded', 'outperformed', 'successful',
        'strong', 'robust', 'significant', 'substantial', 'impressive',
        'record', 'milestone', 'accomplishment', 'success', 'proud'
    ]
    
    challenge_terms = [
        'challenging', 'difficult', 'headwind', 'obstacle', 'hurdle',
        'issue', 'problem', 'concern', 'disappointing', 'below',
        'miss', 'missed', 'shortfall', 'decline', 'decreased'
    ]
    
    # Count occurrences
    text_lower = text.lower()
    accomplishment_count = sum(text_lower.count(f" {term} ") for term in accomplishment_terms)
    challenge_count = sum(text_lower.count(f" {term} ") for term in challenge_terms)
    
    # Calculate ratio
    total = accomplishment_count + challenge_count
    if total > 0:
        tone_ratio = accomplishment_count / total
    else:
        tone_ratio = 0.5  # Neutral if no terms found
    
    results['tone'] = {
        'accomplishment_count': accomplishment_count,
        'challenge_count': challenge_count,
        'tone_ratio': tone_ratio,
        'interpretation': interpret_tone_ratio(tone_ratio)
    }
    
    return results

def interpret_tone_ratio(ratio: float) -> str:
    """
    Interpret the tone ratio.
    
    Args:
        ratio: Tone ratio (0-1)
        
    Returns:
        Interpretation string
    """
    if ratio > 0.8:
        return "Very Positive: Communication heavily emphasizes accomplishments with minimal mention of challenges."
    elif ratio > 0.65:
        return "Positive: Communication emphasizes accomplishments more than challenges."
    elif ratio > 0.45:
        return "Balanced: Communication addresses both accomplishments and challenges fairly equally."
    elif ratio > 0.3:
        return "Cautious: Communication emphasizes challenges more than accomplishments."
    else:
        return "Defensive: Communication heavily focused on challenges with minimal mention of accomplishments."

def extract_guidance(text: str) -> List[Dict[str, str]]:
    """
    Extract forward-looking guidance statements.
    
    Args:
        text: Text to analyze
        
    Returns:
        List of extracted guidance statements with context
    """
    # Guidance indicator phrases
    guidance_phrases = [
        "guidance", "expect", "anticipate", "outlook", "forecast",
        "project", "estimate", "next quarter", "next year", "forward looking",
        "future", "upcoming", "will be", "going forward"
    ]
    
    # Build regex pattern
    pattern_str = r'(?:[^.!?]*(?:' + '|'.join(guidance_phrases) + r')[^.!?]*[.!?])'
    
    # Find all matching sentences
    matches = re.findall(pattern_str, text, re.IGNORECASE)
    
    # Clean and deduplicate results
    guidance_statements = []
    seen_statements = set()
    
    for match in matches:
        # Clean up whitespace
        clean_match = re.sub(r'\s+', ' ', match).strip()
        
        # Skip if too short or already seen
        if len(clean_match) < 20 or clean_match in seen_statements:
            continue
        
        # Identify which guidance phrase was matched
        matched_phrase = ""
        for phrase in guidance_phrases:
            if phrase.lower() in clean_match.lower():
                matched_phrase = phrase
                break
        
        guidance_statements.append({
            'statement': clean_match,
            'trigger_phrase': matched_phrase
        })
        
        seen_statements.add(clean_match)
    
    return guidance_statements

# ==================== SIGNAL DETECTION FUNCTIONS ====================

def detect_warning_signals(text: str, previous_text: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Detect potential warning signals in the text.
    
    Args:
        text: Current text to analyze
        previous_text: Optional previous text for comparison
        
    Returns:
        List of detected warning signals
    """
    warning_signals = []
    
    # Check for high uncertainty
    uncertainty = detect_uncertainty(text)
    if uncertainty['score'] > 25:
        warning_signals.append({
            'type': 'high_uncertainty',
            'severity': 'medium' if uncertainty['score'] < 35 else 'high',
            'description': f"High uncertainty language detected (score: {uncertainty['score']:.1f})",
            'evidence': [term['term'] for term in uncertainty['found_terms'][:3]]
        })
    
    # Check for emphasis on risks/challenges
    topics = categorize_topics(text)
    if topics.get('risks', 0) > 15:
        warning_signals.append({
            'type': 'risk_emphasis',
            'severity': 'medium' if topics['risks'] < 25 else 'high',
            'description': f"Significant emphasis on risks and challenges (score: {topics['risks']:.1f})",
            'evidence': []  # Would need to extract specific risk mentions
        })
    
    # Analyze management tone
    management_analysis = analyze_management_language(text)
    if management_analysis['tone']['tone_ratio'] < 0.4:
        warning_signals.append({
            'type': 'negative_tone',
            'severity': 'medium' if management_analysis['tone']['tone_ratio'] > 0.3 else 'high',
            'description': f"Cautious or defensive management tone (ratio: {management_analysis['tone']['tone_ratio']:.2f})",
            'evidence': []
        })
    
    # Check for shifts in emphasis if previous text is available
    if previous_text:
        emphasis_changes = detect_emphasis_changes(text, previous_text)
        
        # Look for significant negative changes in key areas
        for change in emphasis_changes:
            # Significant decrease in positive areas
            if change['topic'] in ['opportunities', 'strategy', 'products'] and change['pct_change'] < -50:
                warning_signals.append({
                    'type': 'reduced_emphasis',
                    'severity': 'medium',
                    'description': f"Significantly reduced emphasis on {change['topic']} (-{abs(change['pct_change']):.0f}%)",
                    'evidence': []
                })
            
            # Significant increase in negative areas
            if change['topic'] in ['risks', 'competition'] and change['pct_change'] > 50:
                warning_signals.append({
                    'type': 'increased_concern',
                    'severity': 'medium',
                    'description': f"Significantly increased emphasis on {change['topic']} (+{change['pct_change']:.0f}%)",
                    'evidence': []
                })
    
    # Extract and analyze guidance statements
    guidance_statements = extract_guidance(text)
    lowered_guidance_count = 0
    
    for statement in guidance_statements:
        # Check for phrases indicating lowered guidance
        lower_indicators = ['lower', 'below', 'reduce', 'less than', 'not meet', 'challenging', 'headwind', 'slower']
        
        if any(indicator in statement['statement'].lower() for indicator in lower_indicators):
            lowered_guidance_count += 1
    
    if lowered_guidance_count >= 2:
        warning_signals.append({
            'type': 'reduced_guidance',
            'severity': 'high',
            'description': f"Multiple statements suggesting lowered guidance or expectations",
            'evidence': []
        })
    
    return warning_signals

def detect_opportunity_signals(text: str, previous_text: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Detect potential opportunity signals in the text.
    
    Args:
        text: Current text to analyze
        previous_text: Optional previous text for comparison
        
    Returns:
        List of detected opportunity signals
    """
    opportunity_signals = []
    
    # Check for low uncertainty (high confidence)
    uncertainty = detect_uncertainty(text)
    if uncertainty['score'] < 10:
        opportunity_signals.append({
            'type': 'high_confidence',
            'strength': 'medium' if uncertainty['score'] > 5 else 'high',
            'description': f"High confidence language with minimal uncertainty (score: {uncertainty['score']:.1f})",
            'evidence': []
        })
    
    # Check for emphasis on opportunities/growth
    topics = categorize_topics(text)
    if topics.get('opportunities', 0) > 15 or topics.get('revenue', 0) > 20:
        topic = 'opportunities' if topics.get('opportunities', 0) > topics.get('revenue', 0) else 'revenue'
        opportunity_signals.append({
            'type': 'opportunity_emphasis',
            'strength': 'medium' if topics[topic] < 25 else 'high',
            'description': f"Significant emphasis on {topic} and growth (score: {topics[topic]:.1f})",
            'evidence': []
        })
    
    # Analyze management tone
    management_analysis = analyze_management_language(text)
    if management_analysis['tone']['tone_ratio'] > 0.6:
        opportunity_signals.append({
            'type': 'positive_tone',
            'strength': 'medium' if management_analysis['tone']['tone_ratio'] < 0.75 else 'high',
            'description': f"Positive management tone (ratio: {management_analysis['tone']['tone_ratio']:.2f})",
            'evidence': []
        })
    
    # Check for shifts in emphasis if previous text is available
    if previous_text:
        emphasis_changes = detect_emphasis_changes(text, previous_text)
        
        # Look for significant positive changes in key areas
        for change in emphasis_changes:
            # Significant increase in positive areas
            if change['topic'] in ['opportunities', 'strategy', 'products'] and change['pct_change'] > 50:
                opportunity_signals.append({
                    'type': 'increased_emphasis',
                    'strength': 'medium',
                    'description': f"Significantly increased emphasis on {change['topic']} (+{change['pct_change']:.0f}%)",
                    'evidence': []
                })
            
            # Significant decrease in negative areas
            if change['topic'] in ['risks', 'competition'] and change['pct_change'] < -50:
                opportunity_signals.append({
                    'type': 'reduced_concern',
                    'strength': 'medium',
                    'description': f"Significantly reduced emphasis on {change['topic']} (-{abs(change['pct_change']):.0f}%)",
                    'evidence': []
                })
    
    # Extract and analyze guidance statements
    guidance_statements = extract_guidance(text)
    raised_guidance_count = 0
    
    for statement in guidance_statements:
        # Check for phrases indicating raised guidance
        higher_indicators = ['higher', 'above', 'increase', 'exceed', 'better than', 'stronger', 'growth', 'outperform']
        
        if any(indicator in statement['statement'].lower() for indicator in higher_indicators):
            raised_guidance_count += 1
    
    if raised_guidance_count >= 2:
        opportunity_signals.append({
            'type': 'raised_guidance',
            'strength': 'high',
            'description': f"Multiple statements suggesting raised guidance or expectations",
            'evidence': []
        })
    
    return opportunity_signals

# ==================== VISUALIZATION FUNCTIONS ====================

def create_sentiment_timeline(text: str, window_size: int = 200) -> go.Figure:
    """
    Create a sentiment timeline visualization for a document.
    
    Args:
        text: Text to analyze
        window_size: Size of the sliding window in words
        
    Returns:
        Plotly figure with sentiment timeline
    """
    # Split text into words
    words = text.split()
    
    if len(words) < window_size:
        # Text too short for meaningful analysis
        return None
    
    # Create sliding windows
    windows = []
    positions = []
    
    for i in range(0, len(words) - window_size, window_size // 2):  # 50% overlap
        window_text = ' '.join(words[i:i+window_size])
        windows.append(window_text)
        positions.append(i / len(words))  # Position as percentage through document
    
    # Analyze sentiment and uncertainty for each window
    sentiments = []
    uncertainties = []
    
    for window in windows:
        # Sentiment would come from sentiment analysis function (not implemented)
        # For now, we'll use uncertainty as a proxy
        uncertainty = detect_uncertainty(window)
        topic_scores = categorize_topics(window)
        
        # Calculate pseudo-sentiment based on topic ratios
        positive_score = topic_scores.get('opportunities', 0) + topic_scores.get('revenue', 0)
        negative_score = topic_scores.get('risks', 0) + uncertainty['score'] / 5
        
        sentiment = (positive_score - negative_score) / (positive_score + negative_score) if (positive_score + negative_score) > 0 else 0
        sentiment = max(-1, min(1, sentiment))  # Clamp to [-1, 1]
        
        sentiments.append(sentiment)
        uncertainties.append(uncertainty['score'])
    
    # Create visualization
    fig = go.Figure()
    
    # Add sentiment line
    fig.add_trace(go.Scatter(
        x=[p * 100 for p in positions],  # Convert to percentage
        y=sentiments,
        mode='lines',
        name='Sentiment',
        line=dict(color='#4CAF50', width=3)
    ))
    
    # Add uncertainty line
    fig.add_trace(go.Scatter(
        x=[p * 100 for p in positions],  # Convert to percentage
        y=[u / 100 for u in uncertainties],  # Scale down to similar range as sentiment
        mode='lines',
        name='Uncertainty',
        line=dict(color='#F44336', width=3, dash='dash')
    ))
    
    # Update layout
    fig.update_layout(
        title="Document Sentiment & Uncertainty Timeline",
        xaxis_title="Position in Document (%)",
        yaxis_title="Score",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        yaxis=dict(
            range=[-1, 1]
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(30,30,30,0.3)',
        font=dict(color='white')
    )
    
    return fig

def create_topic_distribution(text: str) -> go.Figure:
    """
    Create a visualization of topic distribution in the document.
    
    Args:
        text: Text to analyze
        
    Returns:
        Plotly figure with topic distribution
    """
    # Get topic scores
    topic_scores = categorize_topics(text)
    
    # Sort by score (descending)
    sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Prepare data for visualization
    topics = [t[0].capitalize() for t in sorted_topics]
    scores = [t[1] for t in sorted_topics]
    
    # Create bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=topics,
        y=scores,
        marker_color='#2196F3'
    ))
    
    # Update layout
    fig.update_layout(
        title="Topic Distribution",
        xaxis_title="Topic",
        yaxis_title="Score",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(30,30,30,0.3)',
        font=dict(color='white')
    )
    
    return fig