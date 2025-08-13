"""
G2 Web Scraper for Gusto Social Monitor

⚠️  IMPORTANT LEGAL NOTICE:
This scraper is for educational and research purposes only.
- Check G2's Terms of Service before use
- Use appropriate rate limiting (implemented below)
- Consider G2's official API for commercial use
- Respect website resources and server load

Usage:
    from utils.g2_scraper import G2Scraper
    scraper = G2Scraper()
    reviews = scraper.scrape_gusto_reviews()
"""

import requests
import time
import random
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class G2Scraper:
    def __init__(self, delay_range=(2, 5)):
        """
        Initialize G2 Scraper with responsible defaults
        
        Args:
            delay_range: Tuple of (min, max) seconds to wait between requests
        """
        self.base_url = "https://www.g2.com"
        self.delay_range = delay_range
        self.session = requests.Session()
        
        # Set realistic headers to appear more like a regular browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Cache-Control': 'max-age=0',
        })
        
        logger.info("🤖 G2Scraper initialized - Please use responsibly!")
        logger.warning("⚠️  Remember to check G2's Terms of Service before scraping")

    def test_access(self, url: str) -> bool:
        """Test if we can access a G2 URL."""
        try:
            response = self.session.head(url, timeout=5)
            if response.status_code == 403:
                logger.warning(f"⚠️  Access blocked (403) for: {url}")
                return False
            elif response.status_code == 200:
                logger.info(f"✅ Access confirmed for: {url}")
                return True
            else:
                logger.info(f"⚠️  Unexpected status {response.status_code} for: {url}")
                return False
        except Exception as e:
            logger.warning(f"⚠️  Could not test access to {url}: {e}")
            return False

    def _rate_limit(self):
        """Implement respectful rate limiting"""
        delay = random.uniform(*self.delay_range)
        logger.info(f"⏱️  Rate limiting: waiting {delay:.1f} seconds...")
        time.sleep(delay)

    def _make_request(self, url: str) -> Optional[BeautifulSoup]:
        """Make a rate-limited request and return parsed HTML"""
        try:
            self._rate_limit()
            
            logger.info(f"🌐 Fetching: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            return BeautifulSoup(response.content, 'html.parser')
            
        except requests.RequestException as e:
            logger.error(f"❌ Request failed for {url}: {e}")
            return None

    def search_products(self, query: str) -> List[Dict]:
        """
        Search for products on G2
        
        Args:
            query: Search term (e.g., "gusto", "payroll software")
            
        Returns:
            List of product dictionaries with URLs and basic info
        """
        search_url = f"{self.base_url}/search"
        params = {'query': query}
        
        try:
            response = self.session.get(search_url, params=params, timeout=10)
            if response.status_code == 403:
                logger.warning("⚠️  G2 search blocked (403 Forbidden) - this is common with automated requests")
                return []  # Return empty list to trigger fallback methods
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            products = []
            
            # Find product cards in search results - G2 uses various class names
            selectors = [
                'div[data-testid*="product"]',
                'div[data-testid*="search-result"]',
                '.product-listing',
                '.search-result-item',
                'article[data-testid]',
                'div.border.rounded',
                'div[class*="product"]',
                'div[class*="search"]',
                'a[href*="/products/"]',  # Direct product links
                '.border.border-solid',
                'div.mb-4',  # Common G2 spacing class
                'div.p-4'    # Common G2 padding class
            ]
            
            product_cards = []
            for selector in selectors:
                cards = soup.select(selector)
                if cards:
                    product_cards = cards
                    logger.info(f"✅ Found {len(cards)} product cards using selector: {selector}")
                    break
            
            # Fallback: Look for any elements containing product links
            if not product_cards:
                logger.info("🔍 No product cards found with standard selectors, trying fallback...")
                all_links = soup.find_all('a', href=re.compile(r'/products/'))
                # Group links by their parent containers
                containers = []
                for link in all_links:
                    parent = link.find_parent(['div', 'article', 'section'])
                    if parent and parent not in containers:
                        containers.append(parent)
                product_cards = containers[:10]  # Limit to avoid too many results
                logger.info(f"🔄 Fallback found {len(product_cards)} containers with product links")
            
            for card in product_cards[:10]:  # Limit to first 10 results
                try:
                    # Extract product name and URL - try multiple approaches
                    link = None
                    name = ""
                    url = ""
                    
                    # Approach 1: Direct product link
                    link = card.find('a', href=re.compile(r'/products/'))
                    if not link:
                        link = card.select_one('a[href*="/products/"]')
                    
                    # Approach 2: If card itself is a link
                    if not link and card.name == 'a' and '/products/' in card.get('href', ''):
                        link = card
                    
                    # Approach 3: Look for any link in the card
                    if not link:
                        link = card.find('a', href=True)
                        if link and '/products/' not in link.get('href', ''):
                            link = None
                    
                    if link:
                        # Extract name - try multiple selectors
                        name_selectors = [
                            'h3', 'h4', 'h5', 'h6',
                            '.product-name',
                            '[data-testid*="name"]',
                            '[data-testid*="title"]',
                            '.font-bold',
                            '.fw-bold',
                            '.text-lg',
                            '.text-xl'
                        ]
                        
                        for selector in name_selectors:
                            name_elem = card.select_one(selector)
                            if name_elem:
                                name = name_elem.get_text(strip=True)
                                if name and len(name) > 1:
                                    break
                        
                        # Fallback: use link text
                        if not name:
                            name = link.get_text(strip=True)
                        
                        # Clean up the name
                        name = re.sub(r'\s+', ' ', name).strip()
                        
                        url = urljoin(self.base_url, link['href'])
                        
                        # Extract rating if available
                        rating = None
                        rating_selectors = [
                            '[data-testid*="rating"]',
                            '.fw-semibold',
                            '.stars',
                            '[title*="stars"]'
                        ]
                        
                        for selector in rating_selectors:
                            rating_elem = card.select_one(selector)
                            if rating_elem:
                                rating_text = rating_elem.get_text(strip=True)
                                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                                if rating_match:
                                    rating = float(rating_match.group(1))
                                    break
                        
                        if name and url:  # Only add if we have both name and URL
                            products.append({
                                'name': name,
                                'url': url,
                                'rating': rating,
                                'source': 'g2'
                            })
                            logger.info(f"📦 Added product: {name}")
                        else:
                            logger.warning(f"⚠️  Skipped incomplete product: name='{name}', url='{url}'")
                        
                except Exception as e:
                    logger.warning(f"⚠️  Error parsing product card: {e}")
                    continue
            
            logger.info(f"✅ Found {len(products)} products for query: {query}")
            return products
            
        except Exception as e:
            logger.error(f"❌ Search failed for query '{query}': {e}")
            return []

    def scrape_product_reviews(self, product_url: str, max_pages: int = 3) -> List[Dict]:
        """
        Scrape reviews for a specific product
        
        Args:
            product_url: Full URL to G2 product page
            max_pages: Maximum number of review pages to scrape
            
        Returns:
            List of review dictionaries
        """
        reviews = []
        
        # Ensure we're on the reviews page
        if not product_url.endswith('/reviews'):
            product_url = product_url.rstrip('/') + '/reviews'
        
        for page in range(1, max_pages + 1):
            page_url = product_url
            if page > 1:
                page_url += f"?page={page}"
            
            soup = self._make_request(page_url)
            if not soup:
                break
            
            # Find review containers - G2 uses various structures
            review_selectors = [
                '[data-testid*="review"]',
                '.paper.paper--white',
                'article[data-testid]',
                '.review-container',
                'div[data-qa="review"]'
            ]
            
            review_containers = []
            for selector in review_selectors:
                containers = soup.select(selector)
                if containers:
                    review_containers = containers
                    break
            
            if not review_containers:
                logger.info(f"📄 No more reviews found on page {page}")
                break
            
            page_reviews = 0
            for container in review_containers:
                try:
                    review = self._parse_review(container)
                    if review:
                        review['product_url'] = product_url
                        review['page'] = page
                        reviews.append(review)
                        page_reviews += 1
                        
                except Exception as e:
                    logger.warning(f"⚠️  Error parsing review: {e}")
                    continue
            
            logger.info(f"📋 Scraped {page_reviews} reviews from page {page}")
            
            # If no reviews found on this page, stop
            if page_reviews == 0:
                break
        
        logger.info(f"✅ Total reviews scraped: {len(reviews)}")
        return reviews

    def _parse_review(self, container) -> Optional[Dict]:
        """Parse individual review from HTML container"""
        try:
            # Extract review content - try multiple selectors
            content = ""
            content_selectors = [
                '[data-testid*="review-body"]',
                '.formatted-text',
                'div[data-qa="pros-review"]',
                'p',
                '.review-text'
            ]
            
            for selector in content_selectors:
                content_elem = container.select_one(selector)
                if content_elem:
                    content = content_elem.get_text(strip=True)
                    if len(content) > 20:  # Meaningful content
                        break
            
            # Skip if no meaningful content
            if len(content) < 20:
                return None
            
            # Extract rating
            rating = None
            rating_selectors = [
                '[data-testid*="rating"]',
                '.fw-semibold',
                '[title*="out of 5"]',
                '.stars'
            ]
            
            for selector in rating_selectors:
                rating_elem = container.select_one(selector)
                if rating_elem:
                    # Try to extract from title attribute first
                    title = rating_elem.get('title', '')
                    if 'out of 5' in title:
                        rating_match = re.search(r'(\d+\.?\d*)\s*out of 5', title)
                        if rating_match:
                            rating = float(rating_match.group(1))
                            break
                    
                    # Try to extract from text
                    rating_text = rating_elem.get_text(strip=True)
                    rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                    if rating_match:
                        rating = float(rating_match.group(1))
                        break
            
            # Extract reviewer info
            reviewer = "Anonymous"
            reviewer_selectors = [
                '[data-testid*="reviewer"]',
                '.reviewer-name',
                '.fw-semibold a',
                'a[href*="/reviewers/"]'
            ]
            
            for selector in reviewer_selectors:
                reviewer_elem = container.select_one(selector)
                if reviewer_elem:
                    reviewer = reviewer_elem.get_text(strip=True)
                    break
            
            # Extract date
            date_str = ""
            date_selectors = [
                '[data-testid*="date"]',
                '.color-fg-subtle',
                'time',
                '.review-date'
            ]
            
            for selector in date_selectors:
                date_elem = container.select_one(selector)
                if date_elem:
                    date_str = date_elem.get_text(strip=True)
                    break
            
            # Extract title
            title = ""
            title_selectors = [
                '[data-testid*="title"]',
                'h3',
                'h4',
                '.review-title',
                '.fw-bold'
            ]
            
            for selector in title_selectors:
                title_elem = container.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if len(title) > 5:  # Meaningful title
                        break
            
            # Extract pros and cons
            pros = ""
            cons = ""
            
            # Look for pros/cons sections
            pros_elem = container.find(text=re.compile(r'What do you like best|Pros:', re.I))
            cons_elem = container.find(text=re.compile(r'What do you dislike|Cons:', re.I))
            
            if pros_elem and pros_elem.parent:
                pros_container = pros_elem.parent.find_next('div') or pros_elem.parent
                pros = pros_container.get_text(strip=True)
            
            if cons_elem and cons_elem.parent:
                cons_container = cons_elem.parent.find_next('div') or cons_elem.parent
                cons = cons_container.get_text(strip=True)
            
            return {
                'title': title,
                'content': content,
                'rating': rating,
                'reviewer': reviewer,
                'date': date_str,
                'pros': pros,
                'cons': cons,
                'platform': 'g2',
                'scraped_at': datetime.now().isoformat(),
                'url': self.base_url  # Will be updated with specific product URL
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing review: {e}")
            return None

    def scrape_gusto_reviews(self, max_pages: int = 3) -> List[Dict]:
        """
        Convenience method to scrape Gusto reviews specifically
        
        Args:
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of Gusto review dictionaries
        """
        logger.info("🎯 Searching for Gusto product page...")
        
        # Search for Gusto
        products = self.search_products("gusto payroll")
        
        # Debug: Log found products
        logger.info(f"🔍 Found {len(products)} products:")
        for i, product in enumerate(products, 1):
            logger.info(f"   {i}. {product['name']} - {product['url']}")
        
        # Find the main Gusto product - try multiple strategies
        gusto_product = None
        
        # Strategy 1: Exact match for "Gusto"
        for product in products:
            name_lower = product['name'].lower().strip()
            if name_lower == 'gusto':
                gusto_product = product
                logger.info(f"✅ Found exact match: {product['name']}")
                break
        
        # Strategy 2: Contains "gusto" and payroll/hr related terms
        if not gusto_product:
            for product in products:
                name_lower = product['name'].lower()
                if 'gusto' in name_lower and ('payroll' in name_lower or 'hr' in name_lower or 'human resources' in name_lower):
                    gusto_product = product
                    logger.info(f"✅ Found payroll match: {product['name']}")
                    break
        
        # Strategy 3: Just contains "gusto" (most flexible)
        if not gusto_product:
            for product in products:
                name_lower = product['name'].lower()
                if 'gusto' in name_lower:
                    gusto_product = product
                    logger.info(f"✅ Found flexible match: {product['name']}")
                    break
        
        # Strategy 4: Try a different search term
        if not gusto_product:
            logger.info("🔄 Trying alternative search: 'gusto'")
            products = self.search_products("gusto")
            
            for product in products:
                name_lower = product['name'].lower().strip()
                if name_lower == 'gusto' or (name_lower.startswith('gusto') and len(name_lower) < 20):
                    gusto_product = product
                    logger.info(f"✅ Found alternative search match: {product['name']}")
                    break
        
        # Strategy 5: Use direct URL fallback
        if not gusto_product:
            logger.info("🎯 Trying direct URL approach...")
            direct_url = "https://www.g2.com/products/gusto"
            gusto_product = {
                'name': 'Gusto',
                'url': direct_url,
                'rating': None,
                'source': 'g2'
            }
            logger.info(f"✅ Using direct URL: {direct_url}")
        
        if not gusto_product:
            logger.error("❌ Could not find Gusto product page after trying all strategies")
            logger.error("💡 Available products were:")
            for product in products:
                logger.error(f"   - {product['name']}")
            return []
        
        logger.info(f"✅ Found Gusto product: {gusto_product['name']}")
        logger.info(f"🔗 URL: {gusto_product['url']}")
        
        # Test access before scraping
        if not self.test_access(gusto_product['url']):
            logger.error("❌ Cannot access Gusto product page - scraping may fail")
            # Try the reviews page directly
            reviews_url = gusto_product['url'].rstrip('/') + '/reviews'
            if not self.test_access(reviews_url):
                logger.error("❌ Cannot access Gusto reviews page either")
                return []
            else:
                logger.info("✅ Will try to scrape from reviews page directly")
        
        # Scrape reviews
        reviews = self.scrape_product_reviews(gusto_product['url'], max_pages)
        
        # Add product info to each review
        for review in reviews:
            review['product_name'] = gusto_product['name']
            review['product_rating'] = gusto_product.get('rating')
        
        return reviews

    def scrape_competitor_reviews(self, competitors: List[str], max_pages: int = 2) -> Dict[str, List[Dict]]:
        """
        Scrape reviews for multiple competitor products
        
        Args:
            competitors: List of competitor names to search for
            max_pages: Maximum pages per competitor
            
        Returns:
            Dictionary mapping competitor names to their reviews
        """
        competitor_reviews = {}
        
        for competitor in competitors:
            logger.info(f"🔍 Searching for {competitor} reviews...")
            
            products = self.search_products(f"{competitor} payroll")
            
            if products:
                # Take the first/best match
                product = products[0]
                logger.info(f"✅ Found {competitor} product: {product['name']}")
                
                reviews = self.scrape_product_reviews(product['url'], max_pages)
                
                # Add competitor info to reviews
                for review in reviews:
                    review['competitor'] = competitor
                    review['product_name'] = product['name']
                    review['product_rating'] = product.get('rating')
                
                competitor_reviews[competitor] = reviews
                
            else:
                logger.warning(f"⚠️  No products found for {competitor}")
                competitor_reviews[competitor] = []
        
        return competitor_reviews
