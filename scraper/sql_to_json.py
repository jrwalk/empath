"""back convert rows from the `empath`.`Comments` SQL table into JSON-format 
dicts for easy interaction with python analyses.
"""


def convert(row):
	"""converts row from `empath`.`Comments` back to JSON-format dicts.

	ARGS:
		row: tuple.
			tuple output by pymysql.cursor().execute() on row from 
			`empath`.`Comments`.

	RETURNS:
		data: dict.
			JSON-format dict of results from row.
	"""
	author = row[0]
	body = row[1]
	controversiality = row[2]
	created_utc = row[3]
	distinguished = row[4]
	edited = row[5]
	gilded = row[6]
	post_id = row[7]
	link_id = row[7]
	parent_id = row[8]
	retrieved_on = row[9]
	score = row[10]
	subreddit =row[11]
	subreddit_id = row[12]
	ups = row[13]

	return {'author':author,
		'body':body,
		'controversiality':controversiality,
		'created_utc':created_utc,
		'distinguished':distinguished,
		'edited':edited,
		'gilded':gilded,
		'id':post_id,
		'link_id':link_id,
		'parent_id':parent_id,
		'retrieved_on':retrieved_on,
		'score':score,
		'subreddit':subreddit,
		'subreddit_id':subreddit_id,
		'ups':ups}