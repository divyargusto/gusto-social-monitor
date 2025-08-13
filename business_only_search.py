#!/usr/bin/env python3
"""
Business-ONLY Reddit search for Gusto payroll company
Searches ONLY legitimate business subreddits - no referral spam or irrelevant communities
"""

import asyncio
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
import praw
import re

from backend.database.database import init_database

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def is_business_relevant_post(title: str, text: str, subreddit: str, author: str) -> bool:
    """
    Ultra-strict filter for genuine business discussions about Gusto payroll.
    Excludes referral spam, promotional posts, and irrelevant content.
    """
    
    combined_text = f"{title} {text}".lower()
    
    # EXCLUDE: Spam and promotional content
    spam_patterns = [
        r'\b(referral|ref|code|discount|promo|coupon|deal|offer)\b',
        r'\b(affiliate|commission|earn money|make money)\b',
        r'\b(dm me|message me|contact me|link in bio)\b',
        r'\b(click here|sign up|register now|limited time)\b',
        r'(http|https|www\.)',  # URLs often indicate spam
        r'\b(free trial|get started|special offer)\b',
    ]
    
    # If it matches spam patterns, reject it
    for pattern in spam_patterns:
        if re.search(pattern, combined_text):
            return False
    
    # EXCLUDE: Non-English content (even more strict)
    foreign_patterns = [
        r'\b(sarap|masarap|nakaka|mga|ang|sa|ko|mo|niya)\b',  # Filipino
        r'\b(con|muy|que|para|como|este|una|las|los)\b',      # Spanish
        r'\b(и|в|на|с|для|от|по|за|до|из)\b',                # Russian
        r'\b(le|la|les|des|du|dans|pour|avec|sur)\b',         # French
    ]
    
    for pattern in foreign_patterns:
        if re.search(pattern, combined_text):
            return False
    
    # REQUIRE: Strong business context
    business_indicators = [
        # Direct product discussions
        r'\bgusto\s+(payroll|hr|software|platform|system|app)\b',
        r'\b(payroll|hr|benefits|taxes|w2|1099|compliance)\s+.*\bgusto\b',
        
        # Business decision language
        r'\b(using|used|tried|switched|considering|evaluating|implementing)\s+gusto\b',
        r'\bgusto\s+(review|pricing|cost|features|demo|trial)\b',
        
        # Competitor comparisons (high business value)
        r'\bgusto\s+vs\s+(adp|paychex|bamboohr|quickbooks|rippling|workday)\b',
        r'\b(adp|paychex|bamboohr|quickbooks)\s+vs\s+gusto\b',
        
        # Integration discussions
        r'\b(quickbooks|xero|accounting|bookkeeping).*gusto\b',
        r'\bgusto.*\b(integration|sync|api|connect)\b',
        
        # Business process context
        r'\bgusto.*\b(onboarding|employee|contractor|freelancer)\b',
        r'\b(small business|startup|llc|s-corp|corporation).*gusto\b',
        
        # Problem-solving discussions
        r'\bgusto.*\b(issue|problem|support|help|question)\b',
        r'\b(payroll processing|tax filing|benefits administration).*gusto\b',
    ]
    
    # Must match at least one strong business indicator
    business_match = False
    for pattern in business_indicators:
        if re.search(pattern, combined_text):
            business_match = True
            break
    
    if not business_match:
        return False
    
    # REQUIRE: Legitimate business discussion (not just product name)
    if len(combined_text.strip()) < 50:  # Too short to be meaningful discussion
        return False
    
    # SUCCESS: Passed all filters
    return True

