from chatgpt import *
from core import *
import re
from flask import *
import urllib.parse
import os
from flask import request

app = Flask(__name__, template_folder="templates", static_folder="static")


def replace_url_to_link(value):
    # Replace url to link
    urls = re.compile(r"((https?):((//)|(\\\\))+[\w\d:#@%/;$()~_?\+-=\\\.&]*)", re.MULTILINE | re.UNICODE)
    value = urls.sub(r'<a href="\1" target="_blank">\1</a>', value)
    # Replace email to mailto
    urls = re.compile(r"([\w\-\.]+@(\w[\w\-]+\.)+[\w\-]+)", re.MULTILINE | re.UNICODE)
    value = urls.sub(r'<a href="mailto:\1">\1</a>', value)
    return value


def clearup_response(answer, search_results):
    cleared_answer = re.sub("\[\$(\d+)", "[\1]", answer)
    print(answer)
    url_matched = re.findall("\[[url:]?(https://core.ac.uk/works/\d+)\]", answer)
    print(url_matched)
    if url_matched:
        count = 1
        for result in search_results:
            print(result)
            if result['url'] in url_matched:
                cleared_answer = cleared_answer.replace(f"[{result['url']}]", f"[{count}]")
        count += 1
    return cleared_answer


def render_response(answer, search_results, titles, search_query):
    i = 0
    references = "<ol>"
    search_query_for_web = urllib.parse.quote(f"{search_query} and _exists_:description")
    for a in search_results:
        references += f" <li> {a['url']} - {titles[i]}</li>"
        i += 1
    references += "</ol>"
    core_link = f"<br><a href='https://core.ac.uk/search?q={search_query_for_web}'>See more in CORE</a>"
    return replace_url_to_link(clearup_response(answer, search_results)) + replace_url_to_link(references) + core_link


def render_local_response(answer, search_results, titles, search_query):
    i = 0
    references = "<ol>"
    search_query_for_web = urllib.parse.quote(f"{search_query} and _exists_:description")
    for a in search_results:
        references += f" <li> {a['url']} - {titles[i]}</li>"
        i += 1
    references += "</ol>"
    core_link = f"<br><a href='https://core.ac.uk/search?q={search_query_for_web}'>See more in CORE</a>"
    return replace_url_to_link(clearup_response(answer, search_results)) + replace_url_to_link(references) + core_link


def render_json_response(answer, search_results, titles, search_query):
    i = 1
    references = {}
    search_query_for_web = urllib.parse.quote(f"{search_query} and _exists_:description")
    for a in search_results:
        references[i] = a
        i += 1
    core_link = f"https://core.ac.uk/search?q={search_query_for_web}"
    answer = clearup_response(answer, search_results)

    return {
        "answer": answer,
        "results": references,
        "see_more": core_link
    }


def run(input_request):
    search_query = generate_search_query(input_request)
    print(f"Searching core with: {search_query}")

    titles, search_results = search_works(search_query)

    if len(search_results) == 0:
        return "Not enough CORE results"

    answer = generate_answer(input_request, search_results)
    accept_header = request.headers.get('Accept')
    if accept_header and "json" in accept_header:
        return render_json_response(answer, search_results, titles, search_query)
    return render_response(answer, search_results, titles, search_query)


def runRepo(input_request, dataProviderId):
    search_query = generate_search_query(input_request)
    print(f"Searching core with: {search_query} for {dataProviderId}")

    local_titles, local_search_results = search_works_bydataprovider(search_query, dataProviderId)

    if len(local_search_results) == 0:
        print("Not enough local results")

    titles, search_results = search_works(search_query)

    if len(search_results) == 0:
        return "Not enough CORE results"

    answer = generate_answer(input_request, search_results)
    local_answer = generate_local_answer(input_request, local_search_results)

    overall_answer = generate_overall_answer(input_request, search_results + local_search_results)
    return "LOCAL:<br>" + render_local_response(local_answer, local_search_results, local_titles, search_query) \
           + "<br> GLOBAL <BR>" + render_response(answer, search_results, titles, search_query) \
           + "<br> OVERALL: <br>" + render_response(overall_answer, search_results + local_search_results, local_titles+titles, search_query)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/ask")
def ask():
    q = request.args.get("q")
    answer = run(q)
    return answer


@app.route("/askLocal")
def askLocal():
    q = request.args.get("q")
    dataProvider = request.args.get("repo")
    answer = runRepo(q, dataProvider)
    return answer


if __name__ == "__main__":
    if os.getenv("debug"):
        app.run(debug=True)
    else:
        from waitress import serve

        serve(app, host="0.0.0.0", port=5005)
