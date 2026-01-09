"""
텍스트 입력을 영어로 번역 (다국어 입력 대응, 로컬 모델 전용)
"""
from __future__ import annotations

import json
import os
from typing import Optional, Tuple

import langid
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch


class TranslationService:
    """다국어 -> 영어 번역 서비스 (지연 로딩)"""

    def __init__(self, model_name: Optional[str] = None, device: str = "cpu"):
        self.enabled = os.getenv("FG_TRANSLATION_ENABLED", "1").lower() not in ("0", "false", "no")
        self.model_name = model_name or os.getenv(
            "FG_TRANSLATION_MODEL",
            "Helsinki-NLP/opus-mt-mul-en"
        )
        self.device = device
        self.max_new_tokens = int(os.getenv("FG_TRANSLATION_MAX_TOKENS", "128"))
        self.language_model_map = {
            "ko": "Helsinki-NLP/opus-mt-ko-en",
            "ja": "Helsinki-NLP/opus-mt-ja-en",
            "zh": "Helsinki-NLP/opus-mt-zh-en",
            "fr": "Helsinki-NLP/opus-mt-fr-en",
            "de": "Helsinki-NLP/opus-mt-de-en",
            "es": "Helsinki-NLP/opus-mt-es-en",
            "it": "Helsinki-NLP/opus-mt-it-en",
            "pt": "Helsinki-NLP/opus-mt-pt-en",
            "ru": "Helsinki-NLP/opus-mt-ru-en",
            "ar": "Helsinki-NLP/opus-mt-ar-en",
            "vi": "Helsinki-NLP/opus-mt-vi-en",
            "id": "Helsinki-NLP/opus-mt-id-en",
            "th": "Helsinki-NLP/opus-mt-th-en",
            "tr": "Helsinki-NLP/opus-mt-tr-en",
            "hi": "Helsinki-NLP/opus-mt-hi-en",
            "uk": "Helsinki-NLP/opus-mt-uk-en",
            "nl": "Helsinki-NLP/opus-mt-nl-en",
            "pl": "Helsinki-NLP/opus-mt-pl-en",
            "cs": "Helsinki-NLP/opus-mt-cs-en",
            "ro": "Helsinki-NLP/opus-mt-ro-en",
            "hu": "Helsinki-NLP/opus-mt-hu-en",
            "sv": "Helsinki-NLP/opus-mt-sv-en",
            "da": "Helsinki-NLP/opus-mt-da-en",
            "fi": "Helsinki-NLP/opus-mt-fi-en",
            "no": "Helsinki-NLP/opus-mt-no-en",
            "el": "Helsinki-NLP/opus-mt-el-en",
            "bg": "Helsinki-NLP/opus-mt-bg-en",
            "he": "Helsinki-NLP/opus-mt-he-en",
        }
        self._apply_custom_language_map()
        self._model_cache = {}

    def _apply_custom_language_map(self) -> None:
        raw_map = os.getenv("FG_TRANSLATION_MODEL_MAP")
        if not raw_map:
            return
        try:
            custom_map = json.loads(raw_map)
            if isinstance(custom_map, dict):
                self.language_model_map.update(custom_map)
        except json.JSONDecodeError:
            pass

    def _get_model_name(self, language: str) -> str:
        return self.language_model_map.get(language, self.model_name)

    def _load_model(self, model_name: str) -> Tuple[AutoTokenizer, AutoModelForSeq2SeqLM]:
        cached = self._model_cache.get(model_name)
        if cached:
            return cached

        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        model.to(self.device)
        self._model_cache[model_name] = (tokenizer, model)
        return tokenizer, model

    def detect_language(self, text: str) -> str:
        if not text.strip():
            return "unknown"

        language, _score = langid.classify(text)
        return language or "unknown"

    def _translate_with_hf(self, text: str, language: str) -> Tuple[str, dict]:
        model_name = self._get_model_name(language)
        try:
            tokenizer, model = self._load_model(model_name)
            inputs = tokenizer(
                [text],
                return_tensors="pt",
                padding=True,
                truncation=True
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            with torch.inference_mode():
                outputs = model.generate(**inputs, max_new_tokens=self.max_new_tokens)
            translated = tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
            if translated:
                return translated, {
                    "translated": True,
                    "language": language,
                    "provider": "hf",
                    "model": model_name
                }
        except Exception as exc:
            return text, {
                "translated": False,
                "language": language,
                "provider": "hf",
                "model": model_name,
                "error": str(exc)
            }

        return text, {"translated": False, "language": language, "provider": "hf", "model": model_name}

    def translate(self, text: str) -> Tuple[str, dict]:
        if not self.enabled or not text.strip():
            return text, {"translated": False, "language": "unknown"}

        language = self.detect_language(text)
        if language in ("en", "unknown"):
            return text, {"translated": False, "language": language}

        return self._translate_with_hf(text, language)


_translator_instance: Optional[TranslationService] = None


def get_translator() -> TranslationService:
    """번역기 싱글톤"""
    global _translator_instance
    if _translator_instance is None:
        _translator_instance = TranslationService()
    return _translator_instance
