import argparse
import errno
import os
import requests
import platform
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

    # with open(local_path, 'wb') as handle:
    #     response = requests.get('http://www.example.com/image.jpg', stream=True)

    #     if not response.ok:
    #         raise IOError("Unable to download file.")

    #     for block in response.iter_content(1024):
    #         if not block:
    #             break

    #         handle.write(block)
    # return local_path

    with open(local_path, "wb") as handler:

        response = requests.get(url, stream=True)
        if not response.ok:
            raise IOError(f"Unable to download the file { url }")

        for block in response.iter_content(1024):
            if not block:
                break

            handler.write(block)
    return local_path

    # f = urllib2.urlopen(url)
    # data = f.read()
    # with open(local_path, "wb") as handler:
    #     handler.write(data)
    # return local_path


def run(username, password, output_dir):

    # determine chrome driver path
    chromedrivers_filenames = {
        '32bit' : {
            'Linux': 'NOT SUPPORTED',
            'macOS': 'NOT SUPPORTED',
            'Windows': 'NOT SUPPORTED'
        },
        '64bit' : {
            'Linux': 'chromedriver_linux64',
            'macOS': 'chromedriver_mac_arm64',
            'Windows': 'chromedriver_win64.exe'
        }
    }
    basedir =  os.path.dirname(os.path.realpath(__file__))
    local_os = platform.platform().split("-")[0]
    local_arch = platform.architecture()[0]
    try:
        print(f"Local Arch: { local_arch }")
        print(f"Local OS:   { local_os }")
        driver_path = os.path.join(basedir, 'chromedriver', chromedrivers_filenames[local_arch][local_os])

        if 'NOT SUPPORTED' in driver_path:
            print(f"The driver is not supported in your arch ({ local_arch }) or os ({ local_os })")
            return

        print("Driver Path: ", driver_path)
        browser = webdriver.Chrome(driver_path)
    except Exception as e:
        print("Unable to get Chrome Driver")
        print(e)
        return


    # get our page
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
    purchased_items = []

    # aggregate the download links
    print("Aggregating...")
    for i, card in enumerate(download_cards):
        
        year, title, artist, album = None, None, None, None
        try:
            # retrieve information for the card
            title = card.find_element_by_tag_name("h3").text.strip()
            artist = title.split('\\')[0].replace("/", "-").strip()
            album = title.split('\\')[1].replace("/", "-").strip()
            year = card.find_element_by_css_selector(".fast-info .frst").text[6:].strip()
            download_link = card.find_element_by_css_selector(".zip-cd").get_attribute("href").strip()
            

            # notify user
            item = {
                'current': i,
                'total_cards': total_cards,
                'artist': artist,
                'album': album,
                'year': year,
                'download_link': download_link
            }
            print("\t -- (%(current)s / %(total_cards)s) %(artist)s - %(year)s - %(album)s" % item)
            purchased_items.append(item)
        except Exception as e:
            
            item = {
                'current': i,
                'total_cards': total_cards,
                'artist': artist,
                'album': album,
                'year': year
            }
            print("\t -- (%(current)s / %(total_cards)s) %(artist)s - %(year)s - %(album)s" % item)
            print("\t - Unable to aggregate %s" % e.message)


    # close browser
    browser.close()

    # start downloading
    print("Downloading...")
    for item in purchased_items:

        year = item['year']
        album = item['album']
        artist = item['artist']
        download_link = item['download_link']
        print("\t -- (%(current)s / %(total_cards)s) %(artist)s - %(year)s - %(album)s" % item)
        try:

            # determine local paths
            abs_local_path = os.path.join(output_dir, artist, "%s - %s" % (year, album))
            if os.path.exists(abs_local_path):
                print("\t - Already Downloaded. Skipping...")
                continue
            mkdir_p(abs_local_path)
            print("\t - Downloading: %s" % download_link)

            downloaded_path = download_file(download_link, abs_local_path)
            print("\t - Downloaded to: %s" % downloaded_path)
            with zipfile.ZipFile(downloaded_path, 'r') as zf:
                zf.extractall(os.path.dirname(downloaded_path))
            os.remove(downloaded_path)
        except Exception as e:
            print("\t - ERROR: Unable to download file: %s" % e.message)
            raise


if __name__ == "__main__":

    main()
