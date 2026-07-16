import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, Link, useOutletContext } from 'react-router-dom';
import Toast from '../components/Toast';
import {
  sendChat,
  extractTask,
  getChatHistory,
  getCurrentStudent,
  getAuthToken,
  clearAuthSession
} from '../api/client';
import { restoreConversation } from '../utils/growth';

const Chat = () => {
  const navigate = useNavigate();
  const outletContext = useOutletContext() || {};
  const [email, setEmail] = useState('');
  const [student, setStudent] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionLoading, setSessionLoading] = useState(!!getAuthToken());
  const [canExtract, setCanExtract] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [toast, setToast] = useState(null);
  const [waitStage, setWaitStage] = useState(0);
  const [failedRequest, setFailedRequest] = useState(null);
  const [historyResolved, setHistoryResolved] = useState(false);

  const scrollAnchorRef = useRef(null);
  const inputRef = useRef(null);
  const welcomedRef = useRef(false);
  const requestSequenceRef = useRef(0);
  const activeRequestRef = useRef(null);
  const extractSequenceRef = useRef(0);
  const activeExtractRef = useRef(null);
  const identityKeyRef = useRef('session');
  const lifecycleRef = useRef(0);
  const setWorkspaceStudent = outletContext.setStudent;

  useEffect(() => {
    let alive = true;

    const restoreSession = async () => {
      if (!getAuthToken()) {
        clearAuthSession();
        setStudent(null);
        setEmail('');
        setWorkspaceStudent?.(null);
        setSessionLoading(false);
        setHistoryResolved(true);
        return;
      }

      setSessionLoading(true);
      try {
        const currentStudent = await getCurrentStudent();
        if (alive) {
          setStudent(currentStudent);
          setEmail(currentStudent.email);
          setWorkspaceStudent?.(currentStudent);
        }
      } catch {
        clearAuthSession();
        if (alive) {
          setStudent(null);
          setEmail('');
          setWorkspaceStudent?.(null);
        }
        if (alive) {
          setSessionLoading(false);
          setHistoryResolved(true);
        }
        return;
      }

      try {
        const history = restoreConversation(await getChatHistory(50));
        if (!alive) return;
        setMessages(history.messages);
        setCanExtract(history.canExtractTask);
        welcomedRef.current = history.messages.length > 0;
      } catch {
        if (alive) {
          setToast({ message: '历史对话暂时没有同步，将从本次对话继续。', type: 'error' });
        }
      } finally {
        if (alive) {
          setSessionLoading(false);
          setHistoryResolved(true);
        }
      }
    };

    restoreSession();
    return () => {
      alive = false;
    };
  }, [setWorkspaceStudent]);

  const runChatRequest = useCallback(async (nextMessages, { bootstrap = false } = {}) => {
    const identityKey = identityKeyRef.current;
    const requestId = requestSequenceRef.current + 1;
    requestSequenceRef.current = requestId;
    const controller = new AbortController();

    setLoading(true);
    setWaitStage(0);
    setFailedRequest(null);

    const mediumWaitTimer = window.setTimeout(() => {
      if (activeRequestRef.current?.requestId === requestId) setWaitStage(1);
    }, 5000);
    const longWaitTimer = window.setTimeout(() => {
      if (activeRequestRef.current?.requestId === requestId) setWaitStage(2);
    }, 15000);
    activeRequestRef.current = {
      requestId,
      controller,
      messages: nextMessages,
      bootstrap,
      identityKey,
      timers: [mediumWaitTimer, longWaitTimer]
    };

    try {
      const res = await sendChat(
        { messages: nextMessages, student_name: student?.name || '' },
        { signal: controller.signal }
      );
      if (
        activeRequestRef.current?.requestId !== requestId ||
        identityKeyRef.current !== identityKey
      ) return;

      if (bootstrap) {
        setMessages([{ role: 'assistant', content: res.reply }]);
      } else {
        setMessages((prev) => [...prev, { role: 'assistant', content: res.reply }]);
      }
      setCanExtract(!!res.can_extract_task);
    } catch (err) {
      if (
        activeRequestRef.current?.requestId !== requestId ||
        identityKeyRef.current !== identityKey ||
        controller.signal.aborted ||
        err.code === 'ERR_CANCELED'
      ) {
        return;
      }

      if (bootstrap) {
        setMessages([
          {
            role: 'assistant',
            content:
              '你好呀，我是小海 🌊 很高兴认识你！最近有什么让你好奇或纠结的事情吗？我们可以一起聊聊。'
          }
        ]);
      } else {
        setFailedRequest({ messages: nextMessages, bootstrap: false });
        setToast({ message: '这次回应没有完成，你可以直接重试刚才的消息。', type: 'error' });
      }
    } finally {
      window.clearTimeout(mediumWaitTimer);
      window.clearTimeout(longWaitTimer);
      if (activeRequestRef.current?.requestId === requestId) {
        activeRequestRef.current = null;
        setLoading(false);
        setWaitStage(0);
        window.setTimeout(() => inputRef.current?.focus(), 0);
      }
    }
  }, [student?.name]);

  // 初始欢迎：页面挂载后自动请求一次，让小海先打招呼
  useEffect(() => {
    if (
      !email ||
      sessionLoading ||
      !historyResolved ||
      welcomedRef.current
    ) {
      return;
    }
    welcomedRef.current = true;
    runChatRequest([], { bootstrap: true });
    // 依赖 email 与 student：等 student 请求返回后再触发一次；welcomedRef 保证只跑一次
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    email,
    historyResolved,
    runChatRequest,
    sessionLoading,
    student
  ]);

  useEffect(() => {
    const lifecycleId = lifecycleRef.current + 1;
    lifecycleRef.current = lifecycleId;

    return () => {
      queueMicrotask(() => {
        // StrictMode 会立即执行一次 setup/cleanup；仅在组件真正卸载时取消请求。
        if (lifecycleRef.current !== lifecycleId) return;
        activeRequestRef.current?.timers.forEach((timer) => window.clearTimeout(timer));
        activeRequestRef.current?.controller.abort();
        activeRequestRef.current = null;
        activeExtractRef.current?.controller.abort();
        activeExtractRef.current = null;
      });
    };
  }, []);

  // 消息变化时自动滚动到底部
  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, loading]);

  const handleSend = () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg = { role: 'user', content: text };
    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    setInput('');
    runChatRequest(nextMessages);
  };

  const handleCancelRequest = () => {
    const activeRequest = activeRequestRef.current;
    if (!activeRequest) return;

    activeRequestRef.current = null;
    activeRequest.timers.forEach((timer) => window.clearTimeout(timer));
    activeRequest.controller.abort();
    setFailedRequest({
      messages: activeRequest.messages,
      bootstrap: activeRequest.bootstrap
    });
    setLoading(false);
    setWaitStage(0);
    window.setTimeout(() => inputRef.current?.focus(), 0);
  };

  const handleRetry = () => {
    if (!failedRequest || loading) return;
    runChatRequest(failedRequest.messages, { bootstrap: failedRequest.bootstrap });
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleAcceptTask = async () => {
    if (extracting) return;
    const identityKey = identityKeyRef.current;
    const requestId = extractSequenceRef.current + 1;
    const controller = new AbortController();
    extractSequenceRef.current = requestId;
    activeExtractRef.current = { requestId, identityKey, controller };
    setExtracting(true);
    try {
      const res = await extractTask(
        { student_email: email, messages },
        { signal: controller.signal }
      );
      if (
        activeExtractRef.current?.requestId !== requestId ||
        identityKeyRef.current !== identityKey
      ) return;
      const taskId = res?.data?.task?.id;
      if (taskId != null) {
        navigate(`/app/focus?task_id=${taskId}`);
      } else {
        setToast({ message: '任务已生成，但未能获取任务ID。', type: 'error' });
      }
    } catch (err) {
      if (
        controller.signal.aborted ||
        err.code === 'ERR_CANCELED' ||
        identityKeyRef.current !== identityKey
      ) return;
      setToast({
        message: err.response?.data?.detail || '生成任务失败，请稍后再试。',
        type: 'error'
      });
    } finally {
      if (
        activeExtractRef.current?.requestId === requestId &&
        identityKeyRef.current === identityKey
      ) {
        activeExtractRef.current = null;
        setExtracting(false);
      }
    }
  };

  // 缺少 email：友好引导
  if (sessionLoading) {
    return (
      <>
        <div className="workspace-state">
          <div className="workspace-state-card">
            <div className="workspace-state-mark">ID</div>
            <h2>正在恢复登录状态</h2>
            <p>正在读取你的 Awaken 会话，完成后会直接回到小海对话区。</p>
          </div>
        </div>
      </>
    );
  }

  if (!email) {
    return (
      <>
        <div className="workspace-state">
          <div className="workspace-state-card">
            <div className="workspace-state-mark">小海</div>
            <h2>先登录，小海在这里等你</h2>
            <p>
              与小海的对话需要一个专属入口。登录后，我们会把你带回属于你的对话空间。
            </p>
            <Link to="/login" className="workspace-primary-link">
              登录已有账号 →
            </Link>
            <Link to="/register" className="workspace-secondary-link">
              还没有账号？先注册
            </Link>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      {toast && (
        <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />
      )}
      <div className="chat-page">
        <div className="chat-container">
          {/* 对话标题区 */}
          <div className="chat-header">
            <div className="chat-avatar chat-avatar-lg">🌊</div>
            <div className="chat-header-text">
              <h1 className="chat-title">与小海对话</h1>
              <p className="chat-subtitle">
                {student?.name ? `${student.name}，` : ''}跟着好奇心聊聊，让我陪你找到今天的一小步。
              </p>
            </div>
          </div>

          {/* 可提炼任务提示卡片 */}
          {canExtract && (
            <div className="chat-extract-card">
              <div className="chat-extract-copy">
                <div className="chat-extract-title">✨ 灵感已就绪</div>
                <div className="chat-extract-desc">
                  小海从这次对话里为你准备了一个微行动任务，接受后即可开始打卡。
                </div>
              </div>
              <button
                className="chat-extract-btn"
                onClick={handleAcceptTask}
                disabled={extracting}
              >
                {extracting ? '生成中…' : '接受今天的微行动任务'}
              </button>
            </div>
          )}

          {/* 消息流 */}
          <div className="chat-messages">
            {messages.map((msg, idx) =>
              msg.role === 'user' ? (
                <div key={idx} className="chat-row chat-row-user">
                  <div className="chat-bubble chat-bubble-user">{msg.content}</div>
                </div>
              ) : (
                <div key={idx} className="chat-row chat-row-ai">
                  <div className="chat-avatar chat-avatar-sm">🌊</div>
                  <div className="chat-bubble chat-bubble-ai">{msg.content}</div>
                </div>
              )
            )}

            {loading && (
              <div className="chat-row chat-row-ai">
                <div className="chat-avatar chat-avatar-sm">🌊</div>
                <div className="chat-bubble chat-bubble-ai chat-typing" aria-live="polite">
                  <span className="chat-typing-label">
                    {waitStage === 0 && '小海正在整理你的回答'}
                    {waitStage === 1 && '正在结合你的信息思考方向，可能还需要几秒'}
                    {waitStage === 2 && '这次分析比较深入，你可以继续等待或取消本次回应'}
                  </span>
                  {waitStage < 2 ? (
                    <span className="chat-dots" aria-hidden="true">
                      <span></span>
                      <span></span>
                      <span></span>
                    </span>
                  ) : (
                    <button
                      type="button"
                      className="chat-inline-action"
                      onClick={handleCancelRequest}
                    >
                      取消等待
                    </button>
                  )}
                </div>
              </div>
            )}
            {!loading && failedRequest && (
              <div className="chat-retry-card" role="status">
                <span>
                  {failedRequest.bootstrap
                    ? '小海的开场问候没有完成，你可以重新连接。'
                    : '刚才的回应没有完成，你的消息已经保留。'}
                </span>
                <button type="button" className="chat-inline-action" onClick={handleRetry}>
                  {failedRequest.bootstrap ? '重新连接小海' : '重试刚才消息'}
                </button>
              </div>
            )}
            <div ref={scrollAnchorRef} />
          </div>

          {/* 输入区 */}
          <div className="chat-input-bar">
            <textarea
              ref={inputRef}
              className="chat-input"
              aria-label="输入给小海的消息"
              placeholder={loading ? '小海正在思考…' : '说点什么，回车发送（Shift+Enter 换行）'}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
              rows={1}
            />
            <button
              className="chat-send-btn"
              onClick={handleSend}
              disabled={loading || !input.trim()}
              aria-label="发送"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

export default Chat;
