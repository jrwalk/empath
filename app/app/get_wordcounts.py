"""getter method to restore data from pickled wordcount data, plus 
visualizer.
"""
import glob
import pickle
import re
import pandas
import wordcloud
import matplotlib.pyplot as plt
plt.ioff()


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
	tfidf_scores.sort(columns='score',ascending=False,inplace=True)
	return (count,limit,freq,tfidf_scores)


def visualizer(tfidf_scores,drugname):
	"""Produces visualization of wordcount data, using output from getter().

	ARGS:
		tfidf_scores: pandas.DataFrame.
			DataFrame of words, tf-idf scores from getter() method.
		drugname: string.
			String generated in views.py for display.
	"""
	scores_lim = tfidf_scores.head(20)	# cap at top 20 words
	scores_list = [tuple(row) for row in scores_lim.values]
	cloud = wordcloud.WordCloud()
	cloud.fit_words(scores_list)
	cloud.to_image().save('app/static/images/wordcloud_%s.png' % drugname)
