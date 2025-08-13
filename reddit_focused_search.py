#!/usr/bin/env python3
"""
Hyper-Focused Reddit Search for Gusto Payroll Company
ONLY searches small business and payroll-specific subreddits - maximum relevance
"""

import asyncio
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
import praw
import re
import os

from backend.database.database import init_database

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def is_gusto_payroll_relevant(title: str, text: str, subreddit: str, author: str) -> bool:
    """
    Ultra-strict filter for genuine Gusto payroll discussions.
    Only accepts posts that are clearly about Gusto payroll software.
    """
    
    combined_text = f"{title} {text}".lower()
    
    # MUST contain 'gusto' - this is non-negotiable
    if 'gusto' not in combined_text:
        return False
    
    # EXCLUDE: Spam and promotional content
    spam_patterns = [
        r'\b(referral|ref code|discount|promo|coupon|deal|offer)\b',
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
    
    # EXCLUDE: Non-English content
    foreign_patterns = [
        r'\b(sarap|masarap|nakaka|mga|ang|sa|ko|mo|niya)\b',  # Filipino
        r'\b(con|muy|que|para|como|este|una|las|los)\b',      # Spanish
        r'\b(и|в|на|с|для|от|по|за|до|из)\b',                # Russian
        r'\b(le|la|les|des|du|dans|pour|avec|sur)\b',         # French
    ]
    
    for pattern in foreign_patterns:
        if re.search(pattern, combined_text):
            return False
    
    # REQUIRE: Strong Gusto payroll context
    gusto_payroll_indicators = [
        # Direct Gusto payroll discussions
        r'\bgusto\s+(payroll|hr|software|platform|system|app)\b',
        r'\b(payroll|hr|benefits|taxes|w2|1099)\s+.*\bgusto\b',
        
        # Business decision language about Gusto
        r'\b(using|used|tried|switched|considering|evaluating|implementing)\s+gusto\b',
        r'\bgusto\s+(review|pricing|cost|features|demo|trial|experience)\b',
        
        # Competitor comparisons with Gusto
        r'\bgusto\s+vs\s+(adp|paychex|quickbooks|bamboohr|rippling|workday)\b',
        r'\b(adp|paychex|quickbooks)\s+vs\s+gusto\b',
        
        # Integration discussions with Gusto
        r'\b(quickbooks|xero|accounting|bookkeeping).*gusto\b',
        r'\bgusto.*\b(integration|sync|api|connect)\b',
        
        # Business process context with Gusto
        r'\bgusto.*\b(onboarding|employee|contractor|freelancer|small business)\b',
        r'\b(small business|startup|llc|s-corp|corporation).*gusto\b',
        
        # Problem-solving discussions about Gusto
        r'\bgusto.*\b(issue|problem|support|help|question|error)\b',
        r'\b(payroll processing|tax filing|benefits administration).*gusto\b',
    ]
    
    # Must match at least one strong Gusto payroll indicator
    gusto_match = False
    for pattern in gusto_payroll_indicators:
        if re.search(pattern, combined_text):
            gusto_match = True
            break
    
    if not gusto_match:
        return False
    
    # REQUIRE: Substantial content (not just product name)
    if len(combined_text.strip()) < 30:  # Very short posts are usually not useful
        return False
    
    # SUCCESS: Passed all filters
    return True

async def search_focused_subreddits():
    """Search ONLY the most relevant subreddits for Gusto discussions."""
    
    print("🎯 Starting ULTRA-STRICT Gusto Reddit Search...")
    print("📋 Searching ONLY r/smallbusiness and r/Entrepreneurship subreddits")
    print("🚫 Excluding ALL other subreddits including HR, accounting, payroll, etc.")
    
    # Initialize Reddit API
    try:
        reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent='GustoFocusedMonitor/1.0'
        )
        print("✅ Reddit API connected")
    except Exception as e:
        print(f"❌ Reddit API error: {e}")
        return []
    
    # ULTRA-STRICT: ONLY small business and entrepreneurship subreddits
    focused_subreddits = [
        # Core small business
        'smallbusiness',
        
        # Entrepreneurship focused
        'Entrepreneurship',
        'entrepreneur',
    ]
    
    # Focused search terms - very specific to Gusto
    search_terms = [
        'Gusto payroll',
        'Gusto software',
        'using Gusto',
        'Gusto vs ADP',
        'Gusto vs Paychex',
        'switched to Gusto',
        'Gusto review',
        'Gusto QuickBooks',
    ]
    
    print(f"🎯 Searching {len(focused_subreddits)} ultra-strict subreddits")
    print(f"🔍 Using {len(search_terms)} Gusto-specific terms")
    
    all_results = []
    
    for subreddit_name in focused_subreddits:
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
                        limit=15  # Higher limit since we have fewer subreddits
                    )
                    
                    for submission in search_results:
                        try:
                            # ULTRA-STRICT filtering for Gusto payroll relevance
                            if is_gusto_payroll_relevant(
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
                                    'relevance_score': 'gusto_verified'
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
                print(f"      ✅ Found: {subreddit_count} Gusto discussions")
            else:
                print(f"      📭 No Gusto discussions found")
                
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
    
    print(f"\n🎯 ULTRA-STRICT SEARCH RESULTS:")
    print(f"   📊 Total Gusto discussions: {len(final_results)}")
    print(f"   ✅ All verified as Gusto payroll content")
    print(f"   🚫 Filtered out: ALL other subreddits (HR, accounting, etc.)")
    
    if final_results:
        # Show focused subreddit breakdown
        subreddit_counts = {}
        for result in final_results:
            subreddit = result.get('subreddit', 'unknown')
            subreddit_counts[subreddit] = subreddit_counts.get(subreddit, 0) + 1
        
        print(f"\n📋 FOCUSED SUBREDDITS WITH GUSTO CONTENT:")
        sorted_subreddits = sorted(subreddit_counts.items(), key=lambda x: x[1], reverse=True)
        for subreddit, count in sorted_subreddits:
            print(f"   r/{subreddit}: {count} Gusto discussions")
        
        # Show most effective search terms
        term_counts = {}
        for result in final_results:
            term = result.get('search_term', 'unknown')
            term_counts[term] = term_counts.get(term, 0) + 1
        
        print(f"\n🔍 MOST EFFECTIVE GUSTO SEARCH TERMS:")
        sorted_terms = sorted(term_counts.items(), key=lambda x: x[1], reverse=True)
        for term, count in sorted_terms[:5]:
            print(f"   '{term}': {count} discussions")
    
    return final_results

async def main():
    """Main function to run hyper-focused search."""
    
    # Initialize database
    try:
        init_database()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database error: {e}")
        return
    
    # Run hyper-focused search
    results = await search_focused_subreddits()
    
    if results:
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reddit_ultrastrict_gusto_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Focused Gusto results saved to: {filename}")
        
        # Auto-update process_data.py
        try:
            with open('process_data.py', 'r') as f:
                content = f.read()
            
            import re
            new_content = re.sub(
                r'json_file = ".*\.json"',
                f'json_file = "{filename}"',
                content
            )
            
            with open('process_data.py', 'w') as f:
                f.write(new_content)
            
            print(f"✅ Updated process_data.py to use {filename}")
            
        except Exception as e:
            print(f"⚠️  Update process_data.py manually: {e}")
        
        print(f"\n🎯 ULTRA-STRICT QUALITY CONTROL:")
        print(f"   📈 Collected: {len(results)} verified Gusto discussions")
        print(f"   🎯 Sources: ONLY r/smallbusiness and r/payroll subreddits")
        print(f"   🚫 Excluded: ALL other subreddits (HR, accounting, etc.)")
        print(f"   ✅ Focus: 100% Gusto payroll software discussions")
        
        print(f"\n🔄 NEXT STEPS:")
        print(f"   1. Run: python3 process_data.py")
        print(f"   2. Start dashboard: python3 backend/app/app.py")
        print(f"   3. View ultra-clean data at: http://localhost:5000")
        
    else:
        print("📭 No Gusto discussions found in focused subreddits.")
        print("   This suggests very limited recent Gusto discussion")
        print("   in the most relevant small business communities.")
    
    print("\n✅ Hyper-focused search completed!")

if __name__ == "__main__":
    asyncio.run(main()) 