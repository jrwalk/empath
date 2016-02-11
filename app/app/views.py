import flask
from flask import render_template, request, jsonify
from app import app
import numpy as np
import pickle
import json

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
_gen_dict = bdd.generic_dict(_drug_dict)

#from chunker import train_classifier
#cl = train_classifier()
with open('/home/jrwalk/python/empath/data/training/classifier.pkl','r') as r:
	cl = pickle.load(r)

import get_wordcounts as gw
import top_comments as tc
import sentiments as s
import recommender as r

@app.route('/index')
@app.route('/')
def input():
	return render_template('input.html')

@app.route('/output')
def output():
	# pull drug name from request field, check for match
	drug = request.args.get('ID')
	drug = drug.split()[0]	# quick and dirty input sanitization

	try:
		drugname,gen = drugnames(drug)
	except ValueError:
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

	recommendation = process_recommendation(gen.lower())

	return render_template('output.html',
		drugname=drugname,
		gen=gen.lower(),
		words=words,
		comments=comments,
		nn_sent=(nn_sent,nn_sent_all),
		nba_sent=(nba_sent,nba_sent_all),
		strs=strs,
		recommendation=recommendation)


@app.route('/contact')
def contact():
	"""renderer for contact page.
	"""
	return render_template('contact.html')


@app.route('/about')
def about():
	"""renderer for about page.
	"""
	return render_template('about.html')


@app.route('/data')
def get_data():
	with open('app/static/data/scores.json','r') as r:
		json_data = flask.json.load(r)
	return jsonify(json_data)


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
	pos_scale = ("%.1f" % pos_scale)
	neg_scale = np.abs(1. - neg_percent/neg_percent_all) * 100.
	neg_scale = ("%.1f" % neg_scale)
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
	data = {"name":"wordscores",
		"children":[
			{"name":"positive",
			"children":[]},
			{"name":"neutral",
			"children":[]},
			{"name":"negative",
			"children":[]}
		]}

	scores = scores.head(limit)
	for row in scores.iterrows():
		word = row[1].word
		score = row[1].score
		freq = float(freqdist[word])/freqdist.N()
		count = freqdist[word]

		pscore = cl.prob_classify({word:True}).prob("pos")
		if pscore>=0.6:
			data["children"][0]["children"].append({"name":word,
				"size":count,
				"score":score,
				"freq":freq,
				"pscore":pscore})
		elif pscore>=0.4 and pscore<0.6:
			data["children"][1]["children"].append({"name":word,
				"size":count,
				"score":score,
				"freq":freq,
				"pscore":pscore})
		else:
			data["children"][2]["children"].append({"name":word,
				"size":count,
				"score":score,
				"freq":freq,
				"pscore":pscore})

	with open("app/static/data/scores.json","w") as writefile:
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


def process_recommendation(drug):
	"""Pulls drug recommendation stats from recommender.py, formats.

	ARGS:
		drug: string.
			generic name of drug.

	RETURNS:
		data: tuple.
			tuple of (stayed_frac,better_frac,best_frac,drugname)
	"""
	stayed_on_drug,switched_drug,switched_drug_better,best_drug = r.recommend(drug)

	total = stayed_on_drug + switched_drug
	stayed_frac = float(stayed_on_drug)/total
	better_frac = float(switched_drug_better)/switched_drug
	best_frac = float(best_drug[1])/switched_drug_better
	bdrug = best_drug[0]

	drugname,gen = drugnames(bdrug)

	data = (stayed_frac,better_frac,best_frac,drugname)
	return data


def drugnames(drug):
	"""string handler to produce formatted drug name.

	ARGS:
		drug: string.
			input drug name.

	RETURNS:
		formatted_drug: string.
			formatted string of drug name of the form 
			'generic name (brand names)'.
		gen: string.
			forced generic drug name.

	RAISES: 
		ValueError:
			raised if drug is not in database.
	"""
	# first check that drug is in database
	gen = _drug_dict.get(drug.upper(),None)
	if gen is None:
		raise ValueError("invalid drug.")

	formatted_drug = gen.lower()+" ("	# start off with generic name
	brand_names = _gen_dict[gen.upper()]
	for brand in brand_names:
		formatted_drug += brand.lower()+', '
	formatted_drug = formatted_drug[:-2]+')'
	return formatted_drug,gen