"""Sentiment analysis readouts from `empath`.`Chunks` table.
"""
import pymysql as pms
from collections import Counter
import numpy as np
from word_count import tokenize


def corenlp_sentiment(drug=None):
	"""Parses Stanford CoreNLP sentiment analysis from table.

	KWARGS:
		drug: string or None.
			drug name.  If None, returns all results in `empath`.`Chunks`.

	RETURNS:
		count: collections.Counter object.
	"""
	conn = pms.connect(host='localhost',
		user='root',
		passwd='',
		db='empath',
		charset='utf8',
		init_command='SET NAMES UTF8')
	cur = conn.cursor()

	if drug is not None:
		drug = drug.lower()
		cur.execute("SELECT sents FROM Chunks WHERE drug=%s",drug)
	else:
		cur.execute("SELECT sents FROM Chunks")
	sentiments = []
	for row in cur:
		sents = row[0].split()
		c = Counter(sents)
		sentiments.append(c.most_common(1)[0][0])
		#for sent in sents:
			#sentiments.append(sent)
	conn.close()

	total = len(sentiments)
	count = Counter(sentiments)
	return (count,total)


def nba_sentiment(drug=None):
	"""Parses Naive Bayes Analyzer sentiment analysis from table.

	KWARGS:
		drug: string or None.
			drug name.  If None, returns all results in `empath`.`Chunks`.

	RETURNS:
		nbsent: float.
			mean value of Naive-Bayes calculated sentiment positivity score.
	"""
	conn = pms.connect(host='localhost',
		user='root',
		passwd='',
		db='empath',
		charset='utf8',
		init_command='SET NAMES UTF8')
	cur = conn.cursor()

	if drug is not None:
		drug = drug.lower()
		cur.execute("SELECT nbsent FROM Chunks WHERE drug=%s",drug)
	else:
		cur.execute("SELECT nbsent FROM Chunks")
	sentiments = []
	for row in cur:
		sent = float(row[0])
		sentiments.append(sent)
	conn.close()

	sentiments = np.array(sentiments)
	return sentiments.mean()