from bs4 import BeautifulSoup
from time import localtime, strftime, sleep
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
MAX_SITES = 20 # number of sites we want to do
"""

Main scraping/spidering function
"""
def scrape(url):
	# First check if we should ignore it
	if url.rsplit('.')[0] in IGNORE_SET:
		print url, "is being ignored!"
		return None

	# Spoof our user agent since BMN doesn't like bots
	bugmenot_req = urllib2.Request('http://bugmenot.com/view/' + url,
		headers={'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64)'})
	try:
		bugmenot_response = urllib2.urlopen(bugmenot_req)
	except urllib2.HTTPError, e:
		print "Error code: ", e.code
		if e.code == 404:
			# they're blocking me!
			print "HTTP 404, retrying in 10 seconds"
			sleep(10)
			return -1
		else:
			print e.fp.read()
			raise e

	# Extract the entries for accounts from the BeautifulSoup
	bmn_soup = BeautifulSoup(bugmenot_response.read()).findAll(class_="account")

	""" 
	The soup will be empty if the page has no accounts or falls into the "bad"
	category (paywalled, commmunity, etc.)
	"""
	if not bmn_soup:
		print "No results for", url, "!"
		# add to the ignore set
		IGNORE_SET.add(url.rsplit('.')[0])
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
	return zip(usernames, passwords, rates)

"""
Write out the results to a file
"""
def write_result(url, result):
	# TODO: log results
	print strftime("%m-%d-%Y_%H:%M:%S", localtime())

def parse_args():
	parser = argparse.ArgumentParser(description='Scrape BugMeNot for valid accounts')
	parser.add_argument('-s', '--sites', nargs=1, help='Site list for scraping') # -f for site file
	parser.add_argument('-g', '--generate', nargs=1,
		help="""Use the Alexa list instead and write out working sites
		to a new file.""") # -r for regenerate working site file
	parser.add_argument('-n', '--no-results', help="Don't write results to file")
	parser.add_argument('-m', '--max-sites', nargs=1, help="Max sites to parse")
	return parser.parse_args()

def main():
	# seed for waiting
	random.seed()
	try:
		if GEN_FILE:
			if GEN_FILE == SCRAPE_FILE:
				print "HEY! Don't use the same file for two things!!!"
				raise IOError
			gen_file = open(GEN_FILE, 'w+')

		with open(SCRAPE_FILE, 'r') as alexa_list:
			site_counter = 0
			result_number = 0 # this is for later parsing of a smaller set
			for site in alexa_list:
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
				# write_result(site.rsplit(',')[1].strip(), site_result)
				if site_counter >= MAX_SITES:
					break
				# don't want to DoS...
				sleep(random.uniform(1.0, 3.55))
				site_counter += 1
			gen_file.close() # this is annoying but it makes my design easier to read
	except IOError, e:
		print "Site list file does not exist!"
		raise IOError
		

if __name__ == "__main__":	
	args = parse_args()
	# in case we want to use a different site list, i.e. one we parsed
	if args.sites:
		SCRAPE_FILE = args.sites[0]
	if args.generate:
		GEN_FILE = args.generate[0]
	if args.max_sites:
		MAX_SITES = int(args.max_sites[0])
	main()

