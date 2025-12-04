import logging
import re
from typing import Dict, List, Any, Tuple
import nltk
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('vader_lexicon', quiet=True)
except Exception as e:
    print(f"NLTK download warning: {e}")

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Analyzes sentiment of social media posts and comments."""
    
    def __init__(self):
        """Initialize sentiment analysis tools."""
        self.vader_analyzer = SentimentIntensityAnalyzer()
        
        # Gusto-specific identifiers
        self.gusto_identifiers = [
            'gusto', 'gusto payroll', 'gusto.com', 'gustohq',
            'gusto software', 'gusto platform', 'gusto hr'
        ]
        
        # Competitor identifiers for sentiment analysis
        self.competitor_identifiers = {
            'adp': ['adp', 'adp payroll', 'adp workforce', 'adp run'],
            'paychex': ['paychex', 'paychex flex', 'paychex payroll'],
            'quickbooks': ['quickbooks', 'quickbooks payroll', 'qb payroll', 'intuit payroll'],
            'bamboohr': ['bamboohr', 'bamboo hr', 'bamboo'],
            'rippling': ['rippling', 'rippling payroll', 'rippling hr'],
            'workday': ['workday', 'workday payroll', 'workday hcm'],
            'deel': ['deel', 'deel payroll', 'deel global'],
            'justworks': ['justworks', 'just works', 'justworks payroll']
        }
        
        self.business_keywords = {
            'positive': [
                'love', 'great', 'excellent', 'amazing', 'fantastic', 'perfect', 'best',
                'awesome', 'wonderful', 'outstanding', 'superb', 'incredible', 'brilliant',
                'efficient', 'user-friendly', 'intuitive', 'seamless', 'smooth', 'reliable',
                'helpful', 'responsive', 'professional', 'recommend', 'satisfied', 'happy',
                'switched to', 'better than', 'impressed', 'works well', 'easy to use',
                'without issues', 'without any issues', 'no issues', 'no problems',
                'working fine', 'working well', 'been good', 'been great'
            ],
            'negative': [
                'hate', 'terrible', 'awful', 'horrible', 'worst', 'bad', 'disappointing',
                'frustrating', 'annoying', 'broken', 'buggy', 'slow', 'confusing',
                'complicated', 'expensive', 'overpriced', 'unreliable', 'unresponsive',
                'unprofessional', 'avoid', 'regret', 'unsatisfied', 'unhappy', 'poor',
                'stay away', 'stay away from', 'don\'t use', 'don\'t recommend', 'nightmare',
                'disaster', 'useless', 'waste', 'scam', 'rip off', 'rip-off'
            ]
        }
    
    def clean_text(self, text: str) -> str:
        """
        Clean and preprocess text for sentiment analysis.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove Reddit-specific formatting
        text = re.sub(r'/u/\w+', '', text)  # Remove usernames
        text = re.sub(r'/r/\w+', '', text)  # Remove subreddit names
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Remove bold formatting
        text = re.sub(r'\*(.+?)\*', r'\1', text)  # Remove italic formatting
        
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_gusto_segments(self, text: str) -> List[str]:
        """
        Extract sentences and segments that specifically mention Gusto with enhanced context filtering.
        
        Args:
            text: Full text to analyze
            
        Returns:
            List of text segments that mention Gusto (excluding competitor-focused comparisons)
        """
        if not text:
            return []
        
        import nltk
        try:
            # Split into sentences
            sentences = nltk.sent_tokenize(text.lower())
        except:
            # Fallback to simple splitting if NLTK fails
            sentences = [s.strip() + '.' for s in text.lower().split('.') if s.strip()]
        
        gusto_segments = []
        
        # Competitor names that might create noise in sentiment analysis
        competitors = ['adp', 'paychex', 'quickbooks', 'bamboohr', 'rippling', 'workday', 'deel', 'justworks']
        
        for sentence in sentences:
            # Check if sentence contains any Gusto identifier
            if any(identifier in sentence for identifier in self.gusto_identifiers):
                
                # Special handling for sentences with both Gusto and competitors
                has_competitor = any(competitor in sentence for competitor in competitors)
                
                if has_competitor:
                    # Extract only the Gusto-specific part of mixed sentences
                    gusto_part = self._extract_gusto_specific_clause(sentence)
                    if gusto_part:
                        gusto_segments.append(gusto_part)
                else:
                    # No competitors mentioned, use the full sentence
                    gusto_segments.append(sentence)
        
        # If no specific sentences found, but text contains Gusto, use context window
        if not gusto_segments and any(identifier in text.lower() for identifier in self.gusto_identifiers):
            words = text.split()
            for i, word in enumerate(words):
                if any(identifier in word.lower() for identifier in self.gusto_identifiers):
                    # Extract context window around Gusto mention (±8 words for better focus)
                    start = max(0, i - 8)
                    end = min(len(words), i + 9)
                    context = ' '.join(words[start:end])
                    gusto_segments.append(context)
        
        return gusto_segments
    
    def _extract_gusto_specific_clause(self, sentence: str) -> str:
        """
        Extract only the Gusto-related clause from a sentence that mentions multiple platforms.
        
        Args:
            sentence: Sentence containing both Gusto and competitor mentions
            
        Returns:
            Gusto-specific clause or empty string if not found
        """
        # Common patterns for Gusto-specific clauses
        gusto_patterns = [
            # Positive comparisons
            r'(gusto.*?(?:without.*?issues?|works?.*?well|better|good|great|excellent))',
            r'((?:using|used).*?gusto.*?(?:without.*?issues?|successfully|fine|well))',
            r'((?:switched to|moved to|chose).*?gusto.*?(?:and|because).*?(?:love|like|better|good))',
            
            # Neutral/factual mentions
            r'(using.*?gusto.*?for.*?years?.*?without.*?issues?)',
            r'(gusto.*?for.*?years?.*?(?:fine|okay|works?))',
            
            # Extract clause around Gusto mention with positive/neutral context
            r'((?:[^.!?]*)?gusto(?:[^.!?]*)?(?:without.*?issues?|works?|fine|good|years?)(?:[^.!?]*)?)'
        ]
        
        for pattern in gusto_patterns:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                clause = match.group(1).strip()
                # Clean up the clause
                clause = re.sub(r'^[,\s]+|[,\s]+$', '', clause)
                return clause
        
        # Fallback: extract clause around Gusto mention (basic approach)
        words = sentence.split()
        gusto_index = -1
        for i, word in enumerate(words):
            if 'gusto' in word.lower():
                gusto_index = i
                break
        
        if gusto_index != -1:
            # Extract a smaller context around Gusto to avoid competitor sentiment
            start = max(0, gusto_index - 5)
            end = min(len(words), gusto_index + 6)
            clause = ' '.join(words[start:end])
            return clause
        
        return ""
    
    def extract_competitor_segments(self, text: str, competitor: str) -> List[str]:
        """
        Extract sentences and segments that specifically mention a competitor.
        
        Args:
            text: Full text to analyze
            competitor: Competitor name (e.g., 'adp', 'paychex', etc.)
            
        Returns:
            List of text segments that mention the competitor
        """
        if not text or competitor not in self.competitor_identifiers:
            return []
        
        competitor_ids = self.competitor_identifiers[competitor]
        
        import nltk
        try:
            # Split into sentences
            sentences = nltk.sent_tokenize(text.lower())
        except:
            # Fallback to simple splitting if NLTK fails
            sentences = [s.strip() + '.' for s in text.lower().split('.') if s.strip()]
        
        competitor_segments = []
        
        # All competitors (to identify mixed mentions)
        all_competitors = ['adp', 'paychex', 'quickbooks', 'bamboohr', 'rippling', 'workday', 'deel', 'justworks']
        other_competitors = [c for c in all_competitors if c != competitor] + ['gusto']
        
        for sentence in sentences:
            # Check if sentence contains any competitor identifier
            if any(identifier in sentence for identifier in competitor_ids):
                
                # Special handling for sentences with multiple platforms
                has_other_platform = any(other in sentence for other in other_competitors)
                
                if has_other_platform:
                    # Extract only the competitor-specific part
                    competitor_part = self._extract_competitor_specific_clause(sentence, competitor, competitor_ids)
                    if competitor_part:
                        competitor_segments.append(competitor_part)
                else:
                    # No other platforms mentioned, use the full sentence
                    competitor_segments.append(sentence)
        
        # If no specific sentences found, but text contains competitor, use context window
        if not competitor_segments and any(identifier in text.lower() for identifier in competitor_ids):
            words = text.split()
            for i, word in enumerate(words):
                if any(identifier in word.lower() for identifier in competitor_ids):
                    # Extract context window around competitor mention (±8 words)
                    start = max(0, i - 8)
                    end = min(len(words), i + 9)
                    context = ' '.join(words[start:end])
                    competitor_segments.append(context)
        
        return competitor_segments
    
    def _extract_competitor_specific_clause(self, sentence: str, competitor: str, competitor_ids: List[str]) -> str:
        """
        Extract only the competitor-related clause from a sentence that mentions multiple platforms.
        
        Args:
            sentence: Sentence containing multiple platform mentions
            competitor: Competitor name
            competitor_ids: List of competitor identifiers
            
        Returns:
            Competitor-specific clause or empty string if not found
        """
        import re
        
        # Find the competitor mention and extract focused context
        for comp_id in competitor_ids:
            if comp_id in sentence:
                # Common patterns for competitor-specific clauses
                patterns = [
                    # Theme-relevant patterns
                    rf'({comp_id}.*?(?:costs?|pric\w+|fees?|expensive|cheap|affordable))(?=\s+(?:but|then|however|switch|gusto)|$)',
                    rf'({comp_id}.*?(?:features?|functionality|capabilit\w+|tools?))(?=\s+(?:but|then|however|switch|gusto)|$)',
                    rf'({comp_id}.*?(?:interface|ui|ux|user|experience|easy|difficult))(?=\s+(?:but|then|however|switch|gusto)|$)',
                    rf'({comp_id}.*?(?:support|service|help|customer|staff))(?=\s+(?:but|then|however|switch|gusto)|$)',
                    rf'({comp_id}.*?(?:integration|connect|sync|api|compatibility))(?=\s+(?:but|then|however|switch|gusto)|$)',
                    rf'({comp_id}.*?(?:payroll|pay|processing|tax|benefits|hr))(?=\s+(?:but|then|however|switch|gusto)|$)',
                    rf'({comp_id}.*?(?:performance|speed|fast|slow|reliable|stable))(?=\s+(?:but|then|however|switch|gusto)|$)',
                    
                    # General patterns that stop before transitions  
                    rf'((?:switched to|using|used|chose).*?{comp_id}.*?)(?=\s+(?:but|then|however|switch|gusto|\.|,))',
                    rf'({comp_id}.*?(?:is|was|has|had).*?(?:fine|good|great|bad|terrible|awful))(?=\s+(?:but|then|however|switch|gusto|\.|,))',
                    
                    # Capture negative sentiment about competitor
                    rf'((?:switched to|then).*?{comp_id}.*?(?:terrible|awful|bad|expensive|creeping|worst))(?=\s+(?:what|plus|fees|costs|\.|,))',
                    
                    # Simple mentions with immediate context
                    rf'({comp_id}\s+(?:which|that|is|was|has|had)\s+\w+(?:\s+\w+){{0,4}})(?=\s+(?:but|then|however|switch|gusto|for|although|\.|,))',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, sentence, re.IGNORECASE)
                    if match:
                        clause = match.group(1).strip()
                        clause = re.sub(r'^[,\s]+|[,\s]+$', '', clause)
                        if len(clause) > 5:
                            return clause
                
                # Fallback: extract focused context around competitor mention
                words = sentence.split()
                comp_index = -1
                for i, word in enumerate(words):
                    if comp_id in word.lower():
                        comp_index = i
                        break
                
                if comp_index != -1:
                    start = max(0, comp_index - 5)
                    end = min(len(words), comp_index + 6)
                    clause = ' '.join(words[start:end])
                    return clause
        
        return ""
    
    def analyze_competitor_sentiment(self, text: str, competitor: str) -> str:
        """
        Perform sentiment analysis focused on competitor mentions only.
        
        Args:
            text: Text to analyze
            competitor: Competitor name (e.g., 'adp', 'paychex', etc.)
            
        Returns:
            Sentiment label: 'positive', 'negative', or 'neutral'
        """
        if not text or competitor not in self.competitor_identifiers:
            return 'neutral'
        
        # Extract competitor-specific segments
        competitor_segments = self.extract_competitor_segments(text, competitor)
        
        if not competitor_segments:
            return 'neutral'
        
        # Analyze sentiment on combined competitor segments
        combined_text = ' '.join(competitor_segments)
        
        # Get VADER scores
        vader_scores = self.analyze_sentiment_vader(combined_text)
        
        # Get TextBlob scores
        textblob_scores = self.analyze_sentiment_textblob(combined_text)
        
        # Get business context
        business_scores = self.analyze_business_context(combined_text)
        
        # Combine scores with weights
        vader_weight = 0.4
        textblob_weight = 0.3
        business_weight = 0.3
        
        combined_score = (
            vader_scores['compound'] * vader_weight +
            textblob_scores['polarity'] * textblob_weight +
            business_scores['business_sentiment'] * business_weight
        )
        
        # Determine sentiment label with sensitive thresholds
        if combined_score >= 0.05:
            return 'positive'
        elif combined_score <= -0.05:
            return 'negative'
        else:
            return 'neutral'
    
    def get_competitor_sentiment_score(self, text: str, competitor: str) -> float:
        """
        Get a numerical sentiment score focused on competitor mentions only.
        
        Args:
            text: Text to analyze
            competitor: Competitor name
            
        Returns:
            Sentiment score between -1 (very negative) and 1 (very positive)
        """
        if not text or competitor not in self.competitor_identifiers:
            return 0.0
        
        # Extract competitor-specific segments
        competitor_segments = self.extract_competitor_segments(text, competitor)
        
        if not competitor_segments:
            return 0.0
        
        # Analyze sentiment on combined competitor segments
        combined_text = ' '.join(competitor_segments)
        
        # Get VADER scores
        vader_scores = self.analyze_sentiment_vader(combined_text)
        
        # Get TextBlob scores
        textblob_scores = self.analyze_sentiment_textblob(combined_text)
        
        # Get business context
        business_scores = self.analyze_business_context(combined_text)
        
        # Combine scores with weights
        vader_weight = 0.4
        textblob_weight = 0.3
        business_weight = 0.3
        
        combined_score = (
            vader_scores['compound'] * vader_weight +
            textblob_scores['polarity'] * textblob_weight +
            business_scores['business_sentiment'] * business_weight
        )
        
        # Ensure score is within bounds
        return max(-1.0, min(1.0, combined_score))
    
    def analyze_sentiment_vader(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment using VADER sentiment analyzer.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment scores
        """
        cleaned_text = self.clean_text(text)
        scores = self.vader_analyzer.polarity_scores(cleaned_text)
        
        return {
            'compound': scores['compound'],
            'positive': scores['pos'],
            'negative': scores['neg'],
            'neutral': scores['neu']
        }
    
    def analyze_sentiment_textblob(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment using TextBlob.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment scores
        """
        cleaned_text = self.clean_text(text)
        blob = TextBlob(cleaned_text)
        
        return {
            'polarity': blob.sentiment.polarity,  # -1 to 1
            'subjectivity': blob.sentiment.subjectivity  # 0 to 1
        }
    
    def analyze_business_context(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment with business context for payroll/HR software.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with business-specific sentiment analysis
        """
        cleaned_text = self.clean_text(text.lower())
        
        # Count positive and negative business keywords
        pos_count = sum(1 for word in self.business_keywords['positive'] if word in cleaned_text)
        neg_count = sum(1 for word in self.business_keywords['negative'] if word in cleaned_text)
        
        # Calculate business sentiment score
        total_keywords = pos_count + neg_count
        if total_keywords > 0:
            business_sentiment = (pos_count - neg_count) / total_keywords
        else:
            business_sentiment = 0.0
        
        # Identify specific aspects mentioned
        aspects = self._identify_aspects(cleaned_text)
        
        return {
            'business_sentiment': business_sentiment,
            'positive_keywords': pos_count,
            'negative_keywords': neg_count,
            'aspects_mentioned': aspects,
            'confidence': min(total_keywords / 5.0, 1.0)  # Max confidence at 5+ keywords
        }
    
    def _identify_aspects(self, text: str) -> List[str]:
        """
        Identify specific business aspects mentioned in the text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of identified aspects
        """
        aspects = []
        
        aspect_keywords = {
            'pricing': ['price', 'cost', 'expensive', 'cheap', 'affordable', 'fee', 'pricing', 'money'],
            'customer_service': ['support', 'help', 'service', 'representative', 'response', 'staff'],
            'user_interface': ['interface', 'ui', 'design', 'layout', 'navigation', 'user-friendly'],
            'features': ['feature', 'functionality', 'capability', 'option', 'tool'],
            'performance': ['speed', 'fast', 'slow', 'performance', 'lag', 'responsive'],
            'integration': ['integration', 'connect', 'sync', 'api', 'compatibility'],
            'payroll': ['payroll', 'pay', 'salary', 'wage', 'payment', 'direct deposit'],
            'hr_features': ['hr', 'benefits', 'onboarding', 'employee', 'time tracking', 'pto'],
            'reliability': ['reliable', 'stable', 'crash', 'downtime', 'available', 'uptime']
        }
        
        for aspect, keywords in aspect_keywords.items():
            if any(keyword in text for keyword in keywords):
                aspects.append(aspect)
        
        return aspects
    
    def analyze_sentiment(self, text: str) -> str:
        """
        Perform comprehensive sentiment analysis focused on Gusto mentions only.
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment label: 'positive', 'negative', or 'neutral'
        """
        if not text:
            return 'neutral'
        
        # Extract Gusto-specific segments
        gusto_segments = self.extract_gusto_segments(text)
        
        if not gusto_segments:
            # If no Gusto mentions found, return neutral
            return 'neutral'
        
        # Analyze sentiment on combined Gusto segments
        combined_gusto_text = ' '.join(gusto_segments)
        
        # Get VADER scores
        vader_scores = self.analyze_sentiment_vader(combined_gusto_text)
        
        # Get TextBlob scores
        textblob_scores = self.analyze_sentiment_textblob(combined_gusto_text)
        
        # Get business context
        business_scores = self.analyze_business_context(combined_gusto_text)
        
        # Combine scores with weights
        vader_weight = 0.4
        textblob_weight = 0.3
        business_weight = 0.3
        
        combined_score = (
            vader_scores['compound'] * vader_weight +
            textblob_scores['polarity'] * textblob_weight +
            business_scores['business_sentiment'] * business_weight
        )
        
        # Determine sentiment label with more sensitive thresholds
        if combined_score >= 0.05:
            return 'positive'
        elif combined_score <= -0.05:
            return 'negative'
        else:
            return 'neutral'
    
    def get_sentiment_score(self, text: str) -> float:
        """
        Get a numerical sentiment score focused on Gusto mentions only.
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment score between -1 (very negative) and 1 (very positive)
        """
        if not text:
            return 0.0
        
        # Extract Gusto-specific segments
        gusto_segments = self.extract_gusto_segments(text)
        
        if not gusto_segments:
            # If no Gusto mentions found, return neutral
            return 0.0
        
        # Analyze sentiment on combined Gusto segments
        combined_gusto_text = ' '.join(gusto_segments)
        
        # Get VADER scores
        vader_scores = self.analyze_sentiment_vader(combined_gusto_text)
        
        # Get TextBlob scores
        textblob_scores = self.analyze_sentiment_textblob(combined_gusto_text)
        
        # Get business context
        business_scores = self.analyze_business_context(combined_gusto_text)
        
        # Combine scores with weights
        vader_weight = 0.4
        textblob_weight = 0.3
        business_weight = 0.3
        
        combined_score = (
            vader_scores['compound'] * vader_weight +
            textblob_scores['polarity'] * textblob_weight +
            business_scores['business_sentiment'] * business_weight
        )
        
        # Ensure score is within bounds
        return max(-1.0, min(1.0, combined_score))
    
    def analyze_detailed_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Perform detailed sentiment analysis with all metrics.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with comprehensive sentiment analysis
        """
        if not text:
            return {
                'sentiment_label': 'neutral',
                'sentiment_score': 0.0,
                'confidence': 0.0,
                'aspects': [],
                'vader_scores': {},
                'textblob_scores': {},
                'business_scores': {}
            }
        
        # Get all analysis results
        vader_scores = self.analyze_sentiment_vader(text)
        textblob_scores = self.analyze_sentiment_textblob(text)
        business_scores = self.analyze_business_context(text)
        
        # Get combined sentiment
        sentiment_label = self.analyze_sentiment(text)
        sentiment_score = self.get_sentiment_score(text)
        
        # Calculate overall confidence
        confidence = (
            abs(vader_scores['compound']) * 0.4 +
            abs(textblob_scores['polarity']) * 0.3 +
            business_scores['confidence'] * 0.3
        )
        
        return {
            'sentiment_label': sentiment_label,
            'sentiment_score': sentiment_score,
            'confidence': min(confidence, 1.0),
            'aspects': business_scores['aspects_mentioned'],
            'vader_scores': vader_scores,
            'textblob_scores': textblob_scores,
            'business_scores': business_scores
        }
    
    def batch_analyze_sentiment(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze sentiment for a batch of texts.
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of sentiment analysis results
        """
        results = []
        
        for text in texts:
            try:
                result = self.analyze_detailed_sentiment(text)
                results.append(result)
            except Exception as e:
                logger.warning(f"Error analyzing sentiment for text: {e}")
                results.append({
                    'sentiment_label': 'neutral',
                    'sentiment_score': 0.0,
                    'confidence': 0.0,
                    'aspects': [],
                    'error': str(e)
                })
        
        return results 