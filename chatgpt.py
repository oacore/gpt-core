import os

import json
from langchain_community.chat_models import BedrockChat

model_kwargs = {  # AI21
    "maxTokens": 4096
}

llm = BedrockChat(  # create a Bedrock llm client
    model_id="anthropic.claude-3-sonnet-20240229-v1:0"  # set the foundation model
)

llm.model_kwargs = {
    'max_tokens': 16000,
}


def generate_search_query(input_request):
    messages = [
        {"role": "user", "content": "Generate a search engine query for a research paper based on the question. "
                                    "Prioritise the most important keywords and add synonyms to focus the search. "
                                    "Ensure that the response contain only the query and no other extra text"
                                    "The answer should be no longer than "
                                    "80 words."},
        {"role": "assistant", "content": f"{input_request}"},
    ]

    response = llm.invoke(messages)
    print("results")
    response_body = response.content.replace("\n", "").replace("\"", " ")
    return response_body


def generate_answer(input_request, search_results):
    global final_answer
    messages = [
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
        {"role": "assistant", "content": f"{input_request}"},
        {"role": "user", "content": f"{json.dumps(search_results)}"}
    ]

    response = llm.invoke(messages)  # return a response to the prompt
    response_body = response.content

    return response_body


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

    response = llm.invoke(messages)  # return a response to the prompt
    response_body = response.content

    return response_body
