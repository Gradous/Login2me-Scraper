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
IGNORE_SET = set() # keeps up with the sites that we know don't work
SCRAPE_FILE = 'alexa_top_1m.csv' # default to alexa list
GEN_FILE = '' # write out sites that work with -g option
RESULTS_FILE = '' # write password results to this file
WAIT_MULT = 1
USER_AGENT = 'Bug-Scraper1.0 (gitbhub.com/Gradous/Bug-Scraper)'
"""
USER_AGENTS = ['Mozilla/5.0 (Windows NT 6.1; WOW64)',
'Mozilla/5.0 (iPad; U; CPU OS 3_2_1 like Mac OS X; en-us)'+
'AppleWebKit/531.21.10 (KHTML, like Gecko) Mobile/7B405',
'Mozzilla/5.0 (Windows NT 7.0; Win64; x64; rv:3.0b2pre)'+
'Gecko/20110203 Firefox/4.0b12pre',
'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.11 (KHTML,'+
'like Gecko) Chrome/23.0.1271.95 Safari/537.11',
'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3)'+
'AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11',
'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36'+
'(KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36']
"""

"""

Main scraping/spidering function
"""
def scrape(url):
	# First check if we should ignore it
	#if url.rsplit('.')[0] in IGNORE_SET:
	#	print url, "is being ignored!"
	#	return None

	# Spoof our user agent since BMN doesn't like bots
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
		if e.code == 404:
			print url, "- HTTP 404"
			#bugmenot_response.close()
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
	parser.add_argument('-s', '--sites', nargs=1, help='Site list for scraping') # -f for site file
	parser.add_argument('-g', '--generate', nargs=1,
		help="""Use the Alexa list instead and write out working sites
		to a new file.""") # -r for regenerate working site file
	parser.add_argument('-n', '--no-results', action='store_false',
		help="Don't write results to file")
	parser.add_argument('-m', '--max-sites', nargs=1, default=[20], help="Max sites to parse")
	parser.add_argument('-o', '--output', nargs=1,
		default='result_' + strftime("%m-%d-%Y_%H:%M:%S", localtime()) + '.txt',
		help='Result output file. Defaults to current date and time.')
	return parser.parse_args()

def main(**kwargs):
	# seed for waiting
	random.seed()

	gen_file = ''
	if GEN_FILE:
		if GEN_FILE == SCRAPE_FILE:
			print "HEY! Don't use the same file for two things!!!"
			raise IOError
		gen_file = open(GEN_FILE, 'w+')

	try:
		with open(SCRAPE_FILE, 'r') as scrape_file:
			site_counter = 1 # loop break
			result_number = 0 # this is for later parsing of a smaller set
			for site in scrape_file:
				url = site.rsplit(',')[1].strip()
				site_result = scrape(url)
				# account for failures due to 404
				while site_result == -1:
					site_result = scrape(url)
				if site_result:
					result_number += 1
					print url, "has", len(site_result), "results!"
					# write out the working sites to a new file?
					if GEN_FILE:
						gen_file.write(str(result_number) + ',' + url + '\n')
					if kwargs['writeout']:
						write_result(url, site_result, kwargs['logfile'])
				if site_counter >= kwargs['max_sites']:
					break
				# don't want to DoS...
				sleep(random.uniform(1.5, 3.5))
				site_counter += 1
			
	except IOError, e:
		print "Site list file does not exist!"
		raise IOError
	except KeyboardInterrupt, e2:
		# ask to delete the incomplete logfile
		if kwargs['writeout']:
			if raw_input("Interrupted. Delete the results file? (Y/N) ").upper() == 'Y':
				remove(kwargs['logfile'])
	finally:
		if gen_file:
			gen_file.close() # this is annoying but it makes my design easier to read
		

if __name__ == "__main__":	
	args = parse_args()
	if args.sites:
		SCRAPE_FILE = args.sites[0]
	if args.generate:
		GEN_FILE = args.generate[0]
	main(writeout=args.no_results, max_sites=int(args.max_sites[0]),
		logfile=args.output)
