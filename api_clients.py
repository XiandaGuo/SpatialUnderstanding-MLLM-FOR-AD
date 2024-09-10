from openai import OpenAI
import os
import io
import base64
import google.generativeai as genai
from PIL import Image
from typing import List


def pil2base64(pil_image: Image.Image) -> str:
    """
    Converts a PIL image object to a base64-encoded string.

    Parameters:
    pil_image (PIL.Image.Image): The image to be converted to base64.

    Returns:
    str: The base64-encoded string representation of the image.
    """
    try:
        binary_stream = io.BytesIO()
        pil_image.save(binary_stream, format="PNG")
        binary_data = binary_stream.getvalue()
        return base64.b64encode(binary_data).decode('utf-8')
    except Exception as e:
        raise RuntimeError(f"Failed to convert image to base64: {e}")


def get_openai_output(pil_image: Image.Image, prompt: str, model: str, max_tokens: int = 300) -> str:
    """
    Generates a response from OpenAI API using a prompt and a PIL image.

    Parameters:
    pil_image (PIL.Image.Image): The image to be processed and sent to the OpenAI API.
    prompt (str): The text prompt to send along with the image.
    model (str): The OpenAI model to use for generating the response.
    max_tokens (int, optional): The maximum number of tokens for the response. Defaults to 300.

    Returns:
    str: The response generated by the OpenAI API.

    Raises:
    EnvironmentError: If the OpenAI API key is not found in environment variables.
    LookupError: If the specified model is not supported by the OpenAI API.
    RuntimeError: If the API request fails or there is an issue with the response.
    """
    # Get the API key from environment variables
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise EnvironmentError("OpenAI API key is missing. Set 'OPENAI_API_KEY' in environment variables.")

    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)

        # Fetch the list of supported models from the OpenAI API
        supported_models: List[str] = [model_info.id for model_info in client.models.list().data]

        # Validate if the provided model is supported
        if model not in supported_models:
            raise LookupError(f"Model '{model}' is not supported. Available models: {supported_models}")

        # Convert the PIL image to a base64-encoded string
        image_base64 = pil2base64(pil_image)
        image_url = f"data:image/jpeg;base64,{image_base64}"

        # Call the OpenAI API
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url},
                        },
                    ],
                }
            ],
            max_tokens=max_tokens,
        )

        # Extract and return the output from the API response
        output = response.choices[0].message.content
        return output

    except LookupError as e:
        raise e

    except Exception as e:
        raise RuntimeError(f"Failed to generate OpenAI output: {e}")


def get_gemini_output(pil_image: Image.Image, prompt: str, model: str) -> str:
    """
    Generates a response from Google's Gemini API using a prompt and a PIL image.

    Parameters:
    pil_image (PIL.Image.Image): The image to be processed and sent to the Gemini API.
    prompt (str): The text prompt to send along with the image.
    model (str): The Gemini model to use for generating the response.

    Returns:
    str: The response generated by the Gemini API.

    Raises:
    EnvironmentError: If the Google API key is not found in environment variables.
    LookupError: If the specified model is not supported by Gemini. The exception
                 includes a message listing the available models.
    RuntimeError: If the API request fails or there is an issue with the response.
    """
    # Retrieve the Google API key from environment variables
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        raise EnvironmentError("Google API key is missing. Set 'GOOGLE_API_KEY' in environment variables.")

    try:
        # Configure the Gemini API client with the retrieved API key
        genai.configure(api_key=api_key, transport='rest')

        # Fetch the list of supported models from the Gemini API
        supported_models = [model_info.name for model_info in genai.list_models()]

        # Validate if the provided model is supported
        if model not in supported_models:
            raise LookupError(f"Model '{model}' is not supported. Available models: {supported_models}")

        # Create a generative model instance
        generative_model = genai.GenerativeModel(model_name=model)

        # Generate content using the model, prompt, and image
        output = generative_model.generate_content([prompt, pil_image]).text

        return output

    except LookupError as e:
        raise e

    except Exception as e:
        raise RuntimeError(f"Failed to generate Gemini output: {e}")
