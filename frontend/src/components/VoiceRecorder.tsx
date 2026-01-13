import { useState, useRef, useCallback, useEffect } from 'react';
import './VoiceRecorder.css';

interface CommandResult {
  success: boolean;
  transcription?: string;
  input_text?: string;
  function_call?: {
    function_name: string;
    parameters: Record<string, unknown>;
  };
  function_calls?: Array<{
    function_name: string;
    parameters: Record<string, unknown>;
  }>;
  result?: {
    message?: string;
    [key: string]: unknown;
  };
  results?: Array<{
    message?: string;
    [key: string]: unknown;
  }>;
  raw_output?: string;
  detected_language?: string;
}

interface VoiceRecorderProps {
  onResult: (result: CommandResult) => void;
  disabled?: boolean;
}

const isMediaRecorderSupported = () =>
  Boolean(navigator.mediaDevices?.getUserMedia && window.MediaRecorder);

const supportedMimeTypes = [
  'audio/webm;codecs=opus',
  'audio/webm',
  'audio/ogg;codecs=opus',
  'audio/ogg',
  'audio/mp4',
  'audio/mpeg',
];

const pickMimeType = () => {
  if (!window.MediaRecorder) {
    return undefined;
  }
  return supportedMimeTypes.find((type) => MediaRecorder.isTypeSupported(type));
};

const mimeTypeToExtension = (mimeType?: string) => {
  if (!mimeType) return 'webm';
  if (mimeType.includes('ogg')) return 'ogg';
  if (mimeType.includes('mp4')) return 'm4a';
  if (mimeType.includes('mpeg')) return 'mp3';
  return 'webm';
};

export function VoiceRecorder({ onResult, disabled }: VoiceRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSupported, setIsSupported] = useState(true);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    setIsSupported(isMediaRecorderSupported());

    return () => {
      if (recorderRef.current) {
        recorderRef.current.ondataavailable = null;
        recorderRef.current.onstop = null;
        recorderRef.current.onerror = null;
        if (recorderRef.current.state !== 'inactive') {
          recorderRef.current.stop();
        }
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
    };
  }, []);

  const reportError = useCallback((message: string) => {
    setErrorMessage(message);
    onResult({
      success: false,
      transcription: '',
      result: { message },
    });
  }, [onResult]);

  const sendAudioToServer = useCallback(async (audioBlob: Blob, mimeType?: string) => {
    setIsProcessing(true);
    setErrorMessage(null);
    try {
      const extension = mimeTypeToExtension(mimeType || audioBlob.type);
      const formData = new FormData();
      formData.append('audio', audioBlob, `command.${extension}`);

      const response = await fetch('/api/command/voice', {
        method: 'POST',
        body: formData,
      });

      const contentType = response.headers.get('content-type') || '';
      const data = contentType.includes('application/json')
        ? await response.json()
        : await response.text();

      if (!response.ok) {
        const message = typeof data === 'string'
          ? data
          : data?.detail || data?.result?.message || '요청 실패';
        reportError(message);
        return;
      }

      onResult(data as CommandResult);
    } catch (error) {
      console.error('Failed to process voice command:', error);
      reportError('서버 연결 실패');
    } finally {
      setIsProcessing(false);
    }
  }, [onResult, reportError]);

  const stopStream = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  };

  const startRecording = useCallback(async () => {
    if (!isMediaRecorderSupported()) {
      setIsSupported(false);
      return;
    }

    setErrorMessage(null);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mimeType = pickMimeType();
      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);

      recorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (event: BlobEvent) => {
        if (event.data && event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onerror = () => {
        setIsRecording(false);
        stopStream();
        reportError('음성 녹음에 실패했습니다');
      };

      recorder.onstop = async () => {
        setIsRecording(false);
        stopStream();

        const audioType = recorder.mimeType || mimeType || 'audio/webm';
        const audioBlob = new Blob(chunksRef.current, { type: audioType });
        chunksRef.current = [];

        if (audioBlob.size === 0) {
          reportError('녹음된 오디오가 없습니다');
          return;
        }

        await sendAudioToServer(audioBlob, audioType);
      };

      recorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Failed to start recording:', error);
      setIsRecording(false);
      stopStream();
      reportError('마이크 접근 권한이 필요합니다');
    }
  }, [reportError, sendAudioToServer]);

  const stopRecording = useCallback(() => {
    if (!recorderRef.current) return;
    if (recorderRef.current.state !== 'inactive') {
      recorderRef.current.stop();
    }
  }, []);

  const handleClick = () => {
    if (disabled || isProcessing || !isSupported) return;

    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  if (!isSupported) {
    return (
      <div className="voice-recorder">
        <button className="record-button unsupported" disabled>
          <div className="mic-icon">🎤</div>
        </button>
        <div className="record-status error">
          이 브라우저는 음성 녹음을 지원하지 않습니다
        </div>
      </div>
    );
  }

  const statusText = isProcessing
    ? '처리 중...'
    : isRecording
      ? '녹음 중... (클릭하여 중지)'
      : '클릭하여 음성 명령';

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
      <div className={`record-status ${errorMessage ? 'error' : ''}`}>
        {errorMessage || statusText}
      </div>
    </div>
  );
}
