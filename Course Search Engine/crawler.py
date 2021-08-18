# CS122: Course Search Engine Part 1
#
# Rhedintza Audryna and James Yunzhang Hu
#

import re
import util
import bs4
import queue
import json
import sys
import csv

INDEX_IGNORE = set(['a', 'also', 'an', 'and', 'are', 'as', 'at', 'be',
                    'but', 'by', 'course', 'for', 'from', 'how', 'i',
                    'ii', 'iii', 'in', 'include', 'is', 'not', 'of',
                    'on', 'or', 's', 'sequence', 'so', 'social', 'students',
                    'such', 'that', 'the', 'their', 'this', 'through', 'to',
                    'topics', 'units', 'we', 'were', 'which', 'will', 'with',
                    'yet'])


def process_url(current_url, new_url):
    '''
    If new_url is a relative URL, convert it into an absolute URL;
    otherwise, leave it as an absolute URL. Subsequently, remove
    fragments from the URL. Helper function for update_pages().

    Inputs:
        current_url (string): absolute URL of current page
        new_url (string): URL to process

    Outputs:
        string
    '''
    absolute_url = util.convert_if_relative_url(current_url, new_url)
    return util.remove_fragment(absolute_url)


def update_pages(page, scraped, to_scrape, limiting_domain):
    '''
    Add the current page to the set of scraped pages and, using the links
    scraped from the page, add new pages to the list of pages to scrape.

    Inputs:
        page (request object): the webpage currently being scraped
        scraped (set of strings): the URLS of the webpages that have
          already been scraped, i.e. log
        to_scrape (list of strings): the URLS of the webpages that are
          queued to be scraped, i.e. itinerary
        limiting_domain (string): the domain within which URLs are
          considered okay to follow

    Outputs:
        None (modifies set and list in-place)
    '''
    current_url = util.get_request_url(page)
    scraped.add(current_url)

    html = util.read_request(page)
    soup = bs4.BeautifulSoup(html, "html5lib")

    all_tags = soup.find_all("a", href=True)
    new_urls = [tag.get("href") for tag in all_tags]

    for new_url in new_urls:
        processed_url = process_url(current_url, new_url)
        valid = all([util.is_url_ok_to_follow(processed_url, limiting_domain),
                     processed_url not in scraped,
                     processed_url not in to_scrape])
        if valid:
            to_scrape.append(processed_url)


def get_words(course):
    '''
    Extract the words from a course div tag, excluding common words
    and made lowercase. Helper function for scrape.

    Inputs:
        course (tag): a course div tag

    Outputs:
        set of strings
    '''
    title = course.find("p", class_="courseblocktitle").text
    desc = course.find("p", class_="courseblockdesc").text

    title_words = re.findall("[a-zA-Z][a-zA-Z\d]*", title)
    desc_words = re.findall("[a-zA-Z][a-zA-Z\d]*", desc)
    all_words = set(title_words + desc_words)

    return {word.lower() for word in all_words if word not in INDEX_IGNORE}


def get_course_code(course):
    '''
    Retrieve the course code corresponding to a course div tag.
    Helper function for scrape.

    Inputs:
        course (tag): a course div tag

    Outputs:
        string
    '''
    title = course.find("p", class_="courseblocktitle").text
    code = re.search("([A-Z]{4})\xa0(\d{5})", title)
    return code[1] + " " + code[2]


def scrape(page, code_to_id, index):
    '''
    Scrape the webpage for words pertaining to specific courses and
    update the index.

    Inputs: 
        page (request object): the webpage currently being scraped
        code_to_id (dictionary): mapping of course codes to course IDs
        index (dictionary): mapping of words to course IDs

    Outputs:
        None (modifies index in-place)
    '''
    html = util.read_request(page)
    soup = bs4.BeautifulSoup(html, "html5lib")

    all_courses = soup.find_all("div", class_="courseblock main")

    for course in all_courses:
        words = get_words(course)
        sequence = util.find_sequence(course)
        if sequence:
            for subseq in sequence:
                code = get_course_code(subseq)
                subseq_words = get_words(subseq)
                total_words = words | subseq_words
                for word in total_words:
                    index[word] = index.get(word, []) + [code_to_id[code]]
        else:
            code = get_course_code(course)
            for word in words:
                index[word] = index.get(word, []) + [code_to_id[code]]


def go(num_pages_to_crawl, course_map_filename, index_filename):
    '''
    Crawl the college catalog and generate a CSV file with an index.

    Inputs:
        num_pages_to_crawl: the number of pages to process during the crawl
        course_map_filename: the name of a JSON file that contains the
          mapping of course codes to course identifiers
        index_filename: the name for the CSV of the index.

    Outputs:
        CSV file of the index
    '''
    starting_url = ("http://www.classes.cs.uchicago.edu/archive/2015/winter"
                    "/12200-1/new.collegecatalog.uchicago.edu/index.html")
    limiting_domain = "classes.cs.uchicago.edu"

    with open(course_map_filename) as course_map:
        code_to_id = json.load(course_map)

    index = {}
    to_scrape = [starting_url]
    scraped = set()

    for _ in range(num_pages_to_crawl):
        current_url = to_scrape.pop(0)
        page = util.get_request(current_url)

        scrape(page, code_to_id, index)
        update_pages(page, scraped, to_scrape, limiting_domain)

        if not to_scrape:
            break

    with open(index_filename, "w") as f:
        writer = csv.writer(f, delimiter="|")
        for word, ids in index.items():
            for id in ids:
                writer.writerow([id, word])


if __name__ == "__main__":
    usage = "python3 crawl.py <number of pages to crawl>"
    args_len = len(sys.argv)
    course_map_filename = "course_map.json"
    index_filename = "catalog_index.csv"
    if args_len == 1:
        num_pages_to_crawl = 1000
    elif args_len == 2:
        try:
            num_pages_to_crawl = int(sys.argv[1])
        except ValueError:
            print(usage)
            sys.exit(0)
    else:
        print(usage)
        sys.exit(0)

    go(num_pages_to_crawl, course_map_filename, index_filename)
