import os
import csv
import re
import time
import random
from bs4 import BeautifulSoup
from subprocess import Popen, PIPE
from selenium import webdriver


abspath = lambda *p: os.path.abspath(os.path.join(*p))
ROOT = abspath(os.path.dirname(__file__))


def execute_command(command):
    result = Popen(command, shell=True, stdout=PIPE).stdout.read()
    if len(result) > 0 and not result.isspace():
        raise Exception(result)


def do_screen_capturing(url, url_to_find, screen_path, width, height):
    print "Capturing screen.."
    driver = webdriver.PhantomJS(executable_path='phantomjs.exe', service_args=['--ignore-ssl-errors=true', '--ssl-protocol=any'])
    # it save service log file in same directory
    # if you want to have log file stored else where
    # initialize the webdriver.PhantomJS() as
    # driver = webdriver.PhantomJS(service_log_path='/var/log/phantomjs/ghostdriver.log')
    driver.set_script_timeout(30)
    if width and height:
        driver.set_window_size(width, height)
    driver.get(url)
    results = check_rankings(driver)
    if results:
        for result in results:
            result_url = result['URL']
            rank = str(result['rank'])
            timestr = time.strftime("%Y%m%d-%H%M%S")
            path = ''
            path = screen_path + '-' + rank + '-' + result_url + '-' + timestr + '.png'
            print path
            driver.save_screenshot(path)
    else:
        timestr = time.strftime("%Y%m%d-%H%M%S")
        path = ''
        path = screen_path + '-' + timestr + '.png'
        print path
        driver.save_screenshot(path)

def check_rankings(driver):
    urls = []
    with open('urls.csv', 'rb') as f:
        reader = csv.reader(f)
        for url in reader:
            temp_url = ''.join(url)
            urls.append(temp_url)
    results = parse_results(driver.page_source, urls)
    return results

def parse_results(html, urls):
    soup = BeautifulSoup(html, 'html.parser')

    found_results = []
    rank = 1
    result_block = soup.find_all('div', attrs={'class': 'g'})
    for result in result_block:
        link = result.find('a', href=True)
        title = result.find('h3', attrs={'class': 'r'})
        description = result.find('span', attrs={'class': 'st'})
        if link and title:
            link = link['href']
            title = title.get_text()
            if description:
                description = description.get_text()
            if link != '#':
                for url in urls:
                    temp_url = ''.join(url)
                    if temp_url in link:
                        found_results.append({'URL': url, 'rank': rank})
                rank += 1
    return found_results

def do_crop(params):
    print "Croping captured image.."
    command = [
        'convert',
        params['screen_path'],
        '-crop', '%sx%s+0+0' % (params['width'], params['height']),
        params['crop_path']
    ]
    execute_command(' '.join(command))


def do_thumbnail(params):
    print "Generating thumbnail from croped captured image.."
    command = [
        'convert',
        params['crop_path'],
        '-filter', 'Lanczos',
        '-thumbnail', '%sx%s' % (params['width'], params['height']),
        params['thumbnail_path']
    ]
    execute_command(' '.join(command))


def get_screen_shot(**kwargs):
    url = kwargs['url']
    url_to_find = kwargs['url_to_find']
    width = int(kwargs.get('width', 1024)) # screen width to capture
    height = int(kwargs.get('height', 768)) # screen height to capture
    filename = kwargs.get('filename', 'screen.png') # file name e.g. screen.png
    path = kwargs.get('path', ROOT) # directory path to store screen

    crop = kwargs.get('crop', False) # crop the captured screen
    crop_width = int(kwargs.get('crop_width', width)) # the width of crop screen
    crop_height = int(kwargs.get('crop_height', height)) # the height of crop screen
    crop_replace = kwargs.get('crop_replace', False) # does crop image replace original screen capture?

    thumbnail = kwargs.get('thumbnail', False) # generate thumbnail from screen, requires crop=True
    thumbnail_width = int(kwargs.get('thumbnail_width', width)) # the width of thumbnail
    thumbnail_height = int(kwargs.get('thumbnail_height', height)) # the height of thumbnail
    thumbnail_replace = kwargs.get('thumbnail_replace', False) # does thumbnail image replace crop image?

    filename = re.sub(r"\s+", '-', filename)

    screen_path = abspath(path + '\\images\\', filename)
    crop_path = thumbnail_path = screen_path

    if thumbnail and not crop:
        raise Exception, 'Thumnail generation requires crop image, set crop=True'

    do_screen_capturing(url, url_to_find, screen_path, width, height)

    if crop:
        if not crop_replace:
            crop_path = abspath(path, 'crop_'+filename)
        params = {
            'width': crop_width, 'height': crop_height,
            'crop_path': crop_path, 'screen_path': screen_path}
        do_crop(params)

        if thumbnail:
            if not thumbnail_replace:
                thumbnail_path = abspath(path, 'thumbnail_'+filename)
            params = {
                'width': thumbnail_width, 'height': thumbnail_height,
                'thumbnail_path': thumbnail_path, 'crop_path': crop_path}
            do_thumbnail(params)
    return screen_path, crop_path, thumbnail_path


def get_screenshot(keyword):
    url = 'https://www.google.com/search?q=' + keyword + '&num=100'
    screen_path, crop_path, thumbnail_path = get_screen_shot(
        url=url, url_to_find='dentisttigard.com', filename=keyword,
        crop=True, crop_replace=False,
        thumbnail=True, thumbnail_replace=False,
        thumbnail_width=200, thumbnail_height=150,
    )

def load_data():
    keyword_list = []

    with open('keywords.csv', 'rb') as f:
        reader = csv.reader(f)
        for keyword in reader:
            temp_string = ''.join(keyword)
            keyword_list.append(temp_string)
    return keyword_list

def doStuff():
    keyword_list = load_data()
    for keyword in keyword_list:
        print "getting keyword:" + keyword
        get_screenshot(keyword)
        timer = random.randrange(200, 500, 1)
        print timer
        time.sleep(timer)

if __name__ == '__main__':
    '''
        Requirements:
        Install NodeJS
        Using Node's package manager install phantomjs: npm -g install phantomjs
        install selenium (in your virtualenv, if you are using that)
        install imageMagick
        add phantomjs to system path (on windows)
    '''

    try:
        doStuff()
    except Exception, e:
        f = open('log.txt', 'w')
        f.write('An exceptional thing happed - %s' % e)
        f.close()