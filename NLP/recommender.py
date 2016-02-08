"""Logic-rule recommender system for drugs.
"""
import pymysql as pms
import pandas
from collections import Counter


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

	# first, get how many (chunked) comments stayed on the drug -- assume 
	# single mentions mean that.
	query = ("SELECT c.id from Chunks c "
		"JOIN Mentions m on c.id=m.id "
		"WHERE (m.count=1 AND c.drug='%s')" % drug.lower())
	stayed_on_drug = cur.execute(query)

	# get post ids where drug is mentioned at precedence 1 (precedence 0 is 
	# always preamble)
	starts = {}
	query = ("SELECT c.id,c.sents,c.nbsent from Chunks c "
		"JOIN Mentions m on c.id=m.id "
		"WHERE (m.count=2 AND c.drug='%s' AND c.precedence=1)" % drug.lower())
	cur.execute(query)
	for row in cur:
		starts[row[0]] = (row[1],row[2])
	
	# get follow-on drugs, along with their sentiments
	finishes = {}
	for post_id in starts.keys():
		query = ("SELECT c.id,c.drug,c.sents,c.nbsent from Chunks c "
			"WHERE (c.precedence=2 and c.id='%s')" % post_id)
		cur.execute(query)
		for row in cur:
			finishes[post_id] = (row[1],row[2],row[3])
	conn.close()

	# cast to pandas dataframe
	data = {}
	for post_id in starts.keys():
		init_data = starts[post_id]
		final_data = finishes[post_id]
		data[post_id] = init_data+final_data

	data = pandas.DataFrame.from_dict(data,orient='index')
	data.columns = ['init_sent','init_nbsent',
		'drug','final_sent','final_nbsent']

	switched_drug = len(data)
	data = data[data.final_nbsent > data.init_nbsent]
	better_switched_drug = len(data)

	count_drugs = Counter(data.drug.values)
	best_drug = count_drugs.most_common(1)[0]

	return stayed_on_drug,switched_drug,better_switched_drug,best_drug