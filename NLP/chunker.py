"""Code to chunk text around drug mention, either retaining whole sentences 
with single (or no) drug mentions, or parsing the sentence into maximum-size 
subphrases with single (or no) mentions.  The latter is accomplished by parsing 
the sentence into a tree, and recursively seeking maximum-size subtrees with 
one or zero drug mentions.
"""
import nltk
from corenlp_xml.document import Document
import os
import subprocess
import itertools
import pymysql as pms
import numpy as np
from stop_words import stop_words

import build_drug_dict as bdd
_drug_dict = bdd.build_drug_dict(
	'/home/jrwalk/python/empath/data/drugs/antidepressants.txt')
_generics = bdd.generics(_drug_dict)
_gen_dict = bdd.generic_dict(_drug_dict)


def parse_tree(tree,drugs):
	"""Chunks tree into maximum-size subtrees with one or zero drug mentions.

	ARGS:
		tree: nltk.tree.Tree object.
			parsed tree of sentence structure.
		drugs: list.
			list of strings of drug names to search for.

	RETURNS:
		subtrees: list.
			list of nltk.tree.Tree objects, containing max-length subtrees 
			with one or zero drug mentions.
	"""
	def splitter(tree,drugs):
		"""inner method for recursion.
		"""
		contains = [drug in tree.leaves() for drug in drugs]
		if sum(contains) == 0 or sum(contains) == 1:
			return [tree]
		else:
			trees = []
			while True:
				try:
					subtree = tree.pop(0)
					trees.append(splitter(subtree,drugs))
				except:
					break
			return trees

	def flatten(trees):
		"""inner method to recursively flatten list of subtrees returned by 
		splitter().
    	"""
		for i in trees:
			if not isinstance(i, nltk.tree.Tree):
				for j in flatten(i):
					yield j
			else:
				yield i

	return [subtree for subtree in flatten(splitter(tree,drugs))]


def build_tree(text,drugs):
	"""passes text to tree constructor for use by parse_tree().  Should only 
	be used in cases of sentences containing multiple drug references.

	ARGS:
		text: string.
			text body from comment
		drugs: list.
			list of strings, containing mentioned drugs.

	RETURNS:
		trees: list.
			list of nltk.tree.Tree objects, one for each sentence.
		sentiments: list.
			list of strings, containing the sentiment rating from coreNLP for 
			each sentence.
	"""
	with open('input.txt','w') as writefile:
		writefile.write(text)

	subprocess.call("/home/jrwalk/corenlp/corenlp.sh -annotators "
		"tokenize,ssplit,parse,pos,sentiment "
		"-file input.txt -outputFormat xml",
		shell=True)

	xmlstring = ''
	with open('input.txt.xml','r') as readfile:
		for line in readfile:
			xmlstring += line

	os.remove('input.txt')
	os.remove('input.txt.xml')

	doc = Document(xmlstring)
	sentences = doc.sentences
	trees = []
	sentiments = []
	for sent in sentences:
		sentiments.append(sent.sentiment)
		tree = nltk.tree.Tree.fromstring(sent.parse_string)
		trees.append(tree)

	return (trees,sentiments)


def map_subtrees(trees,drugs):
	"""maps subtrees into mentioned drug, and drug-note order.

	ARGS:
		trees: list.
			list of nltk.tree.Tree objects corresponding to each sentence.
		drugs: list.
			list of drugs mentioned in comment.

	RETURNS:
		texts: dict.
			dict of {drug:[texts]} storing list of lists of tokens 
			from individual subtrees, keyed by the mentioned drug (or 
			'preamble' if it precedes a drug mention).
		mentions: list.
			list of drugs mentioned in each sentence, to be paired with 
			sentiments list from coreNLP.
		precedence: list.
			list of drugs mentioned in each subtree, for use in ranking order.
	"""
	texts = {}
	mentions = []
	precedence = []
	lastdrug = 'preamble'
	for i,tree in enumerate(trees):
		precedence = 0
		sent = sentiments[i]
		mentions.append([d for d in drugs if d in tree.leaves])
		subtrees = parse_tree(tree,drugs)
		for sub in subtrees:
			subtext = sub.leaves()
			drug = [d for d in drugs if d in subtext]
			precedence.append(drug)
			if len(drug) > 0:
				drug = drug[0]
				lastdrug = drug
			else:
				drug = lastdrug
			if drug not in texts.keys():
				texts[drug] = [subtext]
				if lastdrug != 'preamble':
					precedence += 1
			else:
				texts[drug].append(subtext)
	return (texts,mentions,precedence)


def build_chunks(drug,limit=None):
	"""Pulls comment data from SQL table, constructs trees for each, chunks by 
	drug mention, writes to Chunks SQL table organized by drug.

	ARGS:
		drug: string.
			drug name.

	KWARGS:
		limit: int or None.
			optional cap on number of comments streamed through processor.

	RAISES:
		ValueError:
			if invalid drug is input.
	"""
	try:
		drug = _drug_dict[drug.upper()]
	except:
		raise ValueError("invalid drug")

	def uniconvert(s):
		if s == '\x00':
			return 0
		elif s == '\x01':
			return 1
		else:
			return None

	conn = pms.connect(host='localhost',
		user='root',
		passwd='',
		db='empath',
		charset='utf8',
		init_command='SET NAMES UTF8')
	cur = conn.cursor()

	# assemble the mother of all queries
	query = "SELECT c.id,c.body,m.count"
	for gen in _generics:
		query += (",m.%s" % gen.lower())
	query += " FROM Comments c JOIN Subreddits s on c.subreddit=s.subreddit "
	query += "JOIN Mentions m on c.id=m.id WHERE m.count=1 OR m.count=2 "
	query += ("AND m.%s=True" % drug.lower())
	if limit is not None:
		query += (" LIMIT %s" % limit)
	cur.execute(query)

	for row in cur:
		post_id = row[0]
		body = row[1]
		count = row[2]
		drugs = np.array([uniconvert(d) for d in row[3:]])
		dmap = np.where(drugs == 1)
		drugs = [d.lower() for d in list(np.array(_generics)[dmap])]

		# clean body text
		body = body.lower()
		for drug in drugs:
			for remap in _gen_dict[drug.upper()]:
				body = body.replace(remap.lower(),drug.lower())

		trees,sentiments = build_tree(body,drugs)
		subtexts,mentions,precedence = map_subtrees(trees,drugs)

		for drug in set(precedence):
			drugtext = []
			for subtext in subtexts[drug]:
				for word in subtext:
					drugtext.append(word)
			drugtext = [word for word in drugtext 
				if word not in set(stop_words())]
			sents = []
			for i,men in enumerate(mentions):
				if len(men) == 0:
					men = ['preamble']
				if drug in men:
					sents.append(sentiments[i])

			







	conn.close()