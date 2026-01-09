import { useState, useRef, useCallback } from 'react';
import './VoiceRecorder.css';

interface CommandResult {
  success: boolean;
  transcription?: string;
  input_text?: string;
  function_call?: {
    function_name: string;
    parameters: Record<string, unknown>;
  };
  result?: {
    message?: string;
    [key: string]: unknown;
  };
  raw_output?: string;
}

interface VoiceRecorderProps {
  onResult: (result: CommandResult) => void;
  disabled?: boolean;
}

export function VoiceRecorder({ onResult, disabled }: VoiceRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });

      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach(track => track.stop());

        // 서버로 전송
        setIsProcessing(true);
        try {
          const formData = new FormData();
          formData.append('audio', audioBlob, 'recording.webm');

          const response = await fetch('/api/command/voice', {
            method: 'POST',
            body: formData,
          });

          const result = await response.json();
          onResult(result);
        } catch (error) {
          console.error('Failed to process voice command:', error);
          onResult({
            success: false,
            transcription: '',
            result: { message: '서버 연결 실패' }
          });
        } finally {
          setIsProcessing(false);
        }
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Failed to start recording:', error);
      alert('마이크 접근 권한이 필요합니다.');
    }
  }, [onResult]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, [isRecording]);

  const handleClick = () => {
    if (disabled || isProcessing) return;

    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <div className="voice-recorder">
      <button
        className={`record-button ${isRecording ? 'recording' : ''} ${isProcessing ? 'processing' : ''}`}
        onClick={handleClick}
        disabled={disabled || isProcessing}
      >
        {isProcessing ? (
          <div className="spinner" />
        ) : isRecording ? (
          <div className="stop-icon" />
        ) : (
          <div className="mic-icon">🎤</div>
        )}
      </button>
      <div className="record-status">
        {isProcessing ? '처리 중...' : isRecording ? '녹음 중... (클릭하여 중지)' : '클릭하여 음성 명령'}
      </div>
    </div>
  );
}
