import argparse
import errno
import os
import requests
import zipfile

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains


HOME = os.path.expanduser("~")
MUSIC_DIR = os.path.join(HOME, 'Music')

def main():

	parser = argparse.ArgumentParser()
	
	# required arguments
	parser.add_argument('username')
	parser.add_argument('password')

	# optional arguments
	parser.add_argument('--output_directory', action='store', help='Absolute path to where to store downloaded files.', default=MUSIC_DIR)
	args = parser.parse_args()

	# run millionz
	run(args.username, args.password, args.output_directory)

def mkdir_p(path):
	try:
		os.makedirs(path)
	except OSError as exc: # Python >2.5
		if exc.errno == errno.EEXIST and os.path.isdir(path):
			pass
		else: raise

def download_file(url, output_dir):
	local_path = os.path.join(output_dir, url.split("/")[-1])
	r = requests.get(url, stream=True)
	with open(local_path, 'wb') as f:
		for chunk in r.iter_content(chunk_size=1024): 
			if chunk: # filter out keep-alive new chunks
				f.write(chunk)
				f.flush()
	return local_path


def run(username, password, output_dir):

	# initialize terminal

	# initialize selenium browser driver
	browser = webdriver.Firefox()
	browser.get('http://www.mp3million.com/')

	# enter user credentials to login
	login_elements = browser.find_element_by_name('email')
	login_elements.send_keys(username)
	login_elements.send_keys(Keys.TAB)

	login_elements = WebDriverWait(browser, 5).until(
	   EC.presence_of_element_located((By.ID, "pass_ch_p"))
	)

	login_elements.send_keys(password)
	login_elements.send_keys(Keys.TAB)
	login_elements.send_keys(Keys.RETURN)

	# if we're redirected to solve captcha
	if browser.current_url == "http://www.mp3million.com/auth":

		actionChains = ActionChains(driver)
		captcha_div = browser.find_element_by_css_selector(".captcha-img")
		actionChains.move_to_element(captcha_div).context_click(captcha_div).perform()


	# go to downloads page
	# look for downloadable stuff
	browser.get("http://www.mp3million.com/downloads?p=0")
	download_cards = browser.find_elements_by_css_selector('.ex-card-col')
	total_cards = len(download_cards)
	
	for i, card in enumerate(download_cards):

		try:
			# retrieve information for the card
			title = card.find_element_by_tag_name("h3").text
			artist = title.split('\\')[0]
			album = title.split('\\')[1]
			year = card.find_element_by_css_selector(".fast-info .frst").text[6:]
			download_link = card.find_element_by_css_selector(".zip-cd").get_attribute("href")

			# notify user
			disp_dict = {
				'current': i,
				'total_cards': total_cards,
				'artist': artist,
				'album': album,
				'year': year
			}
			print "(%(current)s / %(total_cards)s) %(artist)s - %(year)s - %(album)s" % disp_dict

			# determine local paths
			abs_local_path = os.path.join(output_dir, artist, "%s - %s" % (year, album))
			if os.path.exists(abs_local_path):
				print "\t - Already Downloaded. Skipping..."
				continue
			mkdir_p(abs_local_path)

			downloaded_path = download_file(download_link, abs_local_path)
			print "\t - Downloaded to: %s" % downloaded_path
			with zipfile.ZipFile(downloaded_path, 'r') as zf:
				zf.extractall(os.path.dirname(downloaded_path))
			os.remove(downloaded_path)
		except Exception, e:
			print "\t - ERROR: Unable to download file: %s" % e.message


if __name__ == "__main__":

	main()