async def search_business_subreddits():
    """Search ONLY legitimate business subreddits for Gusto discussions."""
    
    print("🏢 Starting BUSINESS-ONLY Gusto Search...")
    print("✅ Searching ONLY legitimate business subreddits")
    print("🚫 Excluding referral spam, promotional posts, and irrelevant content")
    
    # Initialize Reddit API
    try:
        reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent='GustoBusinessMonitor/1.0'
        )
        print("✅ Reddit API connected")
    except Exception as e:
        print(f"❌ Reddit API error: {e}")
        return []
    
    # ONLY legitimate business subreddits
    business_subreddits = [
        # Core business communities
        'smallbusiness',
        'entrepreneur', 
        'startups',
        'business',
        'solopreneur',
        
        # Finance & Accounting
        'accounting',
        'Accounting',
        'bookkeeping',
        'Bookkeeping',
        'QuickBooks',
        'tax',
        'taxpros',
        
        # HR & Payroll
        'payroll',
        'Payroll',
        'humanresources',
        'HumanResources',
        'AskHR',
        'peopleops',
        
        # Work & Employment
        'remotework',
        'freelance',
        'freelancing',
        'WorkOnline',
        'digitalnomad',
        
        # Legal & Business Structure
        'llc',
        'legaladvice',  # For business legal questions
        'Tax',
        
        # Industry specific
        'nonprofit',
        'nonprofits',
        'consulting',
        'restaurantowners',
        'retail',
        'ecommerce',
        
        # Software & Tools
        'SaaS',
        'saas',
        'BusinessIntelligence',
        'productivity',
        'automation',
    ]
    
    # Business-focused search terms
    search_terms = [
        'Gusto payroll',
        'Gusto HR',
        'Gusto software',
        'payroll software Gusto',
        'HR software Gusto',
        'Gusto vs ADP',
        'Gusto vs Paychex',
        'QuickBooks Gusto',
        'using Gusto',
        'switched to Gusto',
    ]
    
    print(f"🎯 Searching {len(business_subreddits)} business subreddits")
    print(f"🔍 Using {len(search_terms)} business-focused terms")
    
    all_results = []
    
    for subreddit_name in business_subreddits:
        try:
            print(f"   📋 Searching r/{subreddit_name}...")
            
            subreddit = reddit.subreddit(subreddit_name)
            
            # Search each term in this subreddit
            subreddit_count = 0
            for term in search_terms:
                try:
                    search_results = subreddit.search(
                        query=term,
                        sort='relevance',
                        time_filter='year',
                        limit=10  # Conservative limit per term per subreddit
                    )
                    
                    for submission in search_results:
                        try:
                            # STRICT business relevance filtering
                            if is_business_relevant_post(
                                submission.title,
                                submission.selftext,
                                submission.subreddit.display_name,
                                str(submission.author) if submission.author else ''
                            ):
                                result = {
                                    'platform': 'reddit',
                                    'subreddit': submission.subreddit.display_name,
                                    'post_id': submission.id,
                                    'title': submission.title,
                                    'text': submission.selftext if submission.selftext else submission.title,
                                    'author': str(submission.author) if submission.author else 'deleted',
                                    'url': f"https://reddit.com{submission.permalink}",
                                    'created_at': datetime.fromtimestamp(submission.created_utc).isoformat(),
                                    'upvotes': submission.score,
                                    'comments_count': submission.num_comments,
                                    'search_term': term,
                                    'source_subreddit': subreddit_name,
                                    'relevance_score': 'business_verified'
                                }
                                
                                all_results.append(result)
                                subreddit_count += 1
                                
                        except Exception as e:
                            logger.warning(f"Error processing submission: {e}")
                            continue
                            
                except Exception as e:
                    logger.warning(f"Error searching '{term}' in r/{subreddit_name}: {e}")
                    continue
            
            if subreddit_count > 0:
                print(f"      ✅ Found: {subreddit_count} business discussions")
            else:
                print(f"      📭 No relevant discussions found")
                
            # Rate limiting
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"❌ Error accessing r/{subreddit_name}: {e}")
            continue
    
    # Remove duplicates
    unique_results = {}
    for result in all_results:
        key = result['post_id']
        if key not in unique_results:
            unique_results[key] = result
    
    final_results = list(unique_results.values())
    
    print(f"\n🏢 BUSINESS-ONLY SEARCH RESULTS:")
    print(f"   📊 Total business discussions: {len(final_results)}")
    print(f"   ✅ All verified as legitimate business content")
    print(f"   🚫 Filtered out: Referral spam, promotional posts, irrelevant content")
    
    if final_results:
        # Show business subreddit breakdown
        subreddit_counts = {}
        for result in final_results:
            subreddit = result.get('subreddit', 'unknown')
            subreddit_counts[subreddit] = subreddit_counts.get(subreddit, 0) + 1
        
        print(f"\n🏢 LEGITIMATE BUSINESS SUBREDDITS:")
        sorted_subreddits = sorted(subreddit_counts.items(), key=lambda x: x[1], reverse=True)
        for subreddit, count in sorted_subreddits:
            print(f"   r/{subreddit}: {count} business discussions")
        
        # Show effective search terms
        term_counts = {}
        for result in final_results:
            term = result.get('search_term', 'unknown')
            term_counts[term] = term_counts.get(term, 0) + 1
        
        print(f"\n🔍 MOST EFFECTIVE BUSINESS SEARCH TERMS:")
        sorted_terms = sorted(term_counts.items(), key=lambda x: x[1], reverse=True)
        for term, count in sorted_terms[:5]:
            print(f"   '{term}': {count} discussions")
    
    return final_results

async def main():
    """Main function to run business-only search."""
    
    # Initialize database
    try:
        init_database()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database error: {e}")
        return
    
    # Run business-only search
    results = await search_business_subreddits()
    
    if results:
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reddit_business_only_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Business-only results saved to: {filename}")
        
        # Auto-update process_data.py
        try:
            with open('process_data.py', 'r') as f:
                content = f.read()
            
            import re
            new_content = re.sub(
                r'json_file = "reddit_.*\.json"',
                f'json_file = "{filename}"',
                content
            )
            
            with open('process_data.py', 'w') as f:
                f.write(new_content)
            
            print(f"✅ Updated process_data.py to use {filename}")
            
        except Exception as e:
            print(f"⚠️  Update process_data.py manually: {e}")
        
        print(f"\n🏢 BUSINESS QUALITY CONTROL:")
        print(f"   📈 Collected: {len(results)} verified business discussions")
        print(f"   🎯 Sources: Only legitimate business subreddits")
        print(f"   🚫 Excluded: r/Referral, r/KCRoyals, promotional spam")
        print(f"   ✅ Focus: Genuine Gusto payroll business conversations")
        
        print(f"\n🔄 NEXT STEPS:")
        print(f"   1. Run: python process_data.py")
        print(f"   2. Start dashboard: python backend/app/app.py")
        print(f"   3. View CLEAN business data at: http://localhost:5000")
        
    else:
        print("📭 No business discussions found in legitimate subreddits.")
        print("   This suggests very limited recent Gusto business discussion")
        print("   or seasonal patterns in business software discussions.")
    
    print("\n✅ Business-only search completed!")

if __name__ == "__main__":
    import os
    asyncio.run(main()) 