import { useState, useCallback } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { ACDisplay } from './components/ACDisplay';
import { VoiceRecorder } from './components/VoiceRecorder';
import { ManualControls } from './components/ManualControls';
import { CommandLog, type LogEntry } from './components/CommandLog';
import './App.css';

function App() {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  // Vite 프록시를 통해 WebSocket 연결 (포트 포워딩 호환)
  const wsUrl = `${wsProtocol}://${window.location.host}/ws`;
  const { state, connected } = useWebSocket(wsUrl);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [logId, setLogId] = useState(0);

  const handleResult = useCallback((result: {
    success: boolean;
    transcription?: string;
    input_text?: string;
    function_call?: {
      function_name: string;
      parameters: Record<string, unknown>;
    };
    result?: {
      message?: string;
    };
  }) => {
    const newLog: LogEntry = {
      id: logId,
      timestamp: new Date(),
      input: result.transcription || result.input_text || '(음성 인식 실패)',
      functionCall: result.function_call,
      result: result.result?.message || (result.success ? '성공' : '실패'),
      success: result.success,
    };

    setLogs(prev => [newLog, ...prev].slice(0, 10)); // 최근 10개만 유지
    setLogId(prev => prev + 1);
  }, [logId]);

  return (
    <div className="app">
      <header className="app-header">
        <h1>FunctionGemma Car A/C Demo</h1>
        <div className={`connection-status ${connected ? 'connected' : 'disconnected'}`}>
          {connected ? '연결됨' : '연결 끊김'}
        </div>
      </header>

      <main className="app-main">
        <div className="left-panel">
          <ACDisplay state={state} />

          <ManualControls
            state={state}
            disabled={!connected}
          />

          <div className="voice-section">
            <VoiceRecorder
              onResult={handleResult}
              disabled={!connected}
            />
          </div>

          <div className="demo-hints">
            <div className="hints-title">음성 명령 예시</div>
            <ul>
              <li>"온도 올려줘" / "온도 내려줘"</li>
              <li>"오늘 날씨가 덥네"</li>
              <li>"아이들이 땀이 나네"</li>
              <li>"여름철 적정 온도로 맞춰줘"</li>
              <li>"바람 세게 해줘"</li>
              <li>"에어컨 꺼줘"</li>
            </ul>
          </div>
        </div>

        <div className="right-panel">
          <CommandLog logs={logs} />
        </div>
      </main>

      <footer className="app-footer">
        <p>FunctionGemma 기반 음성 에어컨 제어 데모</p>
      </footer>
    </div>
  );
}

export default App;
