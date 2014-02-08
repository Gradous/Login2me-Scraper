from bs4 import BeautifulSoup
from time import localtime, strftime, sleep
import random
import sys
import urllib2


"""
Globals
"""
IGNORE_SET = set() # keeps up with the sites that we know don't work
SCRAPE_FILE = 'alexa_top_1m.csv' # default to alexa list

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

def main():
	# seed for waiting
	random.seed()
	try:
		with open(SCRAPE_FILE, 'r') as alexa_list:
			for site in alexa_list:
				url = site.rsplit(',')[1].strip()
				site_result = scrape(url)
				if site_result:
					print url, "has", len(site_result), "results!"
				# write_result(site.rsplit(',')[1].strip(), site_result)
				if int(site.rsplit(',')[0]) >= 16:
					break
				# don't want to DoS...
				sleep(random.uniform(0.5, 2.25))
	except IOError, e:
		print "Site list file does not exist!"
		raise IOError

if __name__ == "__main__":	
	# TODO Argument parser
	main()

