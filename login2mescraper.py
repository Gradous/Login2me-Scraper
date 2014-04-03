from time import localtime, strftime, sleep
from os import remove, fsync
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
import argparse
import random
import sys


# http://selenium-release.storage.googleapis.com/index.html?path=2.40/

"""
Main scraping/spidering function with browser emulation
"""
def scrape(url, min_wait, max_wait):
	# browser driver setup
	# since we're using the Remote webdriver, there is no need to
	# close this later (since it's a separate program)
	browser = webdriver.Remote("http://localhost:4444/wd/hub", \
	webdriver.DesiredCapabilities.HTMLUNITWITHJS)
	# need some waiting due to page load/render time, 
	# should only matter on first search
	browser.implicitly_wait(5)
	try:
		browser.get('http://login2.me#' + url)
		#print browser.page_source

		# OPTION - get the search box and search instead of direct link
		#search = browser.find_element_by_id("url_input")
		#search.send_keys(url)
		# get the submit element and click
		#browser.find_element_by_id("search_form").submit()

		# Buckets for parsing
		usernames = []
		passwords = []
		try:
			# Keep looping until there are no more accounts to show
			more_button_xpath = '//*[@id="acc_form"]/table/tbody/tr[2]/' +\
			'td[2]/table/tbody/tr/td/form/table/tbody/tr[3]/td[2]/table/' +\
			'tbody/tr/td/img'
			# loop will break when the more button can't be found
			while True: 
				more_btn = browser.find_element_by_xpath(more_button_xpath)
				login = browser.find_element_by_id("login").text
				password = browser.find_element_by_id("password").text
				usernames.append(login)
				passwords.append(password)
				sleep(random.uniform(min_wait, max_wait))
				# click for more accounts
				more_btn.click()
				# page render is stupid
				sleep(1)
		# no more usernames when the login field can't be found
		except NoSuchElementException, e: 
			print "No more logins for", url
		# return the list of tuples for later parsing
		return zip(usernames, passwords)
	except WebDriverException, e2:
		print "Oops, gonna have to check the Selenium server"

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
	parser = argparse.ArgumentParser(description='Scrape Login2Me for accounts')
	parser.add_argument('-f', '--file', nargs=1, help='Site list for scraping',
		default=['alexa_top_1m.csv'])
	parser.add_argument('-n', '--no-results', action='store_false',
		help="Don't write results to file")
	parser.add_argument('-m', '--max-sites', nargs=1, help="Max sites to parse",
		default=[1000000])
	parser.add_argument('-o', '--output', nargs=1,
		default=['login2me_result_' + strftime("%m-%d-%Y_%H-%M-%S", localtime()) + '.txt'],
		help='Result output file. Defaults to current date and time.')
	parser.add_argument('-s', '--skip', nargs=1, default=[1], 
		help='Skip to entry X before scraping')
	return parser.parse_args()

def report_results(url, result, result_num, writeout, log):
	print url, "has", len(result), "results!"
	# write out the working sites to a new file?
	if writeout:
		write_result(url, result, log)

def main(scrape_file, min_wait=5.0, max_wait=6.5, **kwargs):
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
					# get the result
					site_result = scrape(url, min_wait, max_wait)
					if site_result:
						# record the results
						report_results(url, site_result,
							result_number, kwargs['writeout'],
							kwargs['logfile'])
						result_number += 1
					if site_counter >= int(kwargs['site_counter']) +\
					 int(kwargs['max_sites'] - 1):
						break
					# don't want to DoS...or get caught
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
