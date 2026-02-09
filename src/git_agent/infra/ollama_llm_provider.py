from __future__ import annotations

import requests
from loguru import logger

from git_agent.domain.models import CodeReviewResult
from git_agent.domain.ports import LLMProvider


class OllamaLLMProvider(LLMProvider):
    def __init__(
        self, host: str = "http://localhost:11434", model: str = "qwen2.5-coder:7b"
    ):
        self.host = host.rstrip("/")
        self.model = model

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> str:
        url = f"{self.host}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "format": CodeReviewResult.model_json_schema(),
            "think": False,
            "options": {
                "temperature": temperature,
                "num_ctx": 16_384,
                "num_predict": max_tokens,
                "repeat_penalty": 1.1,
            },
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            r_json = result.get("response", "{}")

            logger.debug(r_json)
            return r_json
        except requests.exceptions.RequestException as e:
            logger.error(f"Network failure with Ollama: {e}")
            raise ConnectionError(f"Error connecting to Ollama: {e}") from None
        except (ValueError, KeyError) as e:
            logger.error(f"Invalid response from Ollama: {e}")
            raise ValueError(f"Error processing response: {e}") from e

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 4096
    ) -> str:
        url = f"{self.host}/api/chat"

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }

        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
        except requests.exceptions.RequestException as e:
            logger.error(f"Network failure with Ollama: {e}")
            raise ConnectionError(f"Error connecting to Ollama: {e}") from None
        except (ValueError, KeyError) as e:
            logger.error(f"Invalid response from Ollama: {e}")
            raise ValueError(f"Error processing response: {e}") from e

    def is_available(self) -> bool:
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def list_models(self) -> list[str]:
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            response.raise_for_status()

            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception:
            return []
