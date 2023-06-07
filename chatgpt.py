import openai
import json

AZURE_OPENAI_API_KEY="***REMOVED***"
AZURE_OPENAI_API_BASE="https://lxt-aimwa-openai-dev-us.openai.azure.com/"
AZURE_OPENAI_API_VERSION="2023-05-15"

#***REMOVED***

openai.api_type="azure"

openai.api_version=AZURE_OPENAI_API_VERSION

openai.api_base=AZURE_OPENAI_API_BASE

openai.api_key=AZURE_OPENAI_API_KEY
#ou key for gpt 4
#***REMOVED***
engine = "lxt-aimwa-dev-gpt4-us"
def generate_search_query(input_request):
    messages = [
        {"role": "system", "content": "Generate a search engine query for a research paper based on the question. "
                                      "Prioritise the most important keywords and add synonyms to focus the search. "
                                      "Ensure that the response contain only the query and no other extra text"
                                      "The answer should be no longer than "
                                      "80 words."},
        {"role": "user", "content": f"{input_request}"},
    ]
    response = openai.ChatCompletion.create(
        messages=messages,
        engine=engine

    )
    return response["choices"][0]["message"]["content"].replace("\"", "").replace(":", "")


def generate_answer(input_request, search_results):
    global final_answer
    messages = [
        {"role": "system", "content": "Generate a comprehensive answer (but no more than 160 words) "
                                      "for a given question solely based on the provided search results in the format: "
                                      "{url:$url, abstract:$abstract}. "
                                      "You must only use information from the provided search results."
                                      "Use an unbiased and journalistic tone. Combine search results together "
                                      "into a coherent answer. "
                                      "Do not repeat text. Cite search results using the url provided and the [N] "
                                      "notation. Only "
                                      "cite the most relevant result that answer the question "
                                      "accurately. If different results refer to different entities with the same "
                                      "name, write separate answers for each entity."},
        {"role": "user", "content": f"{input_request}"},
        {"role": "assistant", "content": f"{json.dumps(search_results)}"}
    ]



    print(messages)
    finalResponse = openai.ChatCompletion.create(
        engine=engine,
        messages=messages
    )
    return finalResponse["choices"][0]["message"]["content"]

def generate_course_material(input_request, search_results):
    global final_answer
    messages = [
        {"role": "system", "content": "Generate a comprehensive course reading list for undergraduate students"
                                      "for a given topic solely based on the provided search results in the format: "
                                      "{url:$url, abstract:$abstract}. "
                                      "You must only use information from the provided search results."
                                      "Use an unbiased and journalistic tone. Combine search results together "
                                      "into a coherent course material. "
                                      "Do not repeat text. Cite search results using the url provided and the [N] "
                                      "notation. Only "
                                      "cite the most relevant result that answer the question "
                                      "accurately. If different results refer to different entities with the same "
                                      "name, write separate answers for each entity."},
        {"role": "user", "content": f"{input_request}"},
        {"role": "assistant", "content": f"{json.dumps(search_results)}"}
    ]

    print(messages)
    finalResponse = openai.ChatCompletion.create(
        engine=engine,
        messages=messages
    )
    return finalResponse["choices"][0]["message"]["content"]