from flask import render_template, request
from app import app
import json
import numpy as np

import sys
sys.path.append('/home/jrwalk/python/empath/')
sys.path.append('/home/jrwalk/python/empath/data/')
sys.path.append('/home/jrwalk/python/empath/drug_data/')
sys.path.append('/home/jrwalk/python/empath/NLP/')
sys.path.append('/home/jrwalk/python/empath/scraper/')
sys.path.append('/home/jrwalk/python/empath/app/app/')

import build_drug_dict as bdd
_drug_dict = bdd.build_drug_dict(
	'/home/jrwalk/python/empath/data/drugs/antidepressants.txt')
_generics = bdd.generics(_drug_dict)

from chunker import train_classifier
cl = train_classifier()

import get_wordcounts as gw
import top_comments as tc
import sentiments as s

@app.route('/index')
@app.route('/')
def input():
	return render_template('input.html')

@app.route('/output')
def output():
	# pull drug name from request field, check for match
	drug = request.args.get('ID')
	drug = drug.split()[0]	# 
	gen = _drug_dict.get(drug.upper(),None)
	if gen is not None:	# drug is in dict
		if drug.lower() == gen.lower():	# input is generic
			drugname = drug.lower()
		else:
			drugname = "%s (%s)" % (drug.lower(),gen.lower())
	else:	# drug not in dict
		drugs = []
		with open('/home/jrwalk/python/empath/data/drugs/antidepressants.txt','r') as readfile:
			for line in readfile:
				drugs.append(line.strip())
		return render_template('error.html',drugs=drugs)

	fd,scores,words = get_word_scores(drug)
	rip_to_json(fd,scores,40)

	nn_sent = s.corenlp_sentiment(gen.lower())
	nn_sent_all = s.corenlp_sentiment(None)
	nba_sent = s.nba_sentiment(gen.lower())
	nba_sent_all = s.nba_sentiment(None)

	comments = tc.top_comments(drug.lower())
	comments = [c for c in comments]	# list of tuples, rather than generator

	strs = parse_sentiment(nn_sent,nn_sent_all)

	return render_template('output.html',
		drugname=drugname,
		words=words,
		comments=comments,
		nn_sent=(nn_sent,nn_sent_all),
		nba_sent=(nba_sent,nba_sent_all),
		strs=strs)


def parse_sentiment(nn_sent,nn_sent_all):
	"""constructs strings of positivity/negativity ratings compared to average 
	from neural-net based analyzer.

	ARGS:
		nn_sent: tuple.
			tuple of (collections.Counter,total) of sentiment scores for drug.
		nn_sent_all: tuple.
			Similarly structured tuple, of all drug posts.
	"""
	pos_count = nn_sent[0]['Positive'] + nn_sent[0]['Verypositive']
	pos_count_all = nn_sent_all[0]['Positive'] + nn_sent_all[0]['Verypositive']
	pos_percent = float(pos_count)/nn_sent[1]
	pos_percent_all = float(pos_count_all)/nn_sent_all[1]

	neg_count = nn_sent[0]['Negative'] + nn_sent[0]['Verynegative']
	neg_count_all = nn_sent_all[0]['Negative'] + nn_sent_all[0]['Verynegative']
	neg_percent = float(neg_count)/nn_sent[1]
	neg_percent_all = float(neg_count_all)/nn_sent_all[1]

	pos_scale = np.abs(1. - pos_percent/pos_percent_all) * 100.
	pos_scale = ("%.2f" % pos_scale)
	neg_scale = np.abs(1. - neg_percent/neg_percent_all) * 100.
	neg_scale = ("%.2f" % neg_scale)
	if pos_percent > pos_percent_all:
		pos_str = "more positive"
	else:
		pos_str = "less positive"

	if neg_percent > neg_percent_all:
		neg_str = "more negative"
	else:
		neg_str = "less negative"

	pos = (pos_scale,pos_str)
	neg = (neg_scale,neg_str)
	return (pos,neg)
	


def rip_to_json(freqdist,scores,limit=20):
	"""takes top TF-IDF scoring words, generates JSON categorized by 
	positive/negative/neutral word scoring from Naive Bayes classifier, 
	to be read by d3 utilization in output.html to display word-count bubble.

	ARGS:
		freqdist: nltk.probability.FreqDist object.
			contains word frequencies.
		scores: pandas.DataFrame object.
			contains TF-IDF scores of words in freqdist.

	KWARGS:
		limit: int.
			cap on how many words to parse into bubbler.
	"""
	# initialize structure
	data = {'name':'wordscores',
		'children':[
			{'name':'positive',
			'children':[]},
			{'name':'neutral',
			'children':[]},
			{'name':'negative',
			'children':[]}
		]}

	scores = scores.head(limit)
	for row in scores.iterrows():
		word = row[1].word
		score = row[1].score
		freq = float(freqdist[word])/freqdist.N()
		count = freqdist[word]

		pscore = cl.prob_classify({word:True}).prob('pos')
		if pscore>=0.6:
			data['children'][0]['children'].append({'name':word,
				'size':count,
				'score':score,
				'freq':freq,
				'pscore':pscore})
		elif pscore>=0.4 and pscore<0.6:
			data['children'][1]['children'].append({'name':word,
				'size':count,
				'score':score,
				'freq':freq,
				'pscore':pscore})
		else:
			data['children'][2]['children'].append({'name':word,
				'size':count,
				'score':score,
				'freq':freq,
				'pscore':pscore})

	with open('app/static/data/scores.json','w') as writefile:
		json.dump(data,writefile)


def get_word_scores(drug,limit=20):
	"""processes output of get_wordcounts.getter().

	ARGS:
		drug: string.
			name of drug.

	KWARGS:
		limit: int.
			cap on number of words to return.

	RETURNS:
		fd: nltk.probability.FreqDist object.
			Frequency distribution for words in corpus.
		scores: pandas.DataFrame object.
			sorted DataFrame of TF-IDF scores by word
		words: tuple.
			tuple of:
				count: int.
					total number of posts processed.
				total_words: int.
					total number of words in posts.
				unique_words: int.
					number of unique words in posts.
				top_words: list.
					list of (word,wordcount,TF-IDF score) for top `limit` words.
	"""
	words = gw.getter(_drug_dict[drug.upper()].lower())
	count = words[0]
	#posts = words[1]	# scrape limit
	fd = words[2]		# nltk.probability.FreqDist
	scores = words[3]	# pandas.DataFrame

	total_words = fd.N()
	unique_words = fd.B()
	top_words = []
	for row in scores.head(limit).iterrows():
		word = row[1].word
		score = row[1].score
		wordcount = fd[word]
		top_words.append((word,wordcount,score))

	words = (count,total_words,unique_words,top_words)
	return (fd,scores,words)