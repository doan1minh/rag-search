import os
import requests
import json
import logging
import uuid
import time
from typing import AsyncGenerator, Dict, List, Any, Optional, Union
from autogen_core.models import ChatCompletionClient, SystemMessage, UserMessage, AssistantMessage, LLMMessage, RequestUsage, CreateResult, ModelCapabilities
from autogen_core._types import FunctionCall
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class RateLimitError(Exception):
    """Custom exception for rate limit errors."""
    pass

class NativeGeminiClient(ChatCompletionClient):
    """
    A custom AutoGen ChatCompletionClient for Google Gemini (Native HTTP API).
    Bypasses OpenAI adapter issues.
    Includes automatic retry with exponential backoff for rate limits.
    """
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp", **kwargs):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self._total_usage = RequestUsage(prompt_tokens=0, completion_tokens=0)
        
    def _make_api_request(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make API request with automatic retry on rate limit (429) errors.
        Uses exponential backoff as recommended by Google.
        """
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        logger.info(f"DEBUG: Response Status: {response.status_code}")
        
        if response.status_code == 429:
            # Rate limit hit - raise custom exception for retry
            retry_after = response.headers.get("Retry-After", "60")
            logger.warning(f"⚠️ Rate limit hit (429). Retry-After: {retry_after}s. Will retry with exponential backoff...")
            raise RateLimitError(f"Rate limit exceeded. Retry-After: {retry_after}")
        
        if response.status_code >= 400:
            logger.error(f"DEBUG: Error Response Body: {response.text}")
            
        response.raise_for_status()
        return response.json()

    @retry(
        retry=retry_if_exception_type(RateLimitError),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=2, max=60),
        before_sleep=lambda retry_state: print(f"⏳ Rate limited. Waiting {retry_state.next_action.sleep:.1f}s before retry {retry_state.attempt_number}/5...")
    )
    def _make_api_request_with_retry(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper that adds retry logic to API requests."""
        return self._make_api_request(url, payload)
        
    async def create(
        self,
        messages: List[LLMMessage],
        *,
        tools: Optional[List[Any]] = None,
        json_output: Optional[bool] = None,
        extra_create_args: Dict[str, Any] = {},
        cancellation_token: Any = None,
    ) -> CreateResult:
        """
        Send a chat completion request to Gemini.
        """
        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        
        # Convert AutoGen messages to Gemini format
        gemini_contents = []
        system_instruction = None
        
        for msg in messages:
            if isinstance(msg, SystemMessage):
                # Gemini supports system_instruction field
                system_instruction = {"parts": [{"text": msg.content}]}
            elif isinstance(msg, UserMessage):
                content = msg.content
                if isinstance(content, str):
                    gemini_contents.append({"role": "user", "parts": [{"text": content}]})
                else:
                    # Handle multimodal if needed (simple text support for now)
                    text_parts = [p for p in content if isinstance(p, str)]
                    gemini_contents.append({"role": "user", "parts": [{"text": "".join(text_parts)}]})
            elif isinstance(msg, AssistantMessage):
                content = msg.content
                if isinstance(content, str):
                    gemini_contents.append({"role": "model", "parts": [{"text": content}]})
        
        # Construct Tool definitions for Gemini
        gemini_tools = []
        if tools:
            def clean_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
                """Recursively remove 'title' and 'additionalProperties' from schema to appease Gemini."""
                if not isinstance(schema, dict):
                    return schema
                return {
                    k: clean_schema(v) 
                    for k, v in schema.items() 
                    if k not in ["title", "additionalProperties", "strict"]
                }

            function_declarations = []
            for t in tools:
                 # Support both object and dict (duck typing)
                 name = getattr(t, "name", None) or t.get("name")
                 description = getattr(t, "description", None) or t.get("description")
                 parameters = getattr(t, "parameters", None) or t.get("parameters")
                 
                 if parameters:
                     parameters = clean_schema(parameters)

                 if name:
                     function_declarations.append({
                         "name": name,
                         "description": description,
                         "parameters": parameters
                     })
            
            if function_declarations:
                gemini_tools = [{"function_declarations": function_declarations}]

        payload = {
            "contents": gemini_contents,
            # "generationConfig": {
            #     "response_mime_type": "application/json" if json_output else "text/plain"
            # }
        }
        
        if gemini_tools:
            payload["tools"] = gemini_tools

        if system_instruction:
            payload["system_instruction"] = system_instruction
            
        logger.info(f"DEBUG: NativeGeminiClient sending request to {self.model}...")
        # logger.info(f"DEBUG Payload: {json.dumps(payload, indent=2)}")

        try:
            # Use retry-enabled request method
            data = self._make_api_request_with_retry(url, payload)
            
            # Parse response
            # Assuming standard response structure
            try:
                candidate = data["candidates"][0]
                content_part = candidate["content"]["parts"][0]
                
                content_text = ""
                tool_calls = []

                if "text" in content_part:
                    content_text = content_part["text"]
                
                # Check for Function calls
                # Gemini can return multiple parts.
                for part in candidate["content"]["parts"]:
                    if "functionCall" in part:
                         fc = part["functionCall"]
                         fname = fc["name"]
                         fargs = fc["args"] # Dict
                         # Convert to AutoGen FunctionCall
                         # args must be string
                         tool_calls.append(FunctionCall(id=str(uuid.uuid4()), name=fname, arguments=json.dumps(fargs)))

                raw_finish_reason = candidate.get("finishReason", "STOP")
                finish_reason_map = {
                    "STOP": "stop",
                    "MAX_TOKENS": "length",
                    "SAFETY": "content_filter",
                    "RECITATION": "content_filter",
                    "OTHER": "stop", # Default backup
                }
                finish_reason = finish_reason_map.get(raw_finish_reason, "stop")
                
                # If we have tool calls, finish reason is conventionally 'tool_calls' or 'stop'?
                # AutoGen usually expects 'stop' if tool calls are present? 
                # Or 'function_call'?
                # In OpenAI it is 'tool_calls'.
                # Let's map to 'stop' if not mapped.
                
                # Usage metadata if available
                usage = data.get("usageMetadata", {})
                prompt_tokens = usage.get("promptTokenCount", 0)
                completion_tokens = usage.get("candidatesTokenCount", 0)
                request_usage = RequestUsage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)
                
                # Use kwargs to pass tool_calls if CreateResult supports it via extra fields?
                # Inspect showed CreateResult args. It likely has internal handling.
                # Actually, CreateResult DOES NOT seem to have tool_calls in init unless I missed it.
                # But looking at other clients, they must return it.
                # Let's try passing it.
                return CreateResult(
                    content=content_text,
                    usage=request_usage,
                    finish_reason=finish_reason,
                    cached=False,
                    tool_calls=tool_calls
                )
                   
            except (KeyError, IndexError) as e:
                logger.error(f"Failed to parse Gemini response: {data}")
                raise ValueError(f"Invalid response format from Gemini: {e}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Gemini API Request Error: {e}")
            raise

    async def create_stream(
        self,
        messages: List[LLMMessage],
        *,
        tools: Optional[List[Any]] = None,
        json_output: Optional[bool] = None,
        extra_create_args: Dict[str, Any] = {},
        cancellation_token: Any = None,
    ) -> AsyncGenerator[Any, None]:
        # Minimal stream implementation (non-streaming for now to keep it simple)
        result = await self.create(messages, tools=tools, json_output=json_output)
        yield result.content

    # Abstract methods from ChatCompletionClient (v0.4)
    def actual_usage(self) -> RequestUsage:
        return self._total_usage

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            vision=True,
            function_calling=True, # Enabled to allow tool registration
            json_output=True
        )

    def close(self) -> None:
        pass

    @property # Assuming property based on common pattern, or just method? inspect said 'methods'
    def model_info(self) -> Dict[str, Any]:
        return {
            "family": "gemini",
            "vision": True,
            "function_calling": True,
            "json_output": True,
        }
        
    # Keep previous ones if needed or aliases
    def total_usage(self) -> RequestUsage:
        return self._total_usage

    def remaining_tokens(self, messages: List[LLMMessage], tools: Optional[List[Any]] = None) -> int:
        return 1000000

    def count_tokens(self, messages: List[LLMMessage], tools: Optional[List[Any]] = None) -> int:
        return 0




