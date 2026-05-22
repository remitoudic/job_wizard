from langchain_openai import ChatOpenAI

try:
    llm = ChatOpenAI(api_key="real_key", model="llama3-8b-8192")
    print("SUCCESS with api_key")
except Exception as e:
    print("FAILED with api_key:", type(e), e)

try:
    llm = ChatOpenAI(openai_api_key="real_key", model="llama3-8b-8192")
    print("SUCCESS with openai_api_key")
except Exception as e:
    print("FAILED with openai_api_key:", type(e), e)
