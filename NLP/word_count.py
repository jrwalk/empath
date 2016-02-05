"""word-count statistics for drug mentions.
"""
import pymysql as pms
import pickle
import nltk
from nltk.probability import FreqDist
from nltk.stem import WordNetLemmatizer
import drug_mentions as dm
import stop_words as sw

import build_drug_dict as bdd
_drug_dict = bdd.build_drug_dict(
	'/home/jrwalk/python/empath/data/drugs/antidepressants.txt')
_gen_dict = bdd.generic_dict(_drug_dict)


_lemmatizer = WordNetLemmatizer()


def word_count(drug=None,limit=None,pos_filter=False,lemma=True):
	"""Scans comment texts (from drug_mentions.texts) for selected drug, 
	calculates most common words.

	KWARGS:
		drug: string or None.
			Drug selector.  Allows three cases:
			* None: scrape all comments in database, regardless of drug.
			* 'antidepressant': select comments speaking generically about
				drug, not referencing specific drug.
			* [drug name]: comments referencing specific drug.
			Default None.  Passed to drug_mentions.texts.
		limit: int or None.
			Optional limit on SQL queries retrieved by drug_mentions.texts. 
			Defaults to None (returns all hits).
		pos_filter: boolean.
			Passed to tokenize(), set True to use part-of-speech filtering.
		lemma: boolean.
			Passed to tokenize(), set True to use lemmatization.

	RETURNS:
		freq: nltk.probability.FreqDist object.
			Frequency distribution of words from comments.

	RAISES:
		ValueError:
			for invalid drug name.
	"""
	try:
		texts = dm.texts(drug=drug,limit=limit)
	except ValueError:
		raise ValueError('Invalid drug name.')

	freq = FreqDist()
	for text in texts:
		freq.update(tokenize(text,drug,pos_filter=pos_filter,lemma=lemma))

	return freq


def tokenize(text,drug=None,pos_filter=False,lemma=True):
	"""Simple (or not) tokenizer for given text block.

	ARGS:
		text: string.
			Single comment block.

	KWARGS:
		drug: string or None.
			drug name (added to stoplist to prevent self-mentions)
		pos_filter: boolean.
			set True to use part-of-speech filtering.
		lemma: boolean.
			set True to use lemmatization.

	RETURNS:
		words: list.
			List of lower-case word tokens (individual strings)
	"""
	tokens = nltk.RegexpTokenizer(r'\w+').tokenize(text.lower())
	merger = nltk.MWETokenizer([('side','effect'),('side','effects')])
	tokens = merger.tokenize(tokens)
	
	# filter on stop words
	stops = sw.stop_words()
	if drug is not None:
		if drug.upper() != 'ANTIDEPRESSANT':
			stops.append(drug.lower())
			if _drug_dict[drug.upper()] != drug.upper():
				stops.append(_drug_dict[drug.upper()].lower())
			if drug.upper() in _gen_dict.keys():
				for bd in _gen_dict[drug.upper()]:
					stops.append(bd.lower())
		else:
			stops = stops+['antidepressant','antidepressants']
	stops = set(stops)
	tokens = [word for word in tokens if word not in stops]

	if pos_filter:
		tagged_tokens = nltk.pos_tag(tokens)
		tags = ['CD',
			'DT',
			'JJ',
			'JJR',
			'JJS',
			'NN',
			'NNP',
			'NNPS',
			'NNS',
			'RB',
			'RBR',
			'RBS',
			'VB',
			'VBD',
			'VBG',
			'VBN',
			'VBP',
			'VBZ']
		tokens = [word for (word,tag) in tagged_tokens if tag in tags]

	if lemma:
		tokens = [_lemmatizer.lemmatize(word,pos='v') for word in tokens]
		tokens = [_lemmatizer.lemmatize(word,pos='n') for word in tokens]

	# one more pass through stopword filter
	tokens = [word for word in tokens if word not in stops]

	return tokens


def word_counts(limit=None,pos_filter=False,lemma=True):
	"""Loops through available (generic) drugs, constructs frequency 
	distribution for each, along with hit count in database.  Saves count 
	pull limit, and nltk.probability.FreqDist object to pickle file.

	KWARGS:
		limit: int or None.
			Cap limit on SQL pulls, passed to word_count.
		pos_filter: boolean.
			set True to use part-of-speech filtering in tokenizer.
		lemma: boolean.
			set True to use lemmatization in tokenizer.

	RAISES:
		ValueError:
			if raised by word_count (invalid drug name).
	"""
	conn = pms.connect(
		host='localhost',
		user='root',
		passwd='',
		db='empath',
		charset='utf8',
		init_command='SET NAMES UTF8')
	cur = conn.cursor()

	for drug in _gen_dict.keys()+[None,'ANTIDEPRESSANT']:
		try:
			freq = word_count(drug=drug,
				limit=limit,
				pos_filter=pos_filter,
				lemma=lemma)
		except ValueError:
			raise ValueError('Invalid drug name.')

		if drug is None:
			query = ("SELECT `id` from Mentions")
		elif drug == 'ANTIDEPRESSANT':
			query = ("SELECT `id` from Mentions "
				"WHERE count=0")
		else:
			query = ("SELECT `id` FROM Mentions "
				"WHERE %s=True" % drug.lower())
		count = cur.execute(query)

		data = (count,limit,freq)

		if drug is None:
			filepath = ("/home/jrwalk/python/empath/data/reddit/pickles/"
				"wordcount_all_%s.pkl" % limit)
		else:
			filepath = ("/home/jrwalk/python/empath/data/reddit/pickles/"
				"wordcount_%s_%s.pkl" % (drug.lower(),limit))
		with open(filepath,'w') as writefile:
			pickle.dump(data,writefile)

	conn.close()