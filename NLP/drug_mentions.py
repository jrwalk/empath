"""Getters for texts/data for specific drugs.
"""
import pymysql as pms

import build_drug_dict as bdd
_drug_dict = bdd.build_drug_dict(
	'/home/jrwalk/python/empath/data/drugs/antidepressants.txt')


def texts(drug=None,limit=None):
	"""Generator of texts for selected drug.

	KWARGS:
		drug: string or None.
			Drug selector.  Allows three cases:
			* None: scrape all comments in database, regardless of drug.
			* 'antidepressant': select comments speaking generically about
				drug, not referencing specific drug.
			* [drug name]: comments referencing specific drug.
			Default None.
		limit: int or None.
			Optional limit for SQL pull (for speed/testing purposes), capping 
			number of rows queried.

	YIELDS:
		body: string.
			Comment body for selected posts.

	RAISES:
		ValueError:
			on invalid drug name.
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
		if limit is None:
			query = "SELECT body FROM Comments"
		else:
			query = ("SELECT body FROM Comments "
				#"ORDER BY score DESC "
				"LIMIT %s" 
				% (limit))
		cur.execute(query)
	elif drug.upper() == 'ANTIDEPRESSANT':
		if limit is None:
			query = ("SELECT c.body FROM Comments c "
				"JOIN Mentions m ON m.id=c.id "
				"WHERE m.count=0")
		else:
			query = ("SELECT c.body FROM Comments c "
				"JOIN Mentions m ON m.id=c.id "
				"WHERE m.count=0 "
				#"ORDER BY c.score DESC "
				"LIMIT %s" % (limit))
		cur.execute(query)
	else:
		drug = _drug_dict.get(drug.upper(),None)
		if drug is None:
			raise ValueError('Invalid drug selection.')

		if limit is None:
			query = ("SELECT c.body FROM Comments c "
				"JOIN Mentions m ON m.id=c.id "
				"WHERE m.%s=True" % drug.lower())
		else:
			query = ("SELECT c.body FROM Comments c "
				"JOIN Mentions m ON m.id=c.id "
				"WHERE m.%s=True "
				#"ORDER BY c.score DESC "
				"LIMIT %s" % (drug.lower(),limit))
		cur.execute(query)

	conn.close()

	for row in cur:
		yield row[0]


def chunks(drug,limit=None):
	"""Generator of chunks for selected drug.
	"""