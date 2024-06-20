import os
import openai
import json

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_API_BASE = "https://lxt-aimwa-openai-dev-us.openai.azure.com/"
AZURE_OPENAI_API_VERSION = "2023-05-15"

openai.api_type = "azure"

openai.api_version = AZURE_OPENAI_API_VERSION

openai.azure_endpoint = AZURE_OPENAI_API_BASE

openai.api_key = AZURE_OPENAI_API_KEY
# ou key for gpt 4
engine = "lxt-aimwa-dev-gpt4-us"


def generate_search_query(input_request):
    messages = [
        {"role": "system", "content": "You are a helpful search assistant that can provide information."},
        {"role": "user", "content": "Generate a search engine query for a research paper based on the question. "
                                    "Prioritise the most important keywords and add synonyms to focus the search. "
                                    "Ensure that the response contain only the query and no other extra text"
                                    "The answer should be no longer than "
                                    "80 words."},
        {"role": "user", "content": f"{input_request}"},
    ]
    response = openai.chat.completions.create(
        messages=messages,
        model=engine

    )
    return response.choices[0].message.content.replace("\"", "").replace(":", "")


def generate_answer(input_request, search_results):
    global final_answer
    messages = [
        {"role": "system", "content": "You are a helpful search assistant that can provide information."},
        {"role": "user", "content": "Generate a comprehensive answer (but no more than 160 words) "
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
    finalResponse = openai.chat.completions.create(
        messages=messages,
        model=engine

    )
    return finalResponse.choices[0].message.content


def generate_local_answer(input_request, search_results):
    messages = [
        {"role": "user", "content": "You are an assistant helping the research office understands what research "
                                    "has been done for the topic in the query"
                                    "Generate a comprehensive overview of the research in the institution "
                                    "for a given question solely based on the provided search results in the format: "
                                    "{url:$url, abstract:$abstract, authors:$authors}. "
                                    "The search results are coming from a single institution, "
                                    "The user asking the question is coming from the same institution so the answer "
                                    "need to be phrased on what is the best way that internal research can be used to "
                                    "answer the question, "
                                    "Please mention at the start that the results are coming from the institution of "
                                    "the user "
                                    "You must only use information from the provided search results, please use also "
                                    "the authors surname in the answer "
                                    "You must only use information from the provided search results. "
                                    "Use an unbiased and journalistic tone. Combine search results together "
                                    "into a coherent answer. "
                                    "Do not repeat text. Cite search results using the url provided and the [N] "
                                    "notation. Only "
                                    "cite the most relevant result that answer the question "
                                    "accurately. If different results refer to different entities with the same "
                                    "name, write separate answers for each entity."},
        {"role": "assistant", "content": f"{input_request}"},
        {"role": "user", "content": f"{json.dumps(search_results)}"}
    ]
    print(messages)
    finalResponse = openai.chat.completions.create(
        messages=messages,
        model=engine

    )
    return finalResponse.choices[0].message.content


def generate_overall_answer(input_request, search_results):
    messages = [
        {"role": "user", "content": "Generate a comprehensive summary (but no more than 300 words) "
                                    "with a comparison between local and global results (but no more than 160 words) "
                                    "for a given question solely based on the provided search results in the format: "
                                    "{url:$url, abstract:$abstract, authors:$authors, provenance:$provenance}. "
                                    "The results with local provenance are coming from the user institution, "
                                    "The answer should take the provenance into account and highlight more the local "
                                    "results "
                                    "please mention the provenance when describing the results"
                                    "please emphasise the provenance of each result in your text, if the citation is "
                                    "for a local paper you must mention it "
                                    "You must only use information from the provided search results, please use also "
                                    "the authors surname in the answer "
                                    "Use an unbiased and journalistic tone. Combine search results together "
                                    "into a coherent answer. "
                                    "Do not repeat text. Cite search results using the authors names provided, the [N] "
                                    "notation and the $provenance variable. Only "
                                    "cite that answer the question based on relevancy and provenance"
                                    "accurately. If different results refer to different entities with the same "
                                    "name, write separate answers for each entity."},
        {"role": "assistant", "content": f"{input_request}"},
        {"role": "user", "content": f"{json.dumps(search_results)}"}
    ]
    print(messages)
    finalResponse = openai.chat.completions.create(
        messages=messages,
        model=engine

    )
    return finalResponse.choices[0].message.content


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
    finalResponse = openai.chat.completions.create(
        messages=messages,
        model=engine

    )
    return finalResponse.choices[0].message.content
