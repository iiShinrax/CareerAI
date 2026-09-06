"""Web-safe adapter for Jamal's local Qwen/Llama-cpp interviewer.

The model is loaded only on the first request.  Configure ``LLM_MODEL_PATH``
to the GGUF model file; requests fail clearly when it is not configured rather
than fabricating an answer.
"""

import json
import os
from threading import Lock
from functools import lru_cache


class LLMUnavailable(RuntimeError):
    pass


_inference_lock = Lock()


@lru_cache(maxsize=1)
def _model():
    model_path = os.getenv("LLM_MODEL_PATH")
    if not model_path:
        raise LLMUnavailable("LLM_MODEL_PATH is not configured")
    if not os.path.isfile(model_path):
        raise LLMUnavailable("The configured LLM model file was not found")
    try:
        from llama_cpp import Llama
        return Llama(
            model_path=model_path,
            n_ctx=int(os.getenv("LLM_CONTEXT_SIZE", "4096")),
            n_threads=int(os.getenv("LLM_THREADS", "4")),
            verbose=False,
        )
    except Exception as exc:
        raise LLMUnavailable(f"The local LLM could not be started: {exc}") from exc


def complete(system: str, prompt: str, *, temperature: float = 0.3, max_tokens: int = 500) -> str:
    with _inference_lock:
        for attempt in range(2):
            try:
                response = _model().create_chat_completion(
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                break
            except (OSError, RuntimeError) as exc:
                if attempt == 0:
                    _model.cache_clear()
                    continue
                raise LLMUnavailable(f"The local LLM failed during inference: {exc}") from exc
    return response["choices"][0]["message"]["content"].strip()


def json_completion(system: str, prompt: str, *, max_tokens: int = 800):
    raw = complete(system, prompt, temperature=0.1, max_tokens=max_tokens)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        start = raw.find("{")
        if start < 0:
            raise ValueError("The local LLM returned invalid JSON") from exc
        try:
            result, _ = json.JSONDecoder().raw_decode(raw[start:])
            return result
        except json.JSONDecodeError as nested_exc:
            raise ValueError("The local LLM returned invalid JSON") from nested_exc
