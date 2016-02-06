"""Logic-rule recommender system for drugs.
"""
import pymysql as pms
import pandas


def recommend(drug):
	"""logic-rule recommender for drug.  Reports sentiments for subsequent 
	switches coming off of given drug.

	ARGS:
		drug: string.
			name of drug.
	"""
	conn = pms.connect(host='localhost',
		user='root',
		passwd='',
		db='empath',
		charset='utf8',
		init_command='SET NAMES UTF8')
	cur = conn.cursor()

	# get post ids where drug is mentioned at precedence 1 (precedence 0 is 
	# always preamble)
	query = ("SELECT c.id,c.sents,c.nbsent from Chunks c "
		"JOIN Mentions m on c.id=m.id "
		"WHERE (m.count=2 AND c.drug='%s' AND c.precedence=1)" % drug.lower())
	starts = pandas.read_sql(query,conn)

	
	# get follow-on drugs, along with their sentiments
	finishes = {}
	for post_id in starts.id:
		print post_id
		query = ("SELECT c.id,c.drug,c.sents,c.nbsent from Chunks c "
			"WHERE (c.precedence=2 and c.id='%s')" % post_id)
		cur.execute(query)
		for row in cur:
			finishes[post_id] = (row[1],row[2],row[3])

	conn.close()


	return starts,finishes