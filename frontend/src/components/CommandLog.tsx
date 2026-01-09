import './CommandLog.css';

export interface LogEntry {
  id: number;
  timestamp: Date;
  input: string;
  functionCall?: {
    function_name: string;
    parameters: Record<string, unknown>;
  };
  result?: string;
  success: boolean;
}

interface CommandLogProps {
  logs: LogEntry[];
}

export function CommandLog({ logs }: CommandLogProps) {
  if (logs.length === 0) {
    return (
      <div className="command-log empty">
        <div className="empty-message">
          음성 명령 기록이 여기에 표시됩니다
        </div>
      </div>
    );
  }

  return (
    <div className="command-log">
      <div className="log-header">명령 기록</div>
      <div className="log-entries">
        {logs.map((log) => (
          <div key={log.id} className={`log-entry ${log.success ? 'success' : 'error'}`}>
            <div className="log-time">
              {log.timestamp.toLocaleTimeString('ko-KR', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
              })}
            </div>
            <div className="log-content">
              <div className="log-input">
                <span className="label">입력:</span>
                <span className="value">"{log.input}"</span>
              </div>
              {log.functionCall && (
                <div className="log-function">
                  <span className="label">함수:</span>
                  <code className="function-call">
                    {log.functionCall.function_name}
                    ({Object.entries(log.functionCall.parameters || {})
                      .map(([k, v]) => `${k}: ${JSON.stringify(v)}`)
                      .join(', ')})
                  </code>
                </div>
              )}
              {log.result && (
                <div className="log-result">
                  <span className="label">결과:</span>
                  <span className="value">{log.result}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
