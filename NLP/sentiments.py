"""Sentiment analysis readouts from `empath`.`Chunks` table.
"""
import pymysql as pms
from collections import Counter
import numpy as np


def corenlp_sentiment(drug):
	"""Parses Stanford CoreNLP sentiment analysis from table.

	ARGS:
		drug: string.
			drug name.
	"""
	drug = drug.lower()
	conn = pms.connect(host='localhost',
		user='root',
		passwd='',
		db='empath',
		charset='utf8',
		init_command='SET NAMES UTF8')
	cur = conn.cursor()

	cur.execute("SELECT sents from Chunks WHERE drug=%s",drug)
	sentiments = []
	for row in cur:
		sents = row[0].split()
		for sent in sents:
			sentiments.append(sent)
	conn.close()

	total = len(sentiments)
	count = Counter(sentiments)
	return (count,total)


def nba_sentiment(drug):
	"""Parses Naive Bayes Analyzer sentiment analysis from table.

	ARGS:
		drug: string.
			drug name.
	"""
	drug = drug.lower()
	conn = pms.connect(host='localhost',
		user='root',
		passwd='',
		db='empath',
		charset='utf8',
		init_command='SET NAMES UTF8')
	cur = conn.cursor()

	cur.execute("SELECT nbsent from Chunks WHERE drug=%s",drug)
	sentiments = []
	for row in cur:
		sent = float(row[0])
		sentiments.append(sent)
	conn.close()

	sentiments = np.array(sentiments)
	return sentiments.mean()