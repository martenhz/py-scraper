from lxml import html
import requests
from multiprocessing.dummy import Pool as ThreadPool
import json
import threading
from config_local import config


MAX_THREADS = 2

START_DOMAIN = config["START_DOMAIN"]
LINKS_FILE = config["LINKS_FILE"]
ENTITIES_FILE = config["ENTITIES_FILE"] 


entities = []
lock = threading.Lock()


def append_entity(e):
    with lock:
        entities.append(e)

def clean_up(text):
    return text.replace(u"\u00A0", " ").strip()

def read_data(path, trs):
    print "Reading path", path
    entity = {'path': path}
    current_category = path
    entity[current_category] = []
    for tr in trs:
        tds = tr.xpath("td")
        length = len(tds)
        if length == 1: # Category
            temp_cat = clean_up(tds[0].text_content())
            if temp_cat:
                current_category = temp_cat
                entity[current_category] = []
        elif length == 2: # Data belonging to current category
            entity[current_category].append({clean_up(tds[0].text_content()): clean_up(tds[1].text_content())})
    append_entity(entity)

def scrape_page(path):
    page = requests.get(START_DOMAIN + path)
    tree = html.fromstring(page.content)
    infobox = tree.xpath("//table[@class='infobox']")
    if infobox and infobox[0] is not None:
        trs = infobox[0].xpath("tr")
        read_data(path, trs)


# Get links from a file
with open(LINKS_FILE) as f:
    paths = f.readlines()

# Remove whitespace characters like `\n` at the end of each line
paths = [x.strip() for x in paths]

pool = ThreadPool(MAX_THREADS)
pool.map(scrape_page, paths)

# Close the pool and wait for the work to finish 
pool.close() 
pool.join() 

#print "Entities: ", json.dumps(entities)

file=open(ENTITIES_FILE, 'w+')
file.write(json.dumps(entities))
