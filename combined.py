from IPython import display
import math
from pprint import pprint
import pandas as pd
import numpy as np
import re
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer as SIA
from nltk.corpus import stopwords
import matplotlib.pyplot as plt
import seaborn as sns
import praw
from praw.models import MoreComments
sns.set(style='darkgrid', context='talk', palette='Dark2')

# read a list of headlines and perform lowercasing, tokenizing, and stopword removal
def process_text(headlines):
    tokens = []
    for line in headlines:
        toks=line.split()
        # toks = tokenizer.tokenize(line)
        # toks = [t for t in toks if t not in stop_words]
        toks = [t for t in toks if not re.match("\(?((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*\)?", t)]
        tokens.extend(toks)
    return tokens

def process_text_line(line):
    toks=line.split()
    toks = [t for t in toks if not re.match("\(?((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*\)?", t)]
    return " ".join(toks)

def print_comments(headlines):
    print('comments')

# tokenizer that only looks at words, not punctuation
# more tokenizers at http://www.n|\S+ltk.org/api/nltk.tokenize.htm
# tokenizer = RegexpTokenizer(r'\w+|\s+')

# stop_words are somewhat irrelevant to text sentiment and don't provide any valuable information. can replace with another set
stop_words = stopwords.words('english')
#['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers']

reddit_client_id = ""
reddit_client_secret = ""
reddit_user_agent = ""
# reddit praw connector
reddit = praw.Reddit(client_id='reddit_client_id',
                     client_secret='reddit_client_secret-Q',
                     user_agent='reddit_user_agent')

totalMap = {}
subreddits = ['politics', 'worldnews', 'news', 'geopolitics', 'nottheonion']
postLimit = 1000

for subreddit in subreddits:
    tempSet = set()
    for submission in reddit.subreddit(subreddit).top(limit=postLimit):
        display.clear_output()
        tempSet.add(submission)
        # print("ID:", submission.id, "TITLE", submission.title)
    totalMap[subreddit] = tempSet
    
sia = SIA()
for subreddit in totalMap:

    df2 = pd.DataFrame()
    headlineResults = []
    
    subredditSet = totalMap[subreddit]

    for submission in subredditSet:
        commentResults = []
        # analyze headlines
        line = process_text_line(submission.title)
        pol_score = sia.polarity_scores(line)
        pol_score['submission_id'] = submission.id
        headlineResults.append(pol_score)
        # analyze comments
        submission.comment_sort = "top"
        comments = submission.comments.list()
        comments = comments[:100]
        for comment in comments:
            if isinstance(comment, MoreComments):
                continue
            line = process_text_line(comment.body)
            pol_score = sia.polarity_scores(line)
            pol_score['submission_id'] = submission.id
            commentResults.append(pol_score)

        df = pd.DataFrame.from_records(commentResults)
        df.head()
        #sentiment categorization
        df['label'] = 0
        df.loc[df['compound'] > 0.3, 'label'] = 1
        df.loc[df['compound'] < -0.3, 'label'] = -1
        df.head()
        pmap = df.label.value_counts(normalize=True, sort=False) * 100
        retDistribution = [(0,0) for i in range(3)]
        retPercentage = [(0,0) for i in range(3)]
        for a in pmap.items():
            if a[0] == -1:
                retDistribution[0] = a[1]
            elif a[0] == 0:
                retDistribution[1] = a[1]
            elif a[0] == 1:
                retDistribution[2] = a[1]
        for a in (df.label.value_counts(sort=False)).items():
            if a[0] == -1:
                retPercentage[0] = a[1]
            elif a[0] == 0:
                retPercentage[1] = a[1]
            elif a[0] == 1:
                retPercentage[2] = a[1]
        # print(retDistribution)
        # print(retPercentage)
        # temporary datafram to add the analysis of each comment for the particular subreddit
        tempdf = pd.DataFrame({'submission_id': np.repeat([submission.id],3),
                       'label': [-1,0,1],
                        'comment_ditribution' : retDistribution,
                        'comment_percentage': retPercentage}
                       )
        #concatenating the results for each subreddit
        df2 = pd.concat([df2, tempdf], ignore_index=True)
    
    #headlines
    dfH = pd.DataFrame.from_records(headlineResults)
    dfH.head()
    dfH['label'] = 0
    dfH.loc[dfH['compound'] > 0.3, 'label'] = 1
    dfH.loc[dfH['compound'] < -0.3, 'label'] = -1
    dfH.head()
    dfH2 = dfH[['submission_id', 'label']]
    dfH2.to_csv(subreddit + "_headlines_labels.csv", mode='a', encoding='utf-8', index=False)
    #comments
    df2.to_csv(subreddit + "_comment_labels.csv", mode='a', encoding='utf-8', index=False)