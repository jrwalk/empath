"""quick script to correct precedence ordering in existing data in 
`empath`.`Chunks` due to bug in chunker.build_chunks.
"""
import pymysql as pms
import numpy as np
from word_count import tokenize
from ordered_set import OrderedSet

import build_drug_dict as bdd
_drug_dict = bdd.build_drug_dict(
	'/home/jrwalk/python/empath/data/drugs/antidepressants.txt')
_generics = bdd.generics(_drug_dict)
_gen_dict = bdd.generic_dict(_drug_dict)


def uniconvert(s):
	if s == '\x00':
		return 0
	elif s == '\x01':
		return 1
	else:
		return None


def fix():
	conn = pms.connect(host='localhost',
		user='root',
		passwd='',
		db='empath',
		charset='utf8',
		init_command='SET NAMES UTF8')
	cur = conn.cursor()

	# get chunked comment ids
	query = "SELECT c.id,c.body"
	for gen in _generics:
		query += (",m.%s" % gen.lower())
	query += " FROM Comments c "
	query += "JOIN Mentions m on c.id=m.id WHERE c.chunked=True"
	cur.execute(query)

	data = {}
	for row in cur:
		drugs = np.array([uniconvert(d) for d in row[2:]])
		dmap = np.where(drugs == 1)
		drugs = [d.lower() for d in list(np.array(_generics)[dmap])]
		data[row[0]] = (row[1],drugs)

	for post_id in data.keys():
		body,drugs = data[post_id]

		body = body.lower()
		for drug in drugs:
			for remap in _gen_dict.get(drug.upper(),[drug.upper()]):
				body = body.replace(remap.lower(),drug.lower())

		# set preamble order to correct precedence
		query = ("UPDATE Chunks SET precedence=0 WHERE (id='%s' "
			"AND drug='preamble')" % post_id)
		cur.execute(query)

		# get order of drug mentions
		tokens = tokenize(body,drug=None,pos_filter=False,lemma=False)
		ordered_drugs = []
		for word in tokens:
			if word in drugs:
				ordered_drugs.append(word)
		ordered_drugs = OrderedSet(ordered_drugs)

		for i,drug in enumerate(ordered_drugs):
			query = ("UPDATE Chunks SET precedence=%i WHERE (id='%s' "
				"AND drug='%s')" % (i+1,post_id,drug))
			cur.execute(query)

	conn.commit()
	conn.close()