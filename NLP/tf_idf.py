"""Calculators for TF-IDF score for word list, taken from pre-calculated 
frequency distribution from word_count.
"""
import nltk
from nltk.text import TextCollection
import pickle
import glob
import re


def tf_idf(freqdist,corpus):
	"""Calculates TF-IDF score for series of words, using distribution in 
	freqdist for the TF score and the IDF score for each of those words from 
	the corpus.

	ARGS:
		freqdist: nltk.probability.FreqDist object.
			contains frequency statistics for wordset.
		corpus: nltk.text.TextCollection object.
			TextCollection object (a series of nltk.text.Text objects) on which 
			the IDF score for a word may be computed for an independent corpus.

	RETURNS:
		wordscores: dict.
			dict of TF-IDF scores for each word in freqdist.
	"""
	wordscores = {}
	N = freqdist.N()
	for word in freqdist.viewkeys():
		tf = float(freqdist[word])/N
		idf = corpus.idf(word)
		wordscores[word] = tf*idf
	return wordscores


def calc_tf_idfs(count):
	"""loops through archived wordlists, loads each, calculates TF-IDF score 
	for words contained, writes to dict and saves in pickle.
	"""
	corpus = TextCollection(nltk.corpus.webtext)

	filepath = '/home/jrwalk/python/empath/data/reddit/pickles/'
	files = glob.glob(filepath+'wordcount*%s.pkl' % count)
	filecount = len(files)
	for i,picklefile in enumerate(files):
		print "%i/%i processing %s" % (i+1,filecount,picklefile)
		with open(picklefile,'r') as readfile:
			freqdist = pickle.load(readfile)[2]
		wordscores = tf_idf(freqdist,corpus)
		druglim = re.findall('[a-z]+_[0-9]+|all|antidepressant',picklefile)[0]
		writepath = filepath+'tfidf_'+druglim+'.pkl'
		with open(writepath,'w') as writefile:
			pickle.dump(wordscores,writefile)