import os

import requests
import dateutil.parser
from datetime import datetime, timezone
import time
import urllib.parse
from dotenv import load_dotenv
import logging

load_dotenv()
api_key = os.getenv("CORE_API_KEY")
limit = 10
CORE_SEARCH_URL = os.getenv("CORE_SEARCH_URL", "https://api.core.ac.uk/v3/search/works")
logging.basicConfig(level=logging.INFO)

def query_api(search_url, query, scroll=False, scrollId=None):
    headers = {"Authorization": "Bearer " + api_key.strip()}

    if not scrollId and scroll:
        logging.info(f"{search_url}?q={query}&limit={limit}&scroll=true")
        response = requests.get(f"{search_url}?q={query}&exclude=fullText&limit={limit}&scroll=true", headers=headers)
    elif scroll and scrollId:
        logging.info(f"{search_url}?q={query}&limit={limit}&scrollId={scrollId}")
        response = requests.get(f"{search_url}?q={query}&exclude=fullText&limit={limit}&scrollId={scrollId}",
                                headers=headers)
    else:
        logging.info(f"{search_url}?q={query}&limit={limit}")
        response = requests.get(f"{search_url}?q={query}&exclude=fullText&limit={limit}", headers=headers, verify=False)
    logging.info(response.status_code)
    if response.status_code == 429:
        retryAfter = dateutil.parser.parse(response.headers['X-RateLimit-Retry-After'])
        now = datetime.now(timezone.utc)
        if retryAfter > now:
            sleepTime = retryAfter - now
            logging.info(f"Sleeping for {sleepTime.seconds + 1}")
            time.sleep(sleepTime.seconds + 1)
        return query_api(search_url, query, True, scrollId)
    if response.status_code > 499:
        logging.info(response.status_code)
        logging.info(response.content)
        logging.info("Sleeping for 5")
        time.sleep(5)
        return query_api(search_url, query, True, scrollId)
    return response.json(), response.elapsed.total_seconds()


def search_works(search_query):
    response, elapsed = query_api(CORE_SEARCH_URL,
                                  urllib.parse.quote(f"{search_query}"))
    search_results = []
    if "results" not in response:
        raise RuntimeError("Sorry, no results in CORE for your query.")
    logging.info(len(response["results"]))
    titles = []

    for hit in response["results"]:
        if hit["title"] not in titles:
            search_results.append({"url": f"https://core.ac.uk/works/{hit['id']}", "abstract": f"{hit['abstract'][:800]}", "title": hit["title"]})
            titles.append(hit["title"])
        if len(titles) >= 5:
            break

    return titles, search_results
