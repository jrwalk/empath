"""Wrapper for LDA analysis routines.
"""
import nltk
from nltk.stem.porter import PorterStemmer
from word_count import tokenize
from drug_mentions import texts
import gensim
import itertools

import build_drug_dict as bdd
_drug_dict = bdd.build_drug_dict(
	'/home/jrwalk/python/empath/data/drugs/antidepressants.txt')

stemmer = PorterStemmer()


def stream_tokens(drug=None,limit=None):
	"""Parses comment bodies from SQL database (pulled via word_count.texts) 
	into stream of stemmed, mapped tokens readable by gensim.

	KWARGS:
		drug: string or None.
			drug selector, passed to drug_mentions.texts.
		limit: int or None.
			optional limit on hits yielded from table.  Defaults to None (
			yield all results from table).

	YIELDS:
		text: list.
			each yielded tokens is a list of stemmed, mapped tokens.
	"""
	def streamer():
		for text in texts(drug=drug):
			text = tokenize(text,drug=drug,pos_filter=False)	# list of tokens
			for i,word in enumerate(text):	# remap brand drug names
				remap = _drug_dict.get(word.upper(),None)
				if remap is not None:
					text[i] = remap.lower()
			text = [stemmer.stem(word) for word in text]
			yield text

	return itertools.islice(streamer(),limit)


def build_corpus(drug=None,limit=None):
	"""Builds vectorized corpus using output from stream_tokens.

	KWARGS:
		drug: string or None.
			drug selector, passed to stream_tokens().
		limit: int or None.
			cap on hits returned, passed to stream_tokens().

	RETURNS:
		corpus: list.
			List of vectorized texts.  Each vectorized text is a list of 
			tuples containing the maps.
		dictionary: gensim.corpora.Dictionary.
			dictionary mapping vector indices, words.
	"""
	dictionary = gensim.corpora.Dictionary(stream_tokens(drug=drug,limit=limit))
	corpus =  [dictionary.doc2bow(text) for text 
		in stream_tokens(drug=drug,limit=limit)]
	return (corpus,dictionary)
