import logging
import re
from typing import Dict, List, Any, Tuple
from collections import Counter, defaultdict
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import LatentDirichletAllocation
import numpy as np
import pandas as pd

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
except Exception as e:
    print(f"NLTK download warning: {e}")

logger = logging.getLogger(__name__)

class ThemeExtractor:
    """Extracts themes and topics from social media text data."""
    
    def __init__(self):
        """Initialize theme extraction tools."""
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # Gusto-specific identifiers
        self.gusto_identifiers = [
            'gusto', 'gusto payroll', 'gusto.com', 'gustohq',
            'gusto software', 'gusto platform', 'gusto hr'
        ]
        
        # Add domain-specific stop words (but keep 'gusto' for context)
        self.stop_words.update([
            'payroll', 'software', 'company', 'business', 'use', 'using',
            'get', 'go', 'would', 'could', 'should', 'also', 'really', 'think',
            'know', 'see', 'want', 'need', 'way', 'time', 'work', 'good', 'well'
        ])
        
        # Define business themes with keywords
        self.predefined_themes = {
            'pricing_cost': {
                'keywords': [
                    'price', 'cost', 'expensive', 'cheap', 'affordable', 'fee', 'pricing',
                    'money', 'budget', 'value', 'worth', 'subscription', 'plan', 'tier'
                ],
                'description': 'Discussions about pricing, costs, and value proposition'
            },
            'customer_service': {
                'keywords': [
                    'support', 'help', 'service', 'representative', 'response', 'staff',
                    'team', 'assistance', 'helpdesk', 'chat', 'phone', 'email', 'ticket'
                ],
                'description': 'Customer service and support experiences'
            },
            'user_experience': {
                'keywords': [
                    'interface', 'ui', 'ux', 'design', 'layout', 'navigation', 'user-friendly',
                    'intuitive', 'easy', 'difficult', 'confusing', 'simple', 'complex'
                ],
                'description': 'User interface and overall user experience'
            },
            'features_functionality': {
                'keywords': [
                    'feature', 'functionality', 'capability', 'option', 'tool', 'function',
                    'module', 'component', 'integration', 'automation', 'workflow'
                ],
                'description': 'Product features and functionality discussions'
            },
            'performance_reliability': {
                'keywords': [
                    'speed', 'fast', 'slow', 'performance', 'lag', 'responsive', 'reliable',
                    'stable', 'crash', 'downtime', 'uptime', 'bug', 'error', 'glitch'
                ],
                'description': 'Performance, reliability, and technical issues'
            },
            'payroll_processing': {
                'keywords': [
                    'payroll', 'pay', 'salary', 'wage', 'payment', 'direct deposit',
                    'tax', 'deduction', 'withholding', 'pay stub', 'paycheck', 'processing'
                ],
                'description': 'Core payroll processing functionality'
            },
            'hr_benefits': {
                'keywords': [
                    'hr', 'benefits', 'onboarding', 'employee', 'time tracking', 'pto',
                    'vacation', 'sick leave', 'health insurance', 'retirement', '401k'
                ],
                'description': 'HR features and employee benefits management'
            },
            'integration_compatibility': {
                'keywords': [
                    'integration', 'integrate', 'connect', 'sync', 'api', 'compatibility',
                    'quickbooks', 'accounting', 'export', 'import', 'third-party'
                ],
                'description': 'Integration with other systems and compatibility'
            },
            'compliance_taxes': {
                'keywords': [
                    'compliance', 'tax', 'irs', 'regulation', 'law', 'legal', 'audit',
                    'w2', 'w4', '1099', 'state tax', 'federal tax', 'filing'
                ],
                'description': 'Tax compliance and regulatory requirements'
            },
            'comparison_alternatives': {
                'keywords': [
                    'vs', 'versus', 'compare', 'comparison', 'alternative', 'competitor',
                    'adp', 'paychex', 'quickbooks', 'bamboohr', 'workday', 'instead'
                ],
                'description': 'Comparisons with competitors and alternatives'
            }
        }
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text for theme extraction.
        
        Args:
            text: Raw text to preprocess
            
        Returns:
            Preprocessed text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs, email addresses, and special characters
        text = re.sub(r'http[s]?://\S+', '', text)
        text = re.sub(r'\S+@\S+', '', text)
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_keywords(self, text: str, top_n: int = 20) -> List[Tuple[str, float]]:
        """
        Extract important keywords using TF-IDF.
        
        Args:
            text: Text to extract keywords from
            top_n: Number of top keywords to return
            
        Returns:
            List of (keyword, score) tuples
        """
        processed_text = self.preprocess_text(text)
        
        # Tokenize and lemmatize
        tokens = word_tokenize(processed_text)
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens 
                 if token not in self.stop_words and len(token) > 2]
        
        if not tokens:
            return []
        
        # Create TF-IDF vectorizer
        vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            stop_words='english'
        )
        
        try:
            # Fit and transform the text
            tfidf_matrix = vectorizer.fit_transform([' '.join(tokens)])
            feature_names = vectorizer.get_feature_names_out()
            
            # Get scores
            scores = tfidf_matrix.toarray()[0]
            
            # Create keyword-score pairs
            keyword_scores = list(zip(feature_names, scores))
            keyword_scores.sort(key=lambda x: x[1], reverse=True)
            
            return keyword_scores[:top_n]
            
        except Exception as e:
            logger.warning(f"Error extracting keywords: {e}")
            return []
    
    def extract_gusto_segments(self, text: str) -> List[str]:
        """
        Extract sentences and segments that specifically mention Gusto with enhanced context filtering.
        Focus only on what's being said about Gusto, not the entire post content.
        
        Args:
            text: Full text to analyze
            
        Returns:
            List of text segments that mention Gusto (excluding competitor-focused content)
        """
        if not text:
            return []
        
        try:
            # Split into sentences
            sentences = sent_tokenize(text.lower())
        except:
            # Fallback to simple splitting if NLTK fails
            sentences = [s.strip() + '.' for s in text.lower().split('.') if s.strip()]
        
        gusto_segments = []
        
        # Competitor names that might create noise in theme analysis
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
                    # Extract focused context window around Gusto mention (±12 words)
                    start = max(0, i - 12)
                    end = min(len(words), i + 13)
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
        import re
        
        # Common patterns for Gusto-specific clauses in theme context
        gusto_patterns = [
            # Theme-relevant patterns for pricing, features, etc. (stop at competitor mentions)
            r'(gusto.*?(?:costs?|pric\w+|fees?|expensive|cheap|affordable))(?=\s+(?:but|then|however|switch|adp|paychex|quickbooks|bamboohr|rippling|workday|deel|justworks)|$)',
            r'(gusto.*?(?:features?|functionality|capabilit\w+|tools?))(?=\s+(?:but|then|however|switch|adp|paychex|quickbooks|bamboohr|rippling|workday|deel|justworks)|$)',
            r'(gusto.*?(?:interface|ui|ux|user|experience|easy|difficult))(?=\s+(?:but|then|however|switch|adp|paychex|quickbooks|bamboohr|rippling|workday|deel|justworks)|$)',
            r'(gusto.*?(?:support|service|help|customer|staff))(?=\s+(?:but|then|however|switch|adp|paychex|quickbooks|bamboohr|rippling|workday|deel|justworks)|$)',
            r'(gusto.*?(?:integration|connect|sync|api|compatibility))(?=\s+(?:but|then|however|switch|adp|paychex|quickbooks|bamboohr|rippling|workday|deel|justworks)|$)',
            r'(gusto.*?(?:payroll|pay|processing|tax|benefits|hr))(?=\s+(?:but|then|however|switch|adp|paychex|quickbooks|bamboohr|rippling|workday|deel|justworks)|$)',
            r'(gusto.*?(?:performance|speed|fast|slow|reliable|stable))(?=\s+(?:but|then|however|switch|adp|paychex|quickbooks|bamboohr|rippling|workday|deel|justworks)|$)',
            
            # Specific patterns that stop before transitions
            r'((?:started with|using|used|chose).*?gusto.*?(?:which was|that was|and it was|but it was).*?)(?=\s+(?:but|then|however|switch|\.|,))',
            r'(gusto.*?(?:is|was|has|had).*?(?:fine|good|great|bad|terrible|awful|mess))(?=\s+(?:but|then|however|switch|\.|,))',
            
            # Simple Gusto mentions with immediate context
            r'(gusto\s+(?:which|that|is|was|has|had)\s+\w+(?:\s+\w+){0,4})(?=\s+(?:but|then|however|switch|for|although|\.|,))',
        ]
        
        for pattern in gusto_patterns:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                clause = match.group(1).strip()
                # Clean up the clause
                clause = re.sub(r'^[,\s]+|[,\s]+$', '', clause)
                if len(clause) > 5:  # Ensure we have meaningful content
                    return clause
        
        # Fallback: extract focused context around Gusto mention
        words = sentence.split()
        gusto_index = -1
        for i, word in enumerate(words):
            if 'gusto' in word.lower():
                gusto_index = i
                break
        
        if gusto_index != -1:
            # Extract a smaller context around Gusto to focus on relevant themes
            start = max(0, gusto_index - 6)
            end = min(len(words), gusto_index + 7)
            clause = ' '.join(words[start:end])
            return clause
        
        return ""
    
    def classify_predefined_themes(self, text: str) -> Dict[str, float]:
        """
        Classify text into predefined business themes focusing on Gusto mentions.
        
        Args:
            text: Text to classify
            
        Returns:
            Dictionary of theme scores
        """
        # Extract Gusto-specific segments
        gusto_segments = self.extract_gusto_segments(text)
        
        if not gusto_segments:
            # If no Gusto mentions found, return all zero scores
            return {theme_name: 0.0 for theme_name in self.predefined_themes.keys()}
        
        # Combine Gusto segments and preprocess
        combined_gusto_text = ' '.join(gusto_segments)
        processed_text = self.preprocess_text(combined_gusto_text)
        theme_scores = {}
        
        for theme_name, theme_data in self.predefined_themes.items():
            keywords = theme_data['keywords']
            
            # Count keyword matches in Gusto context
            matches = sum(1 for keyword in keywords if keyword in processed_text)
            
            # Calculate relevance score (normalize by text length and keyword count)
            text_length = len(processed_text.split())
            if text_length > 0:
                score = (matches / len(keywords)) * (matches / text_length) * 100
            else:
                score = 0.0
            
            theme_scores[theme_name] = score
        
        return theme_scores
    
    def extract_topics_lda(self, texts: List[str], n_topics: int = 10) -> Dict[str, Any]:
        """
        Extract topics using Latent Dirichlet Allocation (LDA).
        
        Args:
            texts: List of texts to analyze
            n_topics: Number of topics to extract
            
        Returns:
            Dictionary with topic information
        """
        if not texts:
            return {}
        
        # Preprocess texts
        processed_texts = [self.preprocess_text(text) for text in texts]
        processed_texts = [text for text in processed_texts if text.strip()]
        
        if len(processed_texts) < 2:
            return {}
        
        try:
            # Create TF-IDF vectorizer
            vectorizer = TfidfVectorizer(
                max_features=1000,
                max_df=0.8,
                min_df=2,
                ngram_range=(1, 2),
                stop_words='english'
            )
            
            # Fit and transform texts
            doc_term_matrix = vectorizer.fit_transform(processed_texts)
            
            # Create LDA model
            lda = LatentDirichletAllocation(
                n_components=n_topics,
                random_state=42,
                max_iter=10
            )
            
            # Fit the model
            lda.fit(doc_term_matrix)
            
            # Extract topics
            feature_names = vectorizer.get_feature_names_out()
            topics = []
            
            for topic_idx, topic in enumerate(lda.components_):
                # Get top words for this topic
                top_words_idx = topic.argsort()[-10:][::-1]
                top_words = [feature_names[i] for i in top_words_idx]
                top_scores = [topic[i] for i in top_words_idx]
                
                topics.append({
                    'topic_id': topic_idx,
                    'words': top_words,
                    'scores': top_scores,
                    'weight': np.sum(topic)
                })
            
            return {
                'topics': topics,
                'n_topics': n_topics,
                'perplexity': lda.perplexity(doc_term_matrix)
            }
            
        except Exception as e:
            logger.error(f"Error in LDA topic extraction: {e}")
            return {}
    
    def cluster_texts(self, texts: List[str], n_clusters: int = 5) -> Dict[str, Any]:
        """
        Cluster texts using K-means clustering.
        
        Args:
            texts: List of texts to cluster
            n_clusters: Number of clusters
            
        Returns:
            Dictionary with clustering results
        """
        if not texts or len(texts) < n_clusters:
            return {}
        
        # Preprocess texts
        processed_texts = [self.preprocess_text(text) for text in texts]
        processed_texts = [text for text in processed_texts if text.strip()]
        
        if len(processed_texts) < n_clusters:
            return {}
        
        try:
            # Create TF-IDF vectorizer
            vectorizer = TfidfVectorizer(
                max_features=500,
                max_df=0.8,
                min_df=2,
                stop_words='english'
            )
            
            # Fit and transform texts
            tfidf_matrix = vectorizer.fit_transform(processed_texts)
            
            # Perform K-means clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(tfidf_matrix)
            
            # Extract cluster information
            feature_names = vectorizer.get_feature_names_out()
            clusters = []
            
            for cluster_id in range(n_clusters):
                # Get cluster center
                cluster_center = kmeans.cluster_centers_[cluster_id]
                
                # Get top words for this cluster
                top_words_idx = cluster_center.argsort()[-10:][::-1]
                top_words = [feature_names[i] for i in top_words_idx]
                top_scores = [cluster_center[i] for i in top_words_idx]
                
                # Get texts in this cluster
                cluster_texts = [texts[i] for i, label in enumerate(cluster_labels) if label == cluster_id]
                
                clusters.append({
                    'cluster_id': cluster_id,
                    'top_words': top_words,
                    'word_scores': top_scores,
                    'texts_count': len(cluster_texts),
                    'sample_texts': cluster_texts[:3]  # First 3 texts as examples
                })
            
            return {
                'clusters': clusters,
                'cluster_labels': cluster_labels.tolist(),
                'n_clusters': n_clusters
            }
            
        except Exception as e:
            logger.error(f"Error in text clustering: {e}")
            return {}
    
    def analyze_themes(self, texts: List[str]) -> Dict[str, Any]:
        """
        Comprehensive theme analysis combining multiple techniques.
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            Dictionary with comprehensive theme analysis
        """
        if not texts:
            return {}
        
        logger.info(f"Analyzing themes for {len(texts)} texts")
        
        # Combine all texts for overall analysis
        combined_text = ' '.join(texts)
        
        # Extract keywords
        keywords = self.extract_keywords(combined_text)
        
        # Classify predefined themes
        predefined_themes = {}
        for text in texts:
            text_themes = self.classify_predefined_themes(text)
            for theme, score in text_themes.items():
                if theme not in predefined_themes:
                    predefined_themes[theme] = []
                predefined_themes[theme].append(score)
        
        # Average theme scores
        avg_theme_scores = {
            theme: np.mean(scores) for theme, scores in predefined_themes.items()
        }
        
        # Sort themes by relevance
        sorted_themes = sorted(avg_theme_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Extract topics using LDA
        lda_topics = self.extract_topics_lda(texts, n_topics=min(8, len(texts) // 3))
        
        # Cluster texts
        clusters = self.cluster_texts(texts, n_clusters=min(5, len(texts) // 4))
        
        return {
            'top_keywords': keywords[:15],
            'predefined_themes': {
                'scores': avg_theme_scores,
                'ranked': sorted_themes[:10],
                'descriptions': {name: data['description'] for name, data in self.predefined_themes.items()}
            },
            'discovered_topics': lda_topics,
            'text_clusters': clusters,
            'total_texts_analyzed': len(texts)
        }
    
    def get_theme_summary(self, theme_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary of the most important themes.
        
        Args:
            theme_analysis: Results from analyze_themes()
            
        Returns:
            Simplified theme summary
        """
        if not theme_analysis:
            return {}
        
        summary = {
            'top_themes': [],
            'key_topics': [],
            'main_concerns': [],
            'positive_aspects': []
        }
        
        # Get top predefined themes
        if 'predefined_themes' in theme_analysis and 'ranked' in theme_analysis['predefined_themes']:
            ranked_themes = theme_analysis['predefined_themes']['ranked']
            descriptions = theme_analysis['predefined_themes']['descriptions']
            
            for theme_name, score in ranked_themes[:5]:
                if score > 0:
                    summary['top_themes'].append({
                        'name': theme_name.replace('_', ' ').title(),
                        'score': round(score, 2),
                        'description': descriptions.get(theme_name, '')
                    })
        
        # Extract key topics from LDA
        if 'discovered_topics' in theme_analysis and 'topics' in theme_analysis['discovered_topics']:
            topics = theme_analysis['discovered_topics']['topics']
            for topic in topics[:3]:  # Top 3 topics
                summary['key_topics'].append({
                    'words': topic['words'][:5],
                    'weight': round(topic['weight'], 2)
                })
        
        # Identify concerns and positive aspects based on common patterns
        if 'top_keywords' in theme_analysis:
            keywords = theme_analysis['top_keywords']
            
            concern_words = ['problem', 'issue', 'bug', 'error', 'slow', 'expensive', 'difficult']
            positive_words = ['great', 'love', 'easy', 'good', 'excellent', 'recommend', 'helpful']
            
            for keyword, score in keywords:
                if any(concern in keyword for concern in concern_words):
                    summary['main_concerns'].append(keyword)
                elif any(positive in keyword for positive in positive_words):
                    summary['positive_aspects'].append(keyword)
        
        return summary 