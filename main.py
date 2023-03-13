import openai
import requests
import time
import urllib.parse
import json

import dateutil.parser
from datetime import datetime, timezone

***REMOVED***

api_key = "***REMOVED***"
total = 0
limit = 5


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


if __name__ == "__main__":
    input_request = "Can you give me a critical comparison for alternatives to OAI-PMH for scholarly research outputs?"

    messages = [
        {"role": "system", "content": "Generate a search engine query for a research paper based on the question. "
                                      "Prioritise the most important keywords and add synonyms to focus the search. "
                                      "The answer should be no longer than "
                                      "80 words."},
        {"role": "user", "content": f"{input_request}"},
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    search_query = response["choices"][0]["message"]["content"].replace("\"", "")
    print(f"Searching core with: {search_query}")

    response, elapsed = query_api("https://api.core.ac.uk/v3/search/works",
                                  urllib.parse.quote(f"{search_query} and _exists_:description"))
    answers = []
    if "results" not in response:
        exit();
    print(len(response["results"]))
    for hit in response["results"]:
        answers.append({"url": f"https://core.ac.uk/works/{hit['id']}", "abstract": f"{hit['abstract']}"})
    if len(answers) == 0:
        exit()
    messages = [
        {"role": "system", "content": "Generate a comprehensive answer (but no more than 80 words) "
                                      "for a given question solely based on the provided search results in the format: "
                                      "{url:$url, abstract:$abstract}. "
                                      "You must only use information from the provided search results."
                                      "Use an unbiased and journalistic tone. Combine search results together "
                                      "into a coherent answer. "
                                      "Do not repeat text. Cite search results using the url provided and the [$n] "
                                      "notation. Only "
                                      "cite the most relevant result that answer the question "
                                      "accurately. If different results refer to different entities with the same "
                                      "name, write separate answers for each entity."},
        {"role": "user", "content": f"{input_request}"},
        {"role": "assistant", "content": f"{json.dumps(answers)}"}
    ]
    print(messages)
    finalResponse = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    final_answer = finalResponse["choices"][0]["message"]["content"]
    count = 1
    references = ""
    for a in answers:
        references += f"\n {count}. {a['url']} \n"
        count += 1

    print(final_answer + references)
