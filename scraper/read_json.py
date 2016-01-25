"""Reads monthly JSON dumps from reddit scraper, parses into individual JSON 
blocks, runs checker for target comments (comment text includes target words 
from drug list), saves text file with target comments also stored as JSON
"""
import json
import datetime as dt

# get drug list, store as module access
import build_drug_dict as bdd
_drug_dict = bdd.build_drug_dict(
	'/home/jrwalk/python/empath/data/drugs/antidepressants.txt')
_drug_list = bdd.flatten(_drug_dict)
_drug_list.append('ANTIDEPRESSANT')


def read(filepath,is_submission=False):
	"""reads text file at filepath, interprets each line as a JSON input, 
	parses into a single JSON object.  Then feeds to the comment 
	parser to check for target-comment validity.  Writes target comments into 
	scraped JSON file.

	ARGS:
		filepath: string.
			path to JSON text file of comment/submissions.

	KWARGS:
		is_submission: boolean.
			set True if file contains Submission posts, else assume file 
			contains Comment posts.  Alters which scrape-checker is triggered.
			Default False (Comment posts).
	"""
	# tick counters, logfile
	entries_read = 0
	entries_saved = 0
	logfile = open('/home/jrwalk/python/empath/data/reddit/read_json.log','a')
	logfile.write('reading file %s\n' % (filepath))
	logfile.write('read started %s\n' % (str(dt.datetime.now())))

	# open target JSON writefile
	writefile = open(filepath+'_scraped','w')

	with open(filepath,'r') as readfile:
		for line in readfile:
			data = json.loads(line)
			entries_read += 1
			if scrape_check(data,is_submission):
				entries_saved += 1
				write_json(data,writefile)
	logfile.write('read %i JSON objects, saved %i JSON objects\n' 
		% (entries_read, entries_saved))
	logfile.write('read finished %s\n' % (str(dt.datetime.now())))
	logfile.write('\n')

	# close writefile, logfile
	logfile.close()
	writefile.close()


def scrape_check(data,is_submission):
	"""checks comment body (+title, for posts) for keyword mentions.

	ARGS:
		data: dict.
			JSON-structured dict of data from reddit API.
		is_submission: boolean.
			True if JSON is Submission type, False for Comment type.

	RETURNS:
		trigger: boolean.
			return True if post contains keywords, else False.
	"""
	if not is_submission:	# process comment object
		text = data['body'].upper()
		for drug in _drug_list:
			if drug in text:
				return True
	else:					# process submission object
		if data['is_self']:
			text = data['selftext'].upper() + data['title'].upper()
			for drug in _drug_list:
				if drug in text:
					return True
	return False


def write_json(data,file):
	"""Write data from JSON dict into scraped Comments JSON file.

	ARGS:
		data: dict.
			JSON dict of comment data.
		file: file.
			writeable file object accepting scraped JSON dicts.
	"""
	json.dump(data,file)
	file.write('\n')
