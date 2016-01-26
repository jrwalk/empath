"""wrapper around nltk.corpus.stopwords, expanding on relevant stopwords.
"""
from nltk.corpus import stopwords

def stop_words():
	"""returns expanded list of stopwords.

	RETURNS:
		stops: list.
			expanded list of stopwords, built around nltk.corpus.stopwords.
	"""
	stops = stopwords.words('english')
	expansion = ['com',
		'http',
		'https',
		'm',
		've',
		'also',
		'much',
		'really',
		'take',
		'one',
		'people',
		'get',
		'u',
		'r',
		're',
		'things',
		'drug','drugs',
		'depression',
		'antidepressant','antidepressants',
		'anti',
		'depressed','depression',
		'though',
		'meds','medication',
		'doctor','psychiatrist',
		'weeks',
		'amp','gt','lt',
		'tried']
	stops = stops+expansion
	return stops