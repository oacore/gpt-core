import requests

import dateutil.parser
from datetime import datetime, timezone
import requests
import time
import urllib.parse

api_key = "***REMOVED***"
limit = 10


def query_api(search_url, query, scroll=False, scrollId=None):
    headers = {"Authorization": "Bearer " + api_key.strip()}

    if not scrollId and scroll:
        print(f"{search_url}?q={query}&limit={limit}&scroll=true")
        response = requests.get(f"{search_url}?q={query}&exclude=fullText&limit={limit}&scroll=true", headers=headers)
    elif scroll and scrollId:
        print(f"{search_url}?q={query}&limit={limit}&scrollId={scrollId}")
        response = requests.get(f"{search_url}?q={query}&exclude=fullText&limit={limit}&scrollId={scrollId}",
                                headers=headers)
    else:
        print(f"{search_url}?q={query}&limit={limit}")
        response = requests.get(f"{search_url}?q={query}&exclude=fullText&limit={limit}", headers=headers)
    print(response.status_code)
    if response.status_code == 429:
        retryAfter = dateutil.parser.parse(response.headers['X-RateLimit-Retry-After'])
        now = datetime.now(timezone.utc)
        if retryAfter > now:
            sleepTime = retryAfter - now
            print(f"Sleeping for {sleepTime.seconds + 1}")
            time.sleep(sleepTime.seconds + 1)
        return query_api(search_url, query, True, scrollId)
    if response.status_code > 499:
        print(response.status_code)
        print(response.content)
        print("Sleeping for 5")
        time.sleep(5)
        return query_api(search_url, query, True, scrollId)
    return response.json(), response.elapsed.total_seconds()


def search_works(search_query):
    response, elapsed = query_api("https://api.core.ac.uk/v3/search/works",
                                  urllib.parse.quote(f"{search_query} and _exists_:description"))
    search_results = []
    if "results" not in response:
        raise "Sorry, no results in CORE for your query."
    print(len(response["results"]))
    titles = []

    for hit in response["results"]:
        if hit["title"] not in titles:
            searsdch_results.append({"url": f"https://core.ac.uk/works/{hit['id']}", "abstract": f"{hit['abstract'][:800]}"})
            titles.append(hit["title"])
        if len(titles) >= 5:
            break

    return titles, search_results
