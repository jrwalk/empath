"""scraper to build DB of subreddit subscriber counts for use in normalization 
of comment scores.
"""
import pymysql as pms
import praw
import pandas

def fill():
	"""Wrapper to query reddit API to get subscriber count of a subreddit, post 
	count from `empath`.`Comments` SQL db.  Write into `empath`.`Subreddits` db.
	"""
	conn = pms.connect(host='localhost',
		user='root',
		passwd='',
		db='empath')
	cur = conn.cursor()
	cur.execute('SELECT subreddit from Comments')
	subs = []
	for row in cur:
		subs.append(row[0])
	subs = pandas.Series(subs)
	subs_unique = pandas.Series(subs.unique())

	reddit = praw.Reddit(user_agent='subreddit subscriber checker')
	for sub in subs_unique:
		try:
			subscribers = reddit.get_subreddit(sub).subscribers
		except:
			subscribers = None	# private subreddit can't get subscriber count
		posts = int(subs.value_counts()[sub])
		print("%s\t%s\t%s" % (sub,subscribers,posts))
		cur.execute("INSERT INTO Subreddits "
			"(subreddit,"
			"subscribers,"
			"posts) "
			"VALUES (%s,%s,%s)",
			(sub,subscribers,posts))

	conn.commit()
	conn.close()