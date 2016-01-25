"""Quick script to scrape antidepressant list (antidepressants.txt) taken from 
FDA list of antidepressants with medication guide.  (US names only?)
"""
import re


def build_drug_dict(filepath):
	"""reads data from /empath/data/drugs/antidepressants.txt, builds dict of 
	{'alt name':'generic name'}.

	ARGS:
		filepath: string.
			path to text file of drug names.

	RETURNS:
		drug_dict: dict.
			dict of {'alt name':'generic name'} for drugs in 
			antidepressants.txt.
	"""
	drug_dict = {}
	with open(filepath,'r') as readfile:
		for line in readfile:
			# find drugs of the form brand (generic)
			res = re.match('(\w+) (\(\w+)',line)
			if res:
				brand = res.group(1)
				generic = res.group(2)[1:]	# trim off leading paren
				if brand.upper() not in drug_dict.keys():
					drug_dict[brand.upper()] = generic.upper()
				# generic maps to itself
				if generic.upper() not in drug_dict.keys():
					drug_dict[generic.upper()] = generic.upper()
			else:
				# account for drugs listed with only generic name
				res = re.match('(\w+)',line)
				generic = res.group(0)
				if generic.upper() not in drug_dict.keys():
					drug_dict[generic.upper()] = generic.upper()
	return drug_dict


def generic_dict(drug_dict):
	"""reads dict from build_drug_dict of the form {'alt name':'generic name'}, 
	builds inverse dict of {'generic name':['alt names']}.

	ARGS:
		drug_dict: dict.
			dict of {'alt name':'generic name'} for drugs in 
			antidepressants.txt.

	RETURNS:
		gen_dict: dict.
			dict of {'generic name':['alt names']} from drug_dict.
 	"""
 	gen_dict = {}
 	for drug in drug_dict.keys():
 		gen = drug_dict[drug]
 		if gen != drug:
	 		if gen in gen_dict.keys():
	 			gen_dict[gen].append(drug)
	 		else:
	 			gen_dict[gen] = [drug]
 	return gen_dict


def flatten(drug_dict):
	"""Quick script to flatten drug_dict into list of names.

	ARGS:
		drug_dict: dict.
			dict of drugs of the form {'alt name':'generic name'}

	RETURNS:
		drug_list: list.
			flattened list of drug names for search.
	"""
	drug_list = []
	for altname in drug_dict:
		drug_list.append(altname)
		if drug_dict[altname] is not altname:	# catch generics mapping to self
			drug_list.append(drug_dict[altname])

	# final check for duplicates:
	drug_list = set(drug_list)
	drug_list = list(drug_list)
	return drug_list


def generics(drug_dict):
	"""returns sorted unique list of generic drugs, drawn from drug_dict remap.

	ARGS:
		drug_dict: dict.
			dict of drugs of the form {'alt name':'generic name'}

	RETURNS:
		generics: list.
			sorted unique list of generic drugs.
	"""
	return sorted(list(set(drug_dict.values())))



