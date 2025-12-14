import os
from dotenv import load_dotenv, find_dotenv
from typing import Union
from autogen_ext.models.openai import OpenAIChatCompletionClient
from src.native_gemini_client import NativeGeminiClient

# Ensure env is loaded
load_dotenv(find_dotenv(), override=True)

def get_model_client() -> Union[OpenAIChatCompletionClient, NativeGeminiClient]:
    api_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    
    # Check if OPENAI_API_KEY is a placeholder
    if api_key and (api_key.startswith("sk-...") or api_key == "sk-..."):
        api_key = None
    
    # If no valid OpenAI key but we have Gemini key, use Native Client
    if not api_key and gemini_key:
        print("DEBUG: Using Native Gemini Client (2.0 Flash Exp)")
        return NativeGeminiClient(api_key=gemini_key)
    
    if not api_key:
        raise ValueError("No valid API Key found (OPENAI_API_KEY or GEMINI_API_KEY)")

    return OpenAIChatCompletionClient(
        model="gpt-4o-mini",
        api_key=api_key,
        base_url=base_url,
        temperature=0,
    )
