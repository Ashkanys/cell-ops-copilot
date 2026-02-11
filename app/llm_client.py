import os
import json
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Protocol, Optional


class LLM(Protocol):
    def generate(self, prompt: str) -> str: ...


@dataclass
class StubLLM:
    """Safe default: no generation, forces you to inspect sources."""
    def generate(self, prompt: str) -> str:
        return (
            "I’m running in **retrieve-only mode** (LLM not configured).\n\n"
            "Here are the most relevant SOP excerpts in the Sources panel.\n"
            "Configure an LLM provider to enable synthesized answers."
        )


@dataclass
class OllamaLLM:
    base_url: str = "http://localhost:11434"
    model: str = "qwen2.5:3b-instruct"
    temperature: float = 0.2
    timeout_s: int = 120

    def generate(self, prompt: str) -> str:
        url = f"{self.base_url.rstrip('/')}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,          # one JSON response (no streaming)
            "temperature": self.temperature,
        }
        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            url=url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Ollama HTTPError {e.code}: {detail}") from e
        except Exception as e:
            raise RuntimeError(
                "Failed to call Ollama. Is it running? Try: `ollama serve` and `ollama run <model>`."
            ) from e

        obj = json.loads(body)
        # Ollama returns {"response": "...", ...}
        return obj.get("response", "").strip()


def get_llm() -> LLM:
    """
    Select via env var:
      LLM_PROVIDER=stub | ollama

    Ollama env vars:
      OLLAMA_MODEL=qwen2.5:3b-instruct
      OLLAMA_BASE_URL=http://localhost:11434
      OLLAMA_TEMPERATURE=0.2
      OLLAMA_TIMEOUT_S=120
    """
    provider = os.getenv("LLM_PROVIDER", "stub").lower().strip()

    if provider == "stub":
        return StubLLM()

    if provider == "ollama":
        model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b-instruct").strip()
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()
        temperature = float(os.getenv("OLLAMA_TEMPERATURE", "0.2"))
        timeout_s = int(os.getenv("OLLAMA_TIMEOUT_S", "120"))
        return OllamaLLM(
            base_url=base_url,
            model=model,
            temperature=temperature,
            timeout_s=timeout_s,
        )

    raise RuntimeError(f"Unknown LLM_PROVIDER={provider}. Use LLM_PROVIDER=stub or LLM_PROVIDER=ollama.")
