"""getter method to restore data from pickled wordcount data, plus 
visualizer.
"""
import glob
import pickle
import re
import pandas


def getter(drug):
	"""gets pickled data for drug.

	KWARGS:
		drug: string or None.
			Drug selector.  Allows three cases:
			* None: scrape all comments in database, regardless of drug.
			* 'antidepressant': select comments speaking generically about
				drug, not referencing specific drug.
			* [drug name]: comments referencing specific drug.
			Default None.  Passed to drug_mentions.texts.

	RETURNS:
		count: int.
			number of processed posts in word counter object.
		limit: int or None.
			cap on scraper from word_count.word_counts.
		freq: nltk.probability.FreqDist object.
			frequency distribution of words.
		scores: pandas.DataFrame object.
			DataFrame of TF-IDF scores for words, pre-sorted.
	"""
	drug = drug.lower()
	files = glob.glob(
		'/home/jrwalk/python/empath/data/reddit/pickles/wordcount_%s_*' 
		% drug)

	bestfile = ''
	bestcount = 0
	for file in files:
		num = int(re.findall('[0-9]+',file)[0])
		if num > bestcount:
			bestfile = file
			bestcount = num

	with open(bestfile,'r') as readfile:
		(count,limit,freq) = pickle.load(readfile)

	tfidffile = ("/home/jrwalk/python/empath/data/reddit/pickles/"
		"tfidf_%s_%s.pkl" % (drug,bestcount))	# will match wordcount file
	with open(tfidffile,'r') as readfile:
		tfidf_scores = pickle.load(readfile)

	tfidf_scores = pandas.DataFrame(tfidf_scores.items(),
		columns=['word','score'])
	tfidf_scores.sort_values(by='score',ascending=False,inplace=True)
	return (count,limit,freq,tfidf_scores)