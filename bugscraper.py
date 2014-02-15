from bs4 import BeautifulSoup
from time import localtime, strftime, sleep
from os import remove
import argparse
import random
import sys
import urllib2

# https://twitter.com/guyking
# Founder of BugMeNot


"""
Globals
"""
USER_AGENT = 'Bug-Scraper1.0 (github.com/Gradous/Bug-Scraper)'
"""

Main scraping/spidering function
"""
def scrape(url):
	# A custom user agent!
	bugmenot_req = urllib2.Request('http://bugmenot.com/view/' + url,
		headers={'User-agent' : USER_AGENT})
	try:
		bugmenot_response = urllib2.urlopen(bugmenot_req)
		# Extract the entries for accounts from the BeautifulSoup
		bmn_soup = BeautifulSoup(bugmenot_response.read()).findAll(class_="account")

		""" 
		The soup will be empty if the page has no accounts or falls into the "bad"
		category (paywalled, commmunity, etc.)
		"""
		if not bmn_soup:
			print "No results for", url, "!"
			# add to the ignore set
			#IGNORE_SET.add(url.rsplit('.')[0])
			bugmenot_response.close()
			return None

		# Buckets for parsing
		usernames = []
		passwords = []
		rates = []

		for account in bmn_soup:
			# First, parse the accounts for usernames and passwords
			counter = 0 
			for userpass in BeautifulSoup(str(account)).findAll('kbd'):
				if counter == 0: # we have a username
					counter += 1
					usernames.append(userpass.contents)
				elif counter == 1: # we have a password
					counter += 1
					passwords.append(userpass.contents)
				else: # we have a comment, ignore it and reset counter
					counter = 0
				# Next, parse for the success rates
				for success in BeautifulSoup(str(account)).findAll(class_='success_rate'):
					rates.append(success.contents)

		# return the list of tuples for later parsing
		bugmenot_response.close()
		return zip(usernames, passwords, rates)
	except urllib2.HTTPError, e:
		print "Error code: ", e.code
		# in the odd case of 404, keep going
		if e.code == 404:
			print url, "- HTTP 404"
			return None
		else:
			print e.fp.read()
			raise e


"""
Write out the results to a file
TODO: Add more stats (numpy?)
"""
def write_result(url, results, log):
	with open(log, 'a+') as logfile:
		stats = [] # for some averages and whatnot
		logfile.write(url + '\n')
		logfile.write("Results: " + str(len(results)) + '\n')
		for r in results:
			stats.append(int((str(r[2][0]).rsplit('%'))[0]))
		logfile.write("Average success %: " + str(sum(stats)/len(stats)) + '\n')

def parse_args():
	parser = argparse.ArgumentParser(description='Scrape BugMeNot for valid accounts')
	parser.add_argument('-s', '--sites', nargs=1, help='Site list for scraping',
		default='alexa_top_1m.csv')
	parser.add_argument('-g', '--generate', nargs=1,
		help="""Use the Alexa list instead and write out working sites
		to a new file.""")
	parser.add_argument('-n', '--no-results', action='store_false',
		help="Don't write results to file")
	parser.add_argument('-m', '--max-sites', nargs=1, help="Max sites to parse")
	parser.add_argument('-o', '--output', nargs=1,
		default='result_' + strftime("%m-%d-%Y_%H:%M:%S", localtime()) + '.txt',
		help='Result output file. Defaults to current date and time.')
	return parser.parse_args()

def main(scrape_file, gen_file, min_wait=1.0, max_wait=3.5, **kwargs):
	# seed for waiting
	random.seed()

	if gen_file == scrape_file:
		print "HEY! Don't use the same file for two things!!!"
		raise IOError
	if gen_file:
		gen_file = open(gen_file, 'w+')

	try:
		with open(scrape_file, 'r') as to_scrape:
			site_counter = 1 # loop break
			result_number = 0 # this is for later parsing of a smaller set
			for site in to_scrape:
				url = site.rsplit(',')[1].strip()
				site_result = scrape(url)
				# account for failures due to 404
				while site_result == -1:
					site_result = scrape(url)
				if site_result:
					result_number += 1
					print url, "has", len(site_result), "results!"
					# write out the working sites to a new file?
					if gen_file:
						gen_file.write(str(result_number) + ',' + url + '\n')
					if kwargs['writeout']:
						write_result(url, site_result, kwargs['logfile'])
				if site_counter >= kwargs['max_sites']:
					break
				# don't want to DoS...
				sleep(random.uniform(min_wait, max_wait))
				site_counter += 1
			
	except IOError, e:
		print "Site list file does not exist!"
		raise IOError
	except KeyboardInterrupt, e2:
		# ask to delete the incomplete logfile
		if kwargs['writeout']:
			if raw_input("Interrupted. Delete the results file? (Y/N) ").upper() == 'Y':
				try: # just in case python didn't actually write yet...
					remove(kwargs['logfile'])
				except OSError, e:
					pass
	finally:
		if gen_file:
			gen_file.close() # this is annoying but I have to do it
		

if __name__ == "__main__":	
	args = parse_args()
	main(writeout=args.no_results, max_sites=int(args.max_sites[0]),
		logfile=args.output, scrape_file=args.sites,
		gen_file=args.generate)
