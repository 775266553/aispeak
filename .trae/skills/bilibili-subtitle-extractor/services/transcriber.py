import os
# 修复 OpenMP 库冲突
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import re
from pathlib import Path
from faster_whisper import WhisperModel
from models import TranscribeStage
from .config import config
from .logging import get_logger
from typing import Optional, Callable

try:
    from opencc import OpenCC
except Exception:  # pragma: no cover - optional dependency fallback
    OpenCC = None

logger = get_logger(__name__)

_opencc = OpenCC("t2s") if OpenCC else None


def _to_simplified(text: str) -> str:
    if not text or _opencc is None:
        return text
    return _opencc.convert(text)

class WhisperTranscriber:
    _instance = None
    _model = None

    def __new__(cls, model_size: str = "base", device: str = "auto"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.model_size = model_size
            cls._instance.device = device
        return cls._instance

    def load_model(self, progress_callback: Optional[Callable] = None):
        if self._model is None:
            if progress_callback:
                progress_callback(TranscribeStage.MODEL_LOADING, 0)

            compute_type = "float16" if self.device == "cuda" else "int8"
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=compute_type
            )

            if progress_callback:
                progress_callback(TranscribeStage.MODEL_LOADING, 100)

        return self._model

    def transcribe(
        self,
        audio_path: str,
        output_path: str = None,
        progress_callback: Optional[Callable] = None
    ) -> str:
        model = self.load_model(progress_callback)

        if progress_callback:
            progress_callback(TranscribeStage.TRANSCRIBING, 0)

        segments, info = model.transcribe(
            audio_path,
            language="zh",
            beam_size=5,
            vad_filter=True
        )

        total_duration = info.duration or 0
        transcribed_text = []

        for segment in segments:
            converted_text = _to_simplified(segment.text)
            transcribed_text.append(converted_text)
            if progress_callback and total_duration > 0:
                progress = (segment.end / total_duration) * 100
                progress_callback(TranscribeStage.TRANSCRIBING, min(progress, 99))

        full_text = ''.join(transcribed_text)

        if progress_callback:
            progress_callback(TranscribeStage.WRITING_FILE, 0)

        if output_path:
            output_format = config.get("output_format", "txt")
            if output_format == "txt":
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(full_text)
                timestamp_path = self._build_timestamp_path(output_path)
                self._write_timestamp_txt(segments, timestamp_path)
            elif output_format == "srt":
                self._write_srt(segments, output_path)
            elif output_format == "json":
                import json
                segments_data = [
                    {
                        "start": s.start,
                        "end": s.end,
                        "text": _to_simplified(s.text)
                    }
                    for s in segments
                ]
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(segments_data, f, ensure_ascii=False, indent=2)

        if progress_callback:
            progress_callback(TranscribeStage.WRITING_FILE, 100)

        logger.info(f"Transcription complete: {output_path}")
        return full_text

    def _build_timestamp_path(self, output_path: str) -> str:
        path = Path(output_path)
        return str(path.with_name(f"{path.stem}_时间戳.txt"))

    def _write_timestamp_txt(self, segments, output_path: str):
        with open(output_path, 'w', encoding='utf-8') as f:
            for segment in segments:
                start = self._format_timestamp(segment.start).replace(',', '.')
                end = self._format_timestamp(segment.end).replace(',', '.')
                f.write(f"[{start} - {end}] {_to_simplified(segment.text)}\n")

    def _write_srt(self, segments, output_path: str):
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(segments, 1):
                start = self._format_timestamp(segment.start)
                end = self._format_timestamp(segment.end)
                f.write(f"{i}\n{start} --> {end}\n{_to_simplified(segment.text)}\n\n")

    def _format_timestamp(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def create_transcriber(model_size: str = None, device: str = None) -> WhisperTranscriber:
    if model_size is None:
        model_size = config.get("whisper_model", "base")
    if device is None:
        device = config.get("whisper_device", "auto")
        if device == "auto":
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except:
                device = "cpu"
    return WhisperTranscriber(model_size, device)
