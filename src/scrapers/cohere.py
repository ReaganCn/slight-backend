import os
from langchain_cohere import ChatCohere
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate


def get_cohere_client():
    return ChatCohere(
        model="command-r-08-2024",
        api_key=os.getenv("COHERE_API_KEY"),
    )

def get_cohere_prompt(html_content: str, format: str):
    return ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that helps in scraping pricing and features from a website."),
        ("user", "Please scrape the pricing and features from the following html content: {html_content}"),
        ("user", "Return the pricing and features in the following JSON format. Do not include any other text or comments. If the currecy does not exist, use null. But you can use the currency symbol from the html content: {format}"),
    ])

def get_pricing_and_features_with_cohere(html_content: str):
    client = get_cohere_client()
    format = """
    [
    {
        \"plan\": \"Hobby\",
        \"currency\": \"$\",
        \"price\": {
            \"monthly\": 0,
            \"yearly\": 0
        },
        \"features\": [
            \"Pro two-week trial\",
            \"Limited agent requests\",
            \"Limited tab completions\"
        ]
    },
    ]
    """
    prompt = get_cohere_prompt(html_content, format)
    formatted_prompt = prompt.format_prompt(html_content=html_content, format=format)
    messages = formatted_prompt.to_messages()
    response = client.invoke(messages)
    return response.content