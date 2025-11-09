import praw
import pandas as pd
import time
from datetime import datetime

# --- FILL IN YOUR CREDENTIALS --- #
CLIENT_ID = 'daMBf2Q5VDyixI_SM-_HHw'
CLIENT_SECRET = 'k86Oe_WGGE9hSOMRVCmsg_EBu7FSug'
USER_AGENT = 'LondonLTNSentiment by /u/DoubleEdge5528'

# --- SETUP REDDIT API INSTANCE (READ-ONLY MODE) --- #
print("Connecting to Reddit API...")
reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT
)
print(f"Connected! Read-only: {reddit.read_only}")

# --- KEYWORDS TO SEARCH --- #
keywords = [
    '"low traffic neighbourhood"',
    '"low-traffic neighbourhood"',
    '"low traffic neighborhood"',
    '"low-traffic neighborhood"', 
    '"low traffic zones"',
    '"low-traffic zones"',
    '"LTN"'
]

subreddit = reddit.subreddit("london")
results = []
seen_posts = set()  # Track unique posts to avoid duplicates

# --- FUNCTION TO SEARCH POSTS --- #
def search_ltn_posts(keyword):
    print(f"\nSearching for: '{keyword}'")
    post_count = 0
    comment_count = 0
    
    try:
        # Search for posts (limit 70 per keyword = ~200 unique posts after duplicates)
        for post in subreddit.search(keyword, limit=1500, sort='relevance', time_filter='all'):
            # Skip if we've already processed this post
            if post.id in seen_posts:
                continue
            
            seen_posts.add(post.id)
            post_count += 1
            
            # Save post data
            results.append({
                "type": "post",
                "id": post.id,
                "title": post.title,
                "created_utc": datetime.fromtimestamp(post.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
                "author": str(post.author) if post.author else "[deleted]",
                "body": post.selftext,
                "score": post.score,
                "num_comments": post.num_comments,
                "url": f"https://reddit.com{post.permalink}",
                "keyword_matched": keyword
            })
            
            # Get top 4 comments per post (200 posts × 4 comments = 800 comments + 200 posts = 1000 total)
            try:
                post.comments.replace_more(limit=0)
                comments_added = 0
                for comment in post.comments.list():
                    if hasattr(comment, 'body') and comments_added < 4:  # Limit to 4 comments per post
                        comment_count += 1
                        comments_added += 1
                        results.append({
                            "type": "comment",
                            "id": comment.id,
                            "parent_post_id": post.id,
                            "parent_post_title": post.title,
                            "created_utc": datetime.fromtimestamp(comment.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
                            "author": str(comment.author) if comment.author else "[deleted]",
                            "body": comment.body,
                            "score": comment.score,
                            "url": f"https://reddit.com{comment.permalink}",
                            "keyword_matched": keyword
                        })
            except Exception as e:
                print(f"  Error getting comments for post {post.id}: {e}")
        
        print(f"  Found {post_count} posts and {comment_count} comments")
        
    except Exception as e:
        print(f"  Error searching for '{keyword}': {e}")

# --- MAIN SEARCH LOOP --- #
for kw in keywords:
    search_ltn_posts(kw)
    time.sleep(2)  # Be nice to Reddit API

print(f"\n{'='*60}")
print(f"Total collected: {len(results)} items ({len(seen_posts)} unique posts)")
print(f"{'='*60}")

# --- SAVE TO CSV --- #
if results:
    df = pd.DataFrame(results)
    df.to_csv("ltn_london_reddit.csv", index=False, encoding='utf-8')
    print(f"\n✓ Data saved to ltn_london_reddit.csv")
    print(f"  Posts: {len(df[df['type'] == 'post'])}")
    print(f"  Comments: {len(df[df['type'] == 'comment'])}")
else:
    print("\n✗ No results found. Check your keywords or try different search terms.")
