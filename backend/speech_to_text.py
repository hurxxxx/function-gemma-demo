"""
Whisper 음성 인식 모듈
음성을 텍스트로 변환
"""
import whisper
import tempfile
import os
from typing import Optional


class SpeechToText:
    """Whisper 기반 음성 인식"""

    def __init__(self, model_size: str = "base"):
        """
        Args:
            model_size: whisper 모델 크기
                - tiny: 가장 가벼움 (~39M 파라미터, 빠름)
                - base: 균형 (~74M 파라미터, 권장)
                - small: 정확도 높음 (~244M 파라미터, 느림)
        """
        self.model_size = model_size
        self.model = None
        self.loaded = False

    def load(self):
        """모델 로드 (지연 로딩)"""
        if self.loaded:
            return

        print(f"Loading Whisper model: {self.model_size}")
        self.model = whisper.load_model(self.model_size)
        self.loaded = True
        print("Whisper model loaded successfully!")

    def transcribe(self, audio_file_path: str, language: Optional[str] = None) -> dict:
        """
        음성 파일을 텍스트로 변환

        Args:
            audio_file_path: 음성 파일 경로 (wav, mp3, webm 등)
            language: 언어 코드 (None이면 자동 감지)
                - None: 자동 감지 (100+ 언어 지원)
                - "ko": 한국어
                - "en": 영어
                - "ja": 일본어
                - "zh": 중국어 등

        Returns:
            {
                "text": str,
                "language": str,
                "success": bool
            }
        """
        if not self.loaded:
            self.load()

        try:
            # language=None이면 자동 감지
            transcribe_options = {
                "fp16": False  # CPU에서는 fp16 비활성화
            }
            if language:
                transcribe_options["language"] = language

            result = self.model.transcribe(audio_file_path, **transcribe_options)

            detected_language = result.get("language", "unknown")

            return {
                "text": result["text"].strip(),
                "language": detected_language,
                "success": True
            }
        except Exception as e:
            return {
                "text": "",
                "language": "unknown",
                "success": False,
                "error": str(e)
            }

    def transcribe_bytes(self, audio_bytes: bytes, language: Optional[str] = None) -> dict:
        """
        음성 바이트를 텍스트로 변환

        Args:
            audio_bytes: 음성 데이터 바이트
            language: 언어 코드 (None이면 자동 감지)

        Returns:
            변환 결과
        """
        # 임시 파일로 저장 후 변환
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            return self.transcribe(tmp_path, language)
        finally:
            # 임시 파일 삭제
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


# 전역 인스턴스
_stt_instance: Optional[SpeechToText] = None


def get_stt(model_size: str = "base") -> SpeechToText:
    """STT 인스턴스 가져오기 (싱글톤)"""
    global _stt_instance
    if _stt_instance is None:
        _stt_instance = SpeechToText(model_size)
    return _stt_instance
