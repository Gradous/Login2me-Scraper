from bs4 import BeautifulSoup
from time import localtime, strftime, sleep
from os import remove, fsync
import argparse
import random
import sys
import urllib2


"""
Globals
"""
USER_AGENT = 'FakeAccount-Scraper (github.com/Gradous/FakeAccount-Scraper)'

"""
Main scraping/spidering function
"""

def scrape(url):
	# A custom user agent!
	fakeaccount_req = urllib2.Request('http://fakeaccount.net/login/' + url,
		headers={'User-agent' : USER_AGENT})
	try:
		fakeaccount_response = urllib2.urlopen(fakeaccount_req)
		# Extract the entries for accounts from the BeautifulSoup
		fa_soup = BeautifulSoup(fakeaccount_response.read()).find("div", {"id" : "items"})
		fa_soup = BeautifulSoup(str(fa_soup)).findAll("div", {"class" : "item"})

		""" 
		The soup will be empty if the page has no accounts or falls into the "bad"
		category (paywalled, commmunity, etc.)
		"""
		if not fa_soup:
			print "No results for", url, "!"
			fakeaccount_response.close()
			return None

		# Buckets for parsing
		usernames = []
		passwords = []
		rates = []
		votes = []
		for account in fa_soup:
			# this was significantly easier than BugMeNot
			usernames.append(BeautifulSoup(str(account)).\
			find("span", {"class" : "login"}).text)
			passwords.append(BeautifulSoup(str(account)).\
			find("span", {"class" : "password"}).text)
			rates.append(BeautifulSoup(str(account)).\
			find("span", {"class" : "rating"}).text.strip())
			# split off a little extra text from the votes
			votes.append(BeautifulSoup(str(account)).\
			find("span", {"class" : "votes"}).text[1:-1])

		# return the list of tuples for later parsing
		fakeaccount_response.close()
		return zip(usernames, passwords, rates, votes)
	except urllib2.HTTPError, e:
		print "Error code: ", e.code
		# in the odd case of 404, keep going
		if e.code == 404:
			print url, "- HTTP 404"
			return None
		else:
			raise e(e.fp.read())


"""
Write out the results to a file
"""
def write_result(url, results, log):
	# result tuple = (user, pass, success %, votes, age)
	with open(log, 'a+') as logfile:
		stats = [] # for some averages and whatnot
		for r in results:
			logfile.write(url + ',')
			logfile.write(','.join([d if d is not None else "#None#" for d in r])\
			.encode("UTF-8"))
			logfile.write('\n')
		logfile.flush()
		fsync(logfile)

def parse_args():
	parser = argparse.ArgumentParser(description='Scrape FakeAccount for accounts')
	parser.add_argument('-f', '--file', nargs=1, help='Site list for scraping',
		default=['alexa_top_1m.csv'])
	parser.add_argument('-n', '--no-results', action='store_false',
		help="Don't write results to file")
	parser.add_argument('-m', '--max-sites', nargs=1, help="Max sites to parse",
		default=[1000000])
	parser.add_argument('-o', '--output', nargs=1,
		default=['result_' + strftime("%m-%d-%Y_%H:%M:%S", localtime()) + '.txt'],
		help='Result output file. Defaults to current date and time.')
	parser.add_argument('-s', '--skip', nargs=1, default=[1], 
		help='Skip to entry X before scraping')
	return parser.parse_args()

def report_results(url, result, result_num, writeout, log):
	print url, "has", len(result), "results!"
	# write out the working sites to a new file?
	if writeout:
		write_result(url, result, log)

def main(scrape_file, min_wait=1.0, max_wait=3.5, **kwargs):
	# seed for waiting
	random.seed()

	try:
		with open(scrape_file, 'r') as to_scrape:
			site_counter = kwargs['site_counter'] # loop break, default=1
			result_number = 1 # counter for filtered set
			for site in to_scrape:
				url = site.rsplit(',')[1].strip()
				url_num = site.rsplit(',')[0].strip()
				# --skip option takes effect here
				if int(url_num) == int(site_counter):
					# get the result, None = failure
					site_result = scrape(url)
					if site_result:
						# record the results
						report_results(url, site_result,
							result_number, kwargs['writeout'],
							kwargs['logfile'])
						result_number += 1
					if site_counter >= int(kwargs['site_counter']) +\
					 int(kwargs['max_sites'] - 1):
						break
					# don't want to DoS...
					sleep(random.uniform(min_wait, max_wait))
					site_counter += 1
			
	except IOError, e:
		raise IOError("File " + e.filename + " does not exist!")
	except KeyboardInterrupt, e2:
		# ask to delete the incomplete logfile
		if kwargs['writeout']:
			if raw_input("Interrupted. Delete the results" +\
				" file? (Y/N) ").upper() == 'Y':
				try: # just in case python didn't actually write yet...
					remove(kwargs['logfile'])
				except OSError, e:
					pass

if __name__ == "__main__":	
	args = parse_args()
	main(writeout=args.no_results, max_sites=int(args.max_sites[0]),
		logfile=args.output[0], scrape_file=args.file[0],
		site_counter=int(args.skip[0]))
