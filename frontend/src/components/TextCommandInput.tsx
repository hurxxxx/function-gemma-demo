import { useState, type ChangeEvent, type FormEvent, type KeyboardEvent } from 'react';
import './TextCommandInput.css';

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
}

interface TextCommandInputProps {
  onResult: (result: CommandResult) => void;
  disabled?: boolean;
}

export function TextCommandInput({ onResult, disabled }: TextCommandInputProps) {
  const [text, setText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (event?: FormEvent<HTMLFormElement>) => {
    event?.preventDefault();
    if (disabled || isSubmitting) return;

    const trimmed = text.trim();
    if (!trimmed) {
      setErrorMessage('명령을 입력해주세요');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const response = await fetch('/api/command/text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: trimmed }),
      });

      const contentType = response.headers.get('content-type') || '';
      const data = contentType.includes('application/json')
        ? await response.json()
        : await response.text();

      if (!response.ok) {
        const message = typeof data === 'string'
          ? data
          : data?.detail || data?.result?.message || '요청 실패';
        setErrorMessage(message);
        onResult({
          success: false,
          input_text: trimmed,
          result: { message },
        });
        return;
      }

      onResult(data as CommandResult);
      setText('');
    } catch (error) {
      console.error('Failed to process text command:', error);
      const message = '서버 연결 실패';
      setErrorMessage(message);
      onResult({
        success: false,
        input_text: trimmed,
        result: { message },
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    setText(event.target.value);
    if (errorMessage) {
      setErrorMessage(null);
    }
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void handleSubmit();
    }
  };

  const statusText = errorMessage
    ? errorMessage
    : isSubmitting
      ? '명령 전송 중...'
      : disabled
        ? '연결이 필요합니다'
        : 'Enter로 전송 / Shift+Enter 줄바꿈';

  const isSubmitDisabled = disabled || isSubmitting || text.trim().length === 0;

  return (
    <form className="text-command" onSubmit={handleSubmit}>
      <div className="text-command-header">
        <div className="text-command-title">텍스트 명령</div>
        <div className="text-command-tag">Type</div>
      </div>
      <textarea
        id="text-command-input"
        name="text-command-input"
        placeholder="예: 거실등 밝기 50%로 해줘"
        value={text}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        disabled={disabled || isSubmitting}
        aria-label="텍스트 명령 입력"
        rows={3}
      />
      <div className="text-command-footer">
        <div className={`text-command-status ${errorMessage ? 'error' : isSubmitting ? 'processing' : ''}`}>
          {statusText}
        </div>
        <button
          type="submit"
          className="send-button"
          disabled={isSubmitDisabled}
        >
          전송
        </button>
      </div>
    </form>
  );
}
