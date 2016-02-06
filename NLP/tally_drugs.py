"""read through SQL database, count total drug mentions in comments (accounting 
for remaps between generic and brand names), report count total into SQL table.
"""
import pymysql as pms
import build_drug_dict as bdd
import numpy as np
from word_count import tokenize

_drug_dict = bdd.build_drug_dict(
	'/home/jrwalk/python/empath/data/drugs/antidepressants.txt')
_generics = bdd.generics(_drug_dict)

def tally():
	"""reads through empath.Comments db, detects which drugs are mentioned 
	in each comment body.  Populates empath.Mentions db with count, which 
	drugs are mentioned.
	"""
	conn = pms.connect(host='localhost',
		user='root',
		passwd='',
		db='empath',
		charset='utf8',
		init_command='SET NAMES UTF8')
	cur = conn.cursor()
	cur.execute('select id,body from Comments')

	posts = []
	for row in cur:
		posts.append((row[0],row[1].upper()))

	for row in posts:
		post_id = row[0]
		body = row[1].upper()

		# remap to generic drug names
		for drug in _drug_dict:
			body = body.replace(drug,_drug_dict[drug])

		tokens = tokenize(body,None,False,False)

		# generate row in `empath`.`Mentions` for post
		# loop through generics, detect presence, update Mentions as needed
		try:
			cur.execute('INSERT INTO `Mentions` (`id`) VALUES (%s)',(post_id))
			conn.commit()
		except:
			pass
		counter = 0
		for drug in _generics:
			if drug.lower() in tokens:
				counter += 1
				flagger = ("UPDATE `Mentions` SET `%s`=True WHERE `id`='%s'" 
					% (drug.lower(),post_id))
				cur.execute(flagger)
		cur.execute("UPDATE `Mentions` SET `count`=%s WHERE `id`='%s'"
			% (counter,post_id))

	conn.commit()
	conn.close()