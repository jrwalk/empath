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
import pymysql as pms
import numpy as np
from stop_words import stop_words
import pandas
from word_count import tokenize
import sys
from ordered_set import OrderedSet

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
		writefile.write(text.encode('utf8'))

	with open('corenlp.log','w') as logfile:
		subprocess.call("/home/jrwalk/corenlp/corenlp.sh -annotators "
			"tokenize,ssplit,parse,pos,sentiment "
			"-file input.txt -outputFormat xml",
			shell=True,stdout=logfile)

	xmlstring = ''
	with open('input.txt.xml','r') as readfile:
		for line in readfile:
			xmlstring += line

	os.remove('input.txt')
	os.remove('input.txt.xml')
	os.remove('corenlp.log')

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
			list of drugs mentioned in comment (all sentences).

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
	for tree in trees:
		# list which drugs are in sentence tree
		mentions.append([d for d in drugs if d in tree.leaves()])
		subtrees = parse_tree(tree,drugs)
		for sub in subtrees:
			subtext = sub.leaves()
			# which drug is in subtree: should be one or zero drugs
			drug = [d for d in drugs if d in subtext]
			if len(drug) > 0:	# there is a drug mention in the subtext
				drug = drug[0]
				lastdrug = drug
			else:
				drug = lastdrug
			precedence.append(drug)
			if drug not in texts.keys():
				texts[drug] = [subtext]
				#if lastdrug != 'preamble':
				#	precedence += 1
			else:
				texts[drug].append(subtext)
	return (texts,mentions,precedence)


def train_classifier():
	"""Constructs nltk Naive Bayes classifier using labeled medical comments 
	(from Nicole Strang's dataset).

	RETURNS:
		nbc: nltk.classify.NaiveBayesClassifier object.
			Naive Bayes classifier trained on Nicole Strang's labeled patient 
			comments from previous Insight project.  Similar usage (comments 
			on drug side effects) but disjoint from antidepressant data.
	"""
	df = pandas.read_csv(
		'/home/jrwalk/python/empath/data/training/Comments.txt',index_col=0)
	df['Comments'].replace('',np.nan,inplace=True)
	df.dropna(subset=['Comments'],inplace=True)
	df = df.drop_duplicates(subset=['Drug','Comments'])
	df = df[df.Rating != 3]
	df['Value'] = ['pos' if x>3 else 'neg' for x in df['Rating']]

	# so now we have a DataFrame of the training data, including user rating, 
	# side effects, comments, and patient metadata.  Realistically we only need 
	# the rating and comments.
	pos_texts = df['Comments'][df['Value'] == 'pos'].tolist()
	neg_texts = df['Comments'][df['Value'] == 'neg'].tolist()

	pos_data = [(dict([(word,True) for word in tokenize(com,None,False)]),'pos') 
		for com in pos_texts]
	neg_data = [(dict([(word,True) for word in tokenize(com,None,False)]),'neg') 
		for com in neg_texts]
	trainingdata = pos_data + neg_data

	classifier = nltk.classify.NaiveBayesClassifier.train(trainingdata)
	return classifier


def build_chunks(drug,classifier,limit=None):
	"""Pulls comment data from SQL table, constructs trees for each, chunks by 
	drug mention, writes to Chunks SQL table organized by drug.

	ARGS:
		drug: string.
			drug name.
		classifier: nltk.classify.NaiveBayesClassifier object.
			trained Naive Bayes classifier.

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
	query += "JOIN Mentions m on c.id=m.id WHERE (m.count=1 OR m.count=2) "
	query += ("AND m.%s=True AND c.chunked=False" % drug.lower())
	if limit is not None:
		query += (" LIMIT %s" % limit)
	cur.execute(query)
	conn.close()

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
			for remap in _gen_dict.get(drug.upper(),[drug.upper()]):
				body = body.replace(remap.lower(),drug.lower())

		trees,sentiments = build_tree(body,drugs)
		subtexts,mentions,precedence = map_subtrees(trees,drugs)

		for i,drug in enumerate(OrderedSet(precedence)):
			drugtext = []
			for subtext in subtexts[drug]:
				for word in subtext:
					drugtext.append(word)
			drugtext = [word for word in drugtext 
				if word not in set(stop_words())]
			sents = []
			for j,men in enumerate(mentions):
				if len(men) == 0:
					men = ['preamble']
				if drug in men:
					sents.append(sentiments[j])

			nbsent = classifier.prob_classify(dict([(word,True) for word in 
				drugtext])).prob('pos')	# probability positive

			data = (post_id,i,drug,drugtext,sents,nbsent)
			yield data


def write_chunks(drug,classifier,limit=None):
	"""gets generator of chunked data from build_chunks, writes to SQL Chunks 
	db, updates Comments with chunked flag.  Args, Kwargs passed to 
	build_chunks.

	ARGS:
		drug: string.
			drug name.
		classifier: nltk.classify.NaiveBayesClassifier object.
			trained Naive Bayes classifier.

	KWARGS:
		limit: int or None.
			optional cap on number of comments streamed through processor.

	RETURNS:
		counter: int.
			count of updated rows.

	RAISES:
		ValueError:
			if invalid drug is input.
	"""
	try:
		chunks = build_chunks(drug,classifier,limit=limit)
	except ValueError:
		raise ValueError("invalid drug name.")

	conn = pms.connect(host='localhost',
		user='root',
		passwd='',
		db='empath',
		charset='utf8',
		init_command='SET NAMES UTF8')
	cur = conn.cursor()

	counter = 0
	for chunk in chunks:
		counter += 1
		post_id = chunk[0]
		i = chunk[1]
		drug = chunk[2]
		drug_text = chunk[3]
		sents = chunk[4]
		nbsent = chunk[5]

		print post_id

		drug_text_text = ""
		for dt in drug_text:
			drug_text_text += dt+' '
		sents_text = ""
		for s in sents:
			sents_text += s+' '

		try:
			cur.execute("INSERT INTO Chunks "
				"(id,"
				"drug,"
				"precedence,"
				"drug_text,"
				"sents,"
				"nbsent) " 
				"VALUES (%s,%s,%s,%s,%s,%s)",
				(post_id,
					drug,
					i,
					drug_text_text,
					sents_text,
					nbsent)
				)
			cur.execute(
				"UPDATE Comments SET chunked=True WHERE id=%s",(post_id))
		except:
			print("could not insert to table")

	conn.commit()
	conn.close()
	return counter

		
def write_drugs(limit=None):
	"""loop through drugs, try to find new chunks and process.

	KWARGS:
		limit: int or None.
			cap on any single-drug comment pull.
	"""
	classifier = train_classifier()
	drugs = [d.lower() for d in _generics]
	for i,d in enumerate(drugs):
		count = write_chunks(d,classifier,limit=limit)
		print("%i/%i Processed %i chunks for %s" % (i+1,len(drugs),count,d))