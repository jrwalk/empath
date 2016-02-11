# empath
Sentiment analysis and recommender engine built on reddit mentions of 
antidepressant usage.  Developed for the Insight Health Data Science program, 
January 2016 session.  Final product at [empath-engine.me](http://www.empath-engine.me).

## Structure
* /data/:
storage for raw datasets to be processed and fed into the final SQL table for 
analysis.
	* /data/drugs/:
prescription-drug data.
	* /data/reddit/:
Raw and 1st-pass processed reddit comments/submissions.
* /drug_data/:
scripts to build lookup tables of drug names and side effects, 
scraped from FDA and other databases.
* /scraper/:
tools for parsing reddit comments for keywords, saving to JSON files and 
writing to raw-data SQL tables.
* /NLP/:
natural-language processing implementations for comment analysis.
* /app/:
Flask code for webapp.
