import config
import requests
import json
from bs4 import BeautifulSoup
import time
import re
import os
from sys import exit


def get_urls():
    """
    Access the NYT API to get a list of links to the desired reviews

    Returns list of the URLs, or an empty list if there was a problem
    """
    query_url = 'http://api.nytimes.com/svc/search/v2/articlesearch.json' + \
                '?api_key=' + config.NYT_API_KEY + '&begin_date=20130101' + '&end_date = 20181003'+ '&fl=web_url' + \
                '&fq=byline:("Pete Wells")ANDtype_of_material:("Review")ANDnews_desk:("Dining","Food")'
    # Note API key imported from config file to avoid putting confidential stuff on github
    # Query format according to documentation available from NYT

    # Make a first query just to get the total number of reviews
    first_query = requests.get(query_url).json()
    hits = first_query.get('response').get('meta').get('hits')
    num_pages = hits // 10

    # Fetch all the urls
    # Are limited to fetching in batches of 10
    returned_url_list = []
    for page in range(num_pages + 1):
        time.sleep(1)  # Can't make too many requests per second or the API gets mad
        results = requests.get(query_url+'&page='+str(page)).json()
        response = results.get('response')
        if response is not None:
           current_article_list = response.get('docs')
           for article in current_article_list:
                url = article.get('web_url')
                returned_url_list.append(url)

    if len(returned_url_list) == hits:
        # Remove some non-review articles returned by the API
        bad_words = ["(blog)", "(interactive)", "(wine-school)", "(insider)", "(hungry-city)", "(best)",
             "(/books/)", "(slideshow)", "(obituaries)", "(recipes)", "(reader-center)", "(technology)"]
        final_url_list = []
        for url in returned_url_list:
            if not re.search("|".join(bad_words), url):
                final_url_list.append(url)
        return(final_url_list)
    else:
        return('Problem getting URLS')


# NYT website has custom error page if it can't find the URL - this finds such pages so they can be re-downloaded
def find_server_error(bs):
    result = bs.find_all('meta', {'content': '500 - Server Error'})
    return(len(result) > 0)

# Remove some misclassified content - Critic's Notebook and Hungry City columns
def is_misclassified(bs):
    if len(bs.find_all('meta', {'content': re.compile('Critic.*Notebook')})) > 0 :
        return(True)
    if re.search('<p.*?>\s*[Cc]ritic.*[Nn]otebook\s*</p>', str(bs)):
        return(True)
    if len(bs.find_all('meta', {'content': 'hungry-city'})) > 0:
        return(True)
    return(False)


def get_reviews(to_fetch, n=10):
    """
    Downloads the reviews from NYT web page.

    urls is a list of the urls to retrieve. n is the max number of times to try to download a page

    Downloads each page and saves it as html. Also saves a list of the urls of
    every page. Does some parsing of the pages to remove non-review urls that still haven't been caught
    """
    final_url_list = []
    counter = 0
    os.makedirs('reviews', exist_ok=True)

    def get_from_list(url_list, final_url_list, counter):
        refetch_list = []
        for review_url in url_list:
            review = requests.get(review_url)
            parsed_review = BeautifulSoup(review.content, 'html.parser')
            if find_server_error(parsed_review):
                refetch_list.append(review_url)
            elif is_misclassified(parsed_review):
                continue
            else:
                with open('./reviews/review' + str(counter) + '.html', 'w') as newfile:
                    newfile.write(parsed_review.prettify())
                final_url_list.append(review_url)
                counter += 1
        return (refetch_list, final_url_list, counter)

    attempts = 0
    while (len(to_fetch) > 0) and (attempts <= n):
        to_fetch, final_url_list, counter = get_from_list(to_fetch, final_url_list, counter)
        attempts += 1

    if len(to_fetch) > 0:
        print("Could not successfully access the following reviews:")
        for url in to_fetch:
            print(url)

    with open('./reviews/url_list.txt', 'w') as url_output:
        json.dump(final_url_list, url_output)


if __name__ == '__main__':
    urls = get_urls()
    if urls == 'Problem getting URLS':
        print(urls)
        exit(1)
    print("Got URLS")
    if urls == '':
        print("Error retrieving URLs")
        exit(1)
    else:
        get_reviews(urls)