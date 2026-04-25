# app/core/glm_client.py

import httpx
from typing import Dict, Any, Optional

from google import genai
from google.genai import types

from app.core.config import settings


class GLMClient:
    def __init__(self):
        # ILMU / GLM text config
        self.api_key = settings.GLM_API_KEY
        self.base_url = settings.GLM_BASE_URL
        self.text_model = settings.GLM_TEXT_MODEL

        # Gemini vision config
        self.gemini_api_key = settings.GEMINI_API_KEY
        self.gemini_vision_model = settings.GEMINI_VISION_MODEL

        self.gemini_client = genai.Client(api_key=self.gemini_api_key)

    async def _request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/{endpoint}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    async def chat_completion(
        self,
        messages: list,
        model: str = None,
        response_format: Optional[str] = None,
    ) -> str:
        """
        Text processing remains on ILMU / GLM.
        """
        model = model or self.text_model

        payload = {
            "model": model,
            "messages": messages,
        }

        if response_format == "json_object":
            payload["response_format"] = {"type": "json_object"}

        result = await self._request("chat/completions", payload)
        return result["choices"][0]["message"]["content"]

    async def vision_completion(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt: str,
    ) -> str:
        """
        Image processing uses Gemini only.
        """

        response = self.gemini_client.models.generate_content(
            model=self.gemini_vision_model,
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type,
                ),
                prompt,
            ],
        )

        return response.text


glm_client = GLMClient()