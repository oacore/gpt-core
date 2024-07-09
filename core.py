import os
import time
import urllib.parse
from datetime import datetime, timezone

import dateutil.parser
import requests

api_key = os.getenv("CORE_API_KEY")
limit = 10


def query_api(search_url, query, scroll=False, scroll_id=None):
    headers = {"Authorization": "Bearer " + api_key.strip()}

    if not scroll_id and scroll:
        print(f"{search_url}?q={query}&limit={limit}&scroll=true")
        response = requests.get(f"{search_url}?q={query}&exclude=fullText&limit={limit}&scroll=true", headers=headers)
    elif scroll and scroll_id:
        print(f"{search_url}?q={query}&limit={limit}&scrollId={scroll_id}")
        response = requests.get(f"{search_url}?q={query}&exclude=fullText&limit={limit}&scrollId={scroll_id}",
                                headers=headers)
    else:
        print(f"{search_url}?q={query}&limit={limit}")
        response = requests.get(f"{search_url}?q={query}&exclude=fullText&limit={limit}", headers=headers)
    print(response.status_code)
    if response.status_code == 429:
        retry_after = dateutil.parser.parse(response.headers['X-RateLimit-Retry-After'])
        now = datetime.now(timezone.utc)
        if retry_after > now:
            sleep_time = retry_after - now
            print(f"Sleeping for {sleep_time.seconds + 1}")
            time.sleep(sleep_time.seconds + 1)
        return query_api(search_url, query, True, scroll_id)
    if response.status_code > 499:
        print(response.status_code)
        print(response.content)
        print("Sleeping for 5")
        time.sleep(5)
        return query_api(search_url, query, True, scroll_id)
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
            search_results.append(
                {"url": f"https://core.ac.uk/works/{hit['id']}", "abstract": f"{hit['abstract'][:800]}",
                 "title": hit["title"], "authors": hit["authors"], "provenance": "global"})
            titles.append(hit["title"])
        if len(titles) >= 5:
            break

    return titles, search_results


def search_works_bydataprovider(search_query, data_provider_id):
    response, elapsed = query_api("https://api.core.ac.uk/v3/search/works",
                                  urllib.parse.quote(
                                      f"{search_query} and _exists_:description and dataProviders:{data_provider_id}"))
    search_results = []
    if "results" not in response:
        raise "Sorry, no results in CORE for your query."
    print(len(response["results"]))
    titles = []

    for hit in response["results"]:
        if hit["title"] not in titles:
            search_results.append(
                {"url": f"https://core.ac.uk/works/{hit['id']}", "abstract": f"{hit['abstract'][:800]}",
                 "title": hit["title"],
                 "authors": hit["authors"], "provenance": "local"})
            titles.append(hit["title"])
        if len(titles) >= 5:
            break

    return titles, search_results
