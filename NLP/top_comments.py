"""scrapes top n comments mentioning a given drug, returns parseable form.
"""
import pymysql as pms
import pandas
from pandas import Timestamp
import re
import numpy as np

import build_drug_dict as bdd
_drug_dict = bdd.build_drug_dict(
	'/home/jrwalk/python/empath/data/drugs/antidepressants.txt')


def top_comments_simple(drug=None,n=5):
	"""retrieves top n comments for given drug, returns parseable format.  
	Ranks top comments by raw score (rendered by SQL query).

	KWARGS:
		drug: string or None.
			Drug selector.  Allows three cases:
			* None: scrape all comments in database, regardless of drug.
			* 'antidepressant': select comments speaking generically about
				drug, not referencing specific drug.
			* [drug name]: comments referencing specific drug.
			Default None.
		n: int.
			number of top comments to return.

	YIELDS:
		Iterable of top n comments.

	RAISES:
		ValueError:
			On invalid drug selection.
	"""
	conn = pms.connect(
		host='localhost',
		user='root',
		passwd='',
		db='empath',
		charset='utf8',
		init_command='SET NAMES UTF8')
	cur = conn.cursor()

	if drug is None:
		gen = None
		query = ("SELECT author,body,created_utc,score,subreddit from Comments "
			"ORDER BY score DESC "
			"LIMIT %s" % n)
	elif drug.upper() == 'ANTIDEPRESSANT':
		gen = None
		query = ("SELECT c.author,c.body,c.created_utc,c.score,c.subreddit "
			"FROM Comments c "
			"JOIN Mentions m on m.id=c.id "
			"WHERE m.count=0 "
			"ORDER BY c.score DESC "
			"LIMIT %s" % n)
	else:
		gen = _drug_dict.get(drug.upper(),None)
		if gen is None:
			raise ValueError('Invalid drug selection.')

		query = ("SELECT c.author,c.body,c.created_utc,c.score,c.subreddit "
			"FROM Comments c "
			"JOIN Mentions m on m.id=c.id "
			"WHERE m.%s=True "
			"ORDER BY c.score DESC "
			"LIMIT %s" % (gen.lower(),n))
	cur.execute(query)

	conn.close()

	for row in cur:
		author = row[0]
		body = row[1]
		created_utc = row[2]
		score = row[3]
		subreddit = row[4]

		created_utc = str(Timestamp.utcfromtimestamp(int(created_utc)))

		#if drug is not None:
		#	bodymod = re.compile(drug,re.IGNORECASE)
		#	body = bodymod.sub("%s" % drug,body)
		#if gen is not None:
		#	bodymod = re.compile(gen,re.IGNORECASE)
		#	body = bodymod.sub("%s" % gen,body)

		yield (author,body,created_utc,score,subreddit)


def top_comments(drug=None,n=5):
	"""retrieves top n comments for given drug, returns parseable format.  
	Ranks top comments by score normalized to subreddit population.

	KWARGS:
		drug: string or None.
			Drug selector.  Allows three cases:
			* None: scrape all comments in database, regardless of drug.
			* 'antidepressant': select comments speaking generically about
				drug, not referencing specific drug.
			* [drug name]: comments referencing specific drug.
			Default None.
		n: int.
			number of top comments to return.

	YIELDS:
		Iterable of top n comments.

	RAISES:
		ValueError:
			On invalid drug selection.
	"""
	conn = pms.connect(
		host='localhost',
		user='root',
		passwd='',
		db='empath',
		charset='utf8',
		init_command='SET NAMES UTF8')
	cur = conn.cursor()

	if drug is None:
		gen = None
		query = ("SELECT c.author,c.body,c.created_utc,c.score,c.subreddit,"
			"s.subscribers FROM Comments c "
			"JOIN Subreddits s ON s.subreddit=c.subreddit")
	elif drug.upper() == 'ANTIDEPRESSANT':
		gen = None
		query = ("SELECT c.author,c.body,c.created_utc,c.score,c.subreddit,"
			"s.subscribers FROM Comments c "
			"JOIN Subreddits s ON s.subreddit=c.subreddit")
	else:
		gen = _drug_dict.get(drug.upper(),None)
		if gen is None:
			raise ValueError('Invalid drug selection.')

		query = ("SELECT c.author,c.body,c.created_utc,c.score,c.subreddit,"
			"s.subscribers FROM Comments c "
			"JOIN Subreddits s ON s.subreddit=c.subreddit "
			"JOIN Mentions m ON m.id=c.id "
			"WHERE m.%s=True" % gen.lower())
	data = pandas.read_sql(query,conn)
	conn.close()

	data['normscore'] = data.score/data.subscribers**.33
	data.sort_values(by='normscore',ascending=False,inplace=True)
	data = data[:n]

	for row in data.iterrows():
		entry = row[1]	# pandas.Series
		author = entry.author
		body = entry.body
		created_utc = entry.created_utc
		score = entry.score
		subreddit = entry.subreddit

		created_utc = str(Timestamp.utcfromtimestamp(int(created_utc)))

		#if drug is not None:
		#	bodymod = re.compile(drug,re.IGNORECASE)
		#	body = bodymod.sub("**%s*" % drug,body)
		#if gen is not None:
		#	bodymod = re.compile(gen,re.IGNORECASE)
		#	body = bodymod.sub("**%s**" % gen,body)

		yield (author,body,created_utc,score,subreddit)