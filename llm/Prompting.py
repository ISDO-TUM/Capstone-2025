######-----DEPRECATED-----######
import base64
from langchain.schema import SystemMessage, HumanMessage
from llm.LLMDefinition import LLM


# for Multimodal ai usage
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def llm_call(systemMessage, humanMessage):
    # image = encode_image(image_path)
    # Getting the Base64 string
    messages = [
        SystemMessage(
            content=systemMessage),
        HumanMessage(
            content=humanMessage)
    ]

    try:
        response = LLM.invoke(messages)

    except Exception as e:
        print(f"Error during model invocation: {e}")
        return -1
    return response.content
