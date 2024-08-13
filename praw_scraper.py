
import os
import praw
import numpy
import pandas

# Create a function to retrieve the reddit posts, as per the requirements of PRAW. We will need several unique keys for authentication 
# before being able to call the api and this can be done by creating a developer script application on reddit. Below client_id, client_secret and
# user_agent are taken from the details of the script application, after it has been created.

def get_reddit_posts(sub_reddit: str, post_type: str,
                     nsfw=True,
                     limit=None
                     ):
    
    # Authenticating via PRAW's OAuth

    client_id = os.environ.get('CLIENT_ID')
    client_secret = os.environ.get('CLIENT_SECRET')
    user_agent = os.environ.get('USER_AGENT')
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )

    # Declaring the subreddit to be scraped

    subreddit = reddit.subreddit(sub_reddit)

    # Retrieving posts from different categories that the posts are categorized in

    if post_type == 'new':
        all_posts = subreddit.new(limit=limit)
    elif post_type == 'hot':
        all_posts = subreddit.hot(limit=limit)
    elif post_type == 'top':
        all_posts = subreddit.top(limit=limit)
    elif post_type == 'rising':
        all_posts = subreddit.rising(limit=limit)
    else:
        raise ValueError(f"Unrecognized post_type: {post_type}", nsfw=nsfw)

    return list(all_posts)

# Create a function to get the body, comments and subcomments from each post.

def get_post_texts(all_posts: list,
                   get_all_comments=False,
                   score_threshold= -np.inf):

    # Get bundled post body and associated comments in a list
    all_post_texts = []
    counter=-1

    for post in all_posts:
        counter+=1
        if counter%50==0:
            print(f'{counter} of {len(all_posts)} posts processed.')
        post_text = []
        if post.score < score_threshold:
            continue
        post_text.append(post.title)                        # Add title of post
        post_text.append(post.selftext)                     # Add main body of post
        
        if get_all_comments:
            post.comment_sort = "top"
            post.comments.replace_more(limit=None)             # Replace morecomments objects with more comments
            time.sleep(1)
        else:
            post.comments.replace_more(limit=0)                # Remove morecomments object

        post_agg_comments = process_comments(post.comments,score_threshold)     # Get all comments and subcomments
        post_text += post_agg_comments
        all_post_texts.append(post_text)

    return all_posts,all_post_texts

# Create a function to process the comments. The comments and replies with scores below the threshold will not be included.
# We are also formatting the comments to be joined as one long string, but delimited with a '|'

def process_comments(comments, score_threshold):

    def process_replies(comment, replies):
        if comment.score < score_threshold:
            return replies
        if len(comment.replies) > 0:
            for reply in comment.replies:
                replies.append(f'{reply.body} (score: {reply.score})')
                process_replies(reply, replies)
        return replies
    
    agg_comments = []
    for comment in comments:
        if comment.score >= score_threshold:
            comment_and_replies = [f'{comment.body} (score: {comment.score})']
            replies = process_replies(comment, [])
            if replies:
                comment_and_replies.extend(replies)
            agg_comments.append(" | ".join(comment_and_replies))  # Combine comment and its replies with delimiter
    return agg_comments

# The next block of code is used to call the above functions for 4 different categories of the subreddit
# and create a dataframe with the decided features which will be used for our model training. The dataframe is then
# exported into a file to be loaded later on. The first subreddit we will scrape from is r/MentalHealth.

cats_to_scrape = ['new', 'hot', 'rising', 'top']
full_dataset = []

for cats in cats_to_scrape:
    posts = get_reddit_posts(sub_reddit='mentalhealth', post_type=cats)
    posts_texts = get_post_texts(posts, get_all_comments=True)

    for post, text in zip(posts,posts_texts):
        full_dataset.append({
            'id': post.id,
            'title': post.title,
            'body': post.score,
            'num_comments': post.num_comments,
            'comments': text[2:],
            'category': cats
        })

full_df = pd.DataFrame(full_dataset)
full_df.to_csv('Subreddit_mentalhealth_20240614.csv')

# We will repeat the scraping again for r/CasualConversation.

cats_to_scrape = ['new', 'hot', 'rising', 'top']
full_dataset = []

for cats in cats_to_scrape:
    posts = get_reddit_posts(sub_reddit='casualconversation', post_type=cats)
    posts_texts = get_post_texts(posts, get_all_comments=True)

    for post, text in zip(posts,posts_texts):
        full_dataset.append({
            'id': post.id,
            'title': post.title,
            'body': post.score,
            'num_comments': post.num_comments,
            'comments': text[2:],
            'category': cats
        })

full_df = pd.DataFrame(full_dataset)
full_df.to_csv('subreddit_casualconversation_20240614.csv')
