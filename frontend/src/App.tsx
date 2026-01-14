import { useState, useCallback } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { VoiceRecorder } from './components/VoiceRecorder';
import { TextCommandInput } from './components/TextCommandInput';
import { CommandLog, type LogEntry } from './components/CommandLog';
import {
  ACCard,
  TVCard,
  LightCard,
  VacuumCard,
  AudioCard,
  CurtainCard,
  VentilationCard
} from './components/devices';
import './App.css';

function App() {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
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
    function_calls?: Array<{
      function_name: string;
      parameters: Record<string, unknown>;
    }>;
    result?: {
      message?: string;
    };
    results?: Array<{
      message?: string;
    }>;
  }) => {
    const newLog: LogEntry = {
      id: logId,
      timestamp: new Date(),
      input: result.transcription || result.input_text || '(음성 인식 실패)',
      functionCall: result.function_call,
      functionCalls: result.function_calls,
      result: result.results?.map(r => r.message).join(', ') || result.result?.message || (result.success ? '성공' : '실패'),
      success: result.success,
    };

    setLogs(prev => [newLog, ...prev].slice(0, 10));
    setLogId(prev => prev + 1);
  }, [logId]);

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-left">
          <span className="home-icon">🏠</span>
          <h1>스마트 홈</h1>
        </div>
        <div className={`connection-status ${connected ? 'connected' : 'disconnected'}`}>
          {connected ? '연결됨' : '연결 끊김'}
        </div>
      </header>

      <main className="app-main">
        <section className="devices-grid">
          <ACCard state={state.ac} disabled={!connected} />
          <TVCard state={state.tv} disabled={!connected} />
          <LightCard state={state.light} disabled={!connected} />
          <VacuumCard state={state.vacuum} disabled={!connected} />
          <AudioCard state={state.audio} disabled={!connected} />
          <CurtainCard state={state.curtain} disabled={!connected} />
          <VentilationCard state={state.ventilation} disabled={!connected} />
        </section>

        <section className="voice-control-section">
          <div className="command-inputs">
            <VoiceRecorder
              onResult={handleResult}
              disabled={!connected}
            />
            <TextCommandInput
              onResult={handleResult}
              disabled={!connected}
            />
          </div>
          <div className="voice-hints">
            <div className="hints-title">명령 예시</div>
            <ul>
              <li>"에어컨 온도 올려줘"</li>
              <li>"TV 켜줘"</li>
              <li>"거실등 밝기 50%"</li>
              <li>"청소기 거실 청소해"</li>
              <li>"커튼 닫아줘"</li>
              <li>"넷플릭스 틀어줘"</li>
              <li>"TV 켜고 조명 꺼줘"</li>
            </ul>
          </div>
        </section>

        <section className="command-log-section">
          <CommandLog logs={logs} />
        </section>
      </main>

      <footer className="app-footer">
        <p>FunctionGemma 기반 홈 IoT 음성 제어 데모</p>
      </footer>
    </div>
  );
}

export default App;
