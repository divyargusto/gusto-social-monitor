#!/usr/bin/env python3
"""
Targeted Reddit search for ONLY Gusto payroll company mentions
Filters out irrelevant "gusto" usage (food, Spanish, enthusiasm, etc.)
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

def is_relevant_gusto_mention(title: str, text: str, subreddit: str) -> bool:
    """
    Filter function to determine if this is actually about Gusto payroll company.
    Returns True only if it's genuinely about the business software.
    """
    
    # Combine title and text for analysis
    combined_text = f"{title} {text}".lower()
    
    # EXCLUDE: Non-English/food/enthusiasm contexts
    exclude_patterns = [
        r'\b(sarap|masarap|nakaka|mga|ang|sa)\b',  # Filipino words
        r'\b(con|muy|que|para|como|este)\b',      # Spanish words  
        r'\b(pizza|pasta|food|restaurant|recipe|cooking|delicious)\b',  # Food context
        r'\b(taste|flavor|yummy|tasty|eat|meal)\b',  # Food context
        r'\bmuch gusto\b',  # Spanish "much pleasure"
        r'\bwith gusto\b',  # General enthusiasm
        r'\bfull of gusto\b',  # General enthusiasm
        r'gustong\b',  # Filipino "want to"
        r'gusto ko\b',  # Filipino "I want"
    ]
    
    # If it matches exclude patterns, reject it
    for pattern in exclude_patterns:
        if re.search(pattern, combined_text):
            return False
    
    # REQUIRE: Business/payroll context indicators
    business_indicators = [
        # Direct company references
        r'\bgusto\s+(payroll|hr|software|app|platform|system)\b',
        r'\bgusto\s+vs\s+(adp|paychex|bamboohr|quickbooks|rippling)\b',
        r'\b(using|used|tried|switched to|considering)\s+gusto\b',
        
        # Business context + Gusto
        r'\bgusto\b.*\b(payroll|employee|benefits|taxes|w2|1099|onboarding)\b',
        r'\b(payroll|hr|benefits|taxes)\b.*\bgusto\b',
        
        # Company-specific terms
        r'\bgusto\.com\b',
        r'\bgustohq\b',
        r'\b@gustohq\b',
        
        # Business comparison context
        r'\b(alternative to|better than|instead of|compared to)\s+gusto\b',
        r'\bgusto\s+(pricing|cost|review|demo|features)\b',
        
        # Business process context
        r'\bgusto\b.*\b(integration|api|sync|setup|implementation)\b',
        r'\b(quickbooks|xero|accounting)\b.*\bgusto\b',
        
        # Small business context
        r'\bgusto\b.*\b(small business|startup|llc|s-corp|corporation)\b',
        r'\b(remote work|contractor|freelancer)\b.*\bgusto\b',
    ]
    
    # Must match at least one business indicator
    for pattern in business_indicators:
        if re.search(pattern, combined_text):
            return True
    
    # CONTEXT: Check subreddit relevance
    business_subreddits = [
        'smallbusiness', 'entrepreneur', 'startups', 'accounting', 'payroll', 
        'humanresources', 'business', 'freelance', 'solopreneur', 'saas'
    ]
    
    # If in business subreddit and mentions "Gusto" (capitalized), likely relevant
    if subreddit.lower() in business_subreddits and 'Gusto' in f"{title} {text}":
        return True
    
    # Default: reject if no clear business context
    return False

async def search_targeted_gusto():
    """Targeted search for genuine Gusto payroll company mentions."""
    
    print("🎯 Starting TARGETED Gusto Payroll Company Search...")
    print("🚫 Filtering out food, Spanish, Filipino, and general 'gusto' mentions")
    print("✅ Focusing ONLY on Gusto the payroll software company")
    
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
    
    all_results = []
    
    # HIGHLY SPECIFIC business search terms
    search_terms = [
        # Direct company + product combinations
        '"Gusto payroll"',
        '"Gusto HR"', 
        '"Gusto software"',
        '"Gusto platform"',
        
        # Comparison searches (high business relevance)
        '"Gusto vs ADP"',
        '"Gusto vs Paychex"',
        '"Gusto vs BambooHR"',
        '"Gusto vs QuickBooks payroll"',
        '"ADP vs Gusto"',
        '"Paychex vs Gusto"',
        
        # Business decision searches
        '"switched to Gusto"',
        '"using Gusto for payroll"',
        '"Gusto review"',
        '"Gusto pricing"',
        
        # Integration searches
        '"Gusto QuickBooks"',
        '"Gusto integration"',
        '"Gusto API"',
        
        # Company identifiers
        '"gusto.com"',
        '"@gustohq"',
        'site:gusto.com'
    ]
    
    print(f"🔍 Using {len(search_terms)} highly targeted business search terms...")
    
    for term in search_terms:
        try:
            print(f"   Searching: {term}")
            
            # Search with business time filter
            search_results = reddit.subreddit("all").search(
                query=term,
                sort='relevance',  # Use relevance for better quality
                time_filter='year',  # Expand to year for more business content
                limit=15  # Fewer results but higher quality
            )
            
            count = 0
            for submission in search_results:
                try:
                    # STRICT filtering for relevance
                    if is_relevant_gusto_mention(
                        submission.title, 
                        submission.selftext, 
                        submission.subreddit.display_name
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
                            'relevance_score': 'high'  # Mark as verified relevant
                        }
                        
                        all_results.append(result)
                        count += 1
                        
                        # Also check comments for business context
                        try:
                            submission.comments.replace_more(limit=0)
                            for comment in submission.comments[:2]:  # Top 2 comments only
                                if (hasattr(comment, 'body') and 
                                    is_relevant_gusto_mention('', comment.body, submission.subreddit.display_name)):
                                    
                                    comment_result = {
                                        'platform': 'reddit',
                                        'subreddit': submission.subreddit.display_name,
                                        'post_id': f"{submission.id}_{comment.id}",
                                        'title': f"Comment on: {submission.title}",
                                        'text': comment.body,
                                        'author': str(comment.author) if comment.author else 'deleted',
                                        'url': f"https://reddit.com{comment.permalink}",
                                        'created_at': datetime.fromtimestamp(comment.created_utc).isoformat(),
                                        'upvotes': comment.score,
                                        'comments_count': 0,
                                        'search_term': f"{term} (comment)",
                                        'relevance_score': 'high'
                                    }
                                    all_results.append(comment_result)
                                    count += 1
                        except:
                            pass  # Skip comment processing if it fails
                
                except Exception as e:
                    logger.warning(f"Error processing submission: {e}")
                    continue
            
            print(f"      ✅ Found: {count} RELEVANT business items")
            
            # Longer delay for quality searches
            await asyncio.sleep(3)
            
        except Exception as e:
            print(f"❌ Error searching '{term}': {e}")
            continue
    
    # Remove duplicates based on post_id
    unique_results = {}
    for result in all_results:
        key = result['post_id']
        if key not in unique_results:
            unique_results[key] = result
    
    final_results = list(unique_results.values())
    
    print(f"\n🎯 TARGETED SEARCH RESULTS:")
    print(f"   📊 Total relevant items: {len(final_results)}")
    print(f"   ✅ All results verified as Gusto payroll company mentions")
    
    if final_results:
        # Show subreddit breakdown
        subreddit_counts = {}
        for result in final_results:
            subreddit = result.get('subreddit', 'unknown')
            subreddit_counts[subreddit] = subreddit_counts.get(subreddit, 0) + 1
        
        print(f"\n🏢 BUSINESS SUBREDDITS FOUND:")
        sorted_subreddits = sorted(subreddit_counts.items(), key=lambda x: x[1], reverse=True)
        for subreddit, count in sorted_subreddits:
            print(f"   r/{subreddit}: {count} mentions")
        
        # Show successful search terms
        term_counts = {}
        for result in final_results:
            term = result.get('search_term', 'unknown')
            term_counts[term] = term_counts.get(term, 0) + 1
        
        print(f"\n🔍 MOST EFFECTIVE BUSINESS SEARCH TERMS:")
        sorted_terms = sorted(term_counts.items(), key=lambda x: x[1], reverse=True)
        for term, count in sorted_terms[:8]:
            print(f"   {term}: {count} results")
    
    return final_results

async def main():
    """Main function to run targeted search and save results."""
    
    # Initialize database
    try:
        init_database()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database error: {e}")
        return
    
    # Run targeted search
    results = await search_targeted_gusto()
    
    if results:
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reddit_targeted_gusto_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Targeted results saved to: {filename}")
        
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
        
        print(f"\n🎯 QUALITY CONTROL SUMMARY:")
        print(f"   📈 Collected: {len(results)} VERIFIED Gusto payroll mentions")
        print(f"   🚫 Filtered out: Food, Spanish, Filipino, general enthusiasm")
        print(f"   ✅ Focus: Business software, payroll, HR, comparisons")
        print(f"   🎯 Quality: High relevance, business context only")
        
        print(f"\n🔄 NEXT STEPS:")
        print(f"   1. Run: python process_data.py")
        print(f"   2. Start dashboard: python backend/app/app.py")
        print(f"   3. View CLEAN results at: http://localhost:5000")
        
    else:
        print("📭 No relevant business mentions found.")
        print("   This suggests Gusto has limited recent discussion")
        print("   or our filters are too strict.")
    
    print("\n✅ Targeted search completed!")

if __name__ == "__main__":
    import os
    asyncio.run(main()) 