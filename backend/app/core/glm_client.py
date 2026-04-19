# app/core/glm_client.py
import httpx
import asyncio
from typing import Dict, Any, Optional
from app.core.config import settings

class GLMClient:
    def __init__(self):
        self.api_key = settings.GLM_API_KEY
        self.base_url = settings.GLM_BASE_URL
        self.text_model = settings.GLM_TEXT_MODEL
        self.vision_model = settings.GLM_VISION_MODEL

    async def _request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/{endpoint}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def chat_completion(self, messages: list, model: str = None, response_format: Optional[str] = None) -> str:
        model = model or self.text_model
        payload = {
            "model": model,
            "messages": messages,
        }
        if response_format == "json_object":
            payload["response_format"] = {"type": "json_object"}
        result = await self._request("chat/completions", payload)
        return result["choices"][0]["message"]["content"]


    async def vision_completion(self, image_url: str, prompt: str) -> str:
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ]
        return await self.chat_completion(messages, model=self.vision_model)

glm_client = GLMClient()