from flask import render_template, request
from app import app

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

import get_wordcounts as gw
import top_comments as tc
import sentiments as s

@app.route('/index')
def index():
	return 'placeholder'

@app.route('/')
def input():
	return render_template('input.html')

@app.route('/output')
def output():
	# pull drug name from request field, check for match
	drug = request.args.get('ID')
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

	words = gw.getter(_drug_dict[drug.upper()].lower())
	count = words[0]
	#posts = words[1]	# scrape limit
	fd = words[2]		# nltk.probability.FreqDist
	scores = words[3]	# pandas.DataFrame

	total_words = fd.N()
	unique_words = fd.B()
	scores = scores[:20]
	gw.visualizer(scores,drugname)
	top_words = []
	for row in scores.iterrows():
		word = row[1].word
		score = row[1].score
		count = fd[word]
		top_words.append((word,count,score))

	words = (count,total_words,unique_words,top_words)

	nn_sent = s.corenlp_sentiment(gen.lower())
	nba_sent = s.nba_sentiment(gen.lower())

	comments = tc.top_comments(drug.lower())
	comments = [c for c in comments]	# list of tuples, rather than generator

	return render_template('output.html',
		drugname=drugname,
		words=words,
		comments=comments,
		nn_sent=nn_sent,
		nba_sent=nba_sent)