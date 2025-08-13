#!/usr/bin/env python3
"""
Site-wide Reddit search for Gusto mentions using broader search approach
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import praw

from backend.database.database import init_database

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def search_reddit_site_wide():
    """Site-wide Reddit search for Gusto mentions."""
    
    print("🚀 Starting SITE-WIDE Reddit Search for Gusto...")
    print("🔍 Using Reddit's general search (not subreddit-specific)")
    print("📅 Focusing on recent activity (last 30 days)")
    
    # Initialize Reddit API
    try:
        reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent='GustoSocialMonitor/1.0'
        )
        print("✅ Reddit API connected")
    except Exception as e:
        print(f"❌ Reddit API error: {e}")
        return []
    
    all_results = []
    
    # Simpler, more targeted keywords
    search_terms = [
        "Gusto payroll",
        "Gusto HR", 
        "Gusto software",
        "Gusto vs",
        "Gusto review",
        "gustohq",
        "gusto.com"
    ]
    
    print(f"🔍 Searching for {len(search_terms)} terms across all of Reddit...")
    
    for term in search_terms:
        try:
            print(f"   Searching: '{term}'")
            
            # Site-wide search with recent focus
            search_results = reddit.subreddit("all").search(
                query=term,
                sort='new',
                time_filter='month',  # Last month
                limit=25  # Get more results per term
            )
            
            count = 0
            for submission in search_results:
                try:
                    # Check if it's actually about Gusto (not just random word matches)
                    content = f"{submission.title} {submission.selftext}".lower()
                    if any(word in content for word in ['gusto', 'payroll', 'hr']):
                        
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
                            'search_term': term
                        }
                        
                        all_results.append(result)
                        count += 1
                        
                        # Also check top comments
                        submission.comments.replace_more(limit=0)
                        for comment in submission.comments[:3]:  # Top 3 comments
                            if hasattr(comment, 'body') and 'gusto' in comment.body.lower():
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
                                    'search_term': f"{term} (comment)"
                                }
                                all_results.append(comment_result)
                                count += 1
                
                except Exception as e:
                    logger.warning(f"Error processing submission: {e}")
                    continue
            
            print(f"      Found: {count} items")
            
            # Add delay to avoid rate limits
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"❌ Error searching '{term}': {e}")
            continue
    
    # Remove duplicates
    unique_results = {}
    for result in all_results:
        key = result['post_id']
        if key not in unique_results:
            unique_results[key] = result
    
    final_results = list(unique_results.values())
    
    print(f"\n📊 SITE-WIDE SEARCH RESULTS:")
    print(f"   Total unique items: {len(final_results)}")
    
    if final_results:
        # Show breakdown by subreddit
        subreddit_counts = {}
        for result in final_results:
            subreddit = result.get('subreddit', 'unknown')
            subreddit_counts[subreddit] = subreddit_counts.get(subreddit, 0) + 1
        
        print(f"\n🏆 TOP SUBREDDITS FOUND:")
        sorted_subreddits = sorted(subreddit_counts.items(), key=lambda x: x[1], reverse=True)
        for subreddit, count in sorted_subreddits[:10]:
            print(f"   r/{subreddit}: {count} mentions")
        
        # Show search terms that worked
        term_counts = {}
        for result in final_results:
            term = result.get('search_term', 'unknown')
            term_counts[term] = term_counts.get(term, 0) + 1
        
        print(f"\n🔍 SUCCESSFUL SEARCH TERMS:")
        sorted_terms = sorted(term_counts.items(), key=lambda x: x[1], reverse=True)
        for term, count in sorted_terms:
            print(f"   '{term}': {count} results")
    
    return final_results

async def main():
    """Main function to run site-wide search and save results."""
    
    # Initialize database
    try:
        init_database()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database error: {e}")
        return
    
    # Run site-wide search
    results = await search_reddit_site_wide()
    
    if results:
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reddit_sitewide_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filename}")
        
        # Update process_data.py
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
        
        print(f"\n🔄 NEXT STEPS:")
        print(f"   1. Run: python process_data.py")
        print(f"   2. Start dashboard: python backend/app/app.py")
        print(f"   3. View results at: http://localhost:5000")
        
    else:
        print("📭 No results found with site-wide search either.")
        print("This suggests:")
        print("   - Very few Gusto mentions on Reddit recently")
        print("   - Reddit API limitations")
        print("   - Need to try different search approaches")
    
    print("\n✅ Site-wide search completed!")

if __name__ == "__main__":
    import os
    asyncio.run(main()) 