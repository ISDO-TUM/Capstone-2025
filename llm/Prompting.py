import base64
from langchain_core.messages import HumanMessage, SystemMessage
import llm


#for Multimodal ai usage
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def multimodal_call(ai_input, image_path):

    image = encode_image(image_path)
    # Getting the Base64 string
    message = [
        SystemMessage(
            content="You are a helpful assistant!"
        ),

        HumanMessage(
            content=[
            {"type": "text", "text": ai_input},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image}"}},
            ],
        )
    ]

    try:
        response = llm.LLMDefinition.LLM.invoke([message])


    except Exception as e:
        print(f"Error during model invocation: {e}")
        return -1
    return response.content