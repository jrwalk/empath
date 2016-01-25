"""Read JSON dumps from reddit scraper into raw-data SQL tables.
"""
import json
import pymysql as pms

def read(filepath,is_submission=False):
	"""reads text file at filepath, interprets each line as as JSON input, 
	parses into a single JSON object.  Writes JSON into SQL table for Comments 
	or Submissions as determined by the is_submission flag.

	ARGS:
		filepath: string.
			path to JSON text file of comment/submissions.

	KWARGS:
		is_submission: boolean.
			set True if file contains Submission posts, else assume file 
			contains Comment posts.  Alters which SQL table is written into.  
			Default False (Comment posts).
	"""
	# open SQL connection
	conn = pms.connect(host='localhost',
		user='root',
		passwd='',
		db='empath',
		charset='utf8',
		init_command='SET NAMES UTF8')

	# read JSON file
	with open(filepath,'r') as readfile:
		for line in readfile:
			data = json.loads(line)
			if is_submission:
				write_submission(data,conn)
			else:
				write_comment(data,conn)

	#close SQL connection
	conn.commit()
	conn.close()


def write_comment(data,conn):
	"""Write data from JSON dict into empath.Comments SQL table.

	ARGS:
		data: dict.
			JSON dict of comment data.
		conn: pymysql.Connect object.
			connection to SQL database.
	"""
	cur = conn.cursor()

	author = data['author']
	body = data['body']
	controversiality = data['controversiality']
	created_utc = data['created_utc']
	distinguished = data['distinguished']
	edited = data['edited']
	gilded = data['gilded']
	post_id = data['id']
	link_id = data['link_id']
	parent_id = data['parent_id']
	retrieved_on = data['retrieved_on']
	score = data['score']
	subreddit = data['subreddit']
	subreddit_id = data['subreddit_id']
	ups = data['ups']

	cur.execute('INSERT INTO Comments '
		'(author,'
		'body,'
		'controversiality,'
		'created_utc,'
		'distinguished,'
		'edited,'
		'gilded,'
		'`id`,'
		'link_id,'
		'parent_id,'
		'retrieved_on,'
		'score,'
		'subreddit,'
		'subreddit_id,'
		'ups) '
		'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
		(author,
			body,
			controversiality,
			created_utc,
			distinguished,
			edited,
			gilded,
			post_id,
			link_id,
			parent_id,
			retrieved_on,
			score,
			subreddit,
			subreddit_id,
			ups)
		)

def write_submission(data,conn):
	"""
	"""
	pass
	# don't currently need to parse submissions, have enough data from 
	# comments alone.  back-burner this