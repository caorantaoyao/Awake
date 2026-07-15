import { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate, Link, useOutletContext } from 'react-router-dom';
import Toast from '../components/Toast';
import {
  sendChat,
  extractTask,
  getStudent,
  getCurrentStudent,
  getAuthToken,
  getStoredStudent,
  clearAuthSession
} from '../api/client';

const Chat = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const outletContext = useOutletContext() || {};
  const queryEmail = searchParams.get('email');
  const storedStudent = getAuthToken() ? getStoredStudent() : null;

  const [email, setEmail] = useState(queryEmail || storedStudent?.email || '');
  const [student, setStudent] = useState(storedStudent);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionLoading, setSessionLoading] = useState(!queryEmail && !!getAuthToken());
  const [canExtract, setCanExtract] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [toast, setToast] = useState(null);

  const scrollAnchorRef = useRef(null);
  const inputRef = useRef(null);
  const welcomedRef = useRef(false);
  const setWorkspaceStudent = outletContext.setStudent;

  // 优先兼容旧邮件链接；无 email 参数时使用登录 token 恢复会话。
  useEffect(() => {
    let alive = true;

    const loadStudent = async () => {
      if (queryEmail) {
        setEmail(queryEmail);
        setWorkspaceStudent?.({ email: queryEmail });
        setSessionLoading(false);
        try {
          const data = await getStudent(queryEmail);
          if (alive) {
            setStudent(data);
            setWorkspaceStudent?.(data);
          }
        } catch {
          // 静默失败，name 保持为空，仍可对话
        }
        return;
      }

      if (!getAuthToken()) {
        clearAuthSession();
        setStudent(null);
        setEmail('');
        setWorkspaceStudent?.(null);
        setSessionLoading(false);
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
      } finally {
        if (alive) setSessionLoading(false);
      }
    };

    loadStudent();
    return () => {
      alive = false;
    };
  }, [queryEmail, setWorkspaceStudent]);

  // 初始欢迎：页面挂载后自动请求一次，让小海先打招呼
  useEffect(() => {
    if (!email || sessionLoading || welcomedRef.current) return;
    welcomedRef.current = true;
    const studentName = student?.name || '';

    const bootstrap = async () => {
      setLoading(true);
      try {
        const res = await sendChat({ messages: [], student_name: studentName });
        setMessages([{ role: 'assistant', content: res.reply }]);
        setCanExtract(!!res.can_extract_task);
      } catch {
        setMessages([
          {
            role: 'assistant',
            content:
              '你好呀，我是小海 🌊 很高兴认识你！最近有什么让你好奇或纠结的事情吗？我们可以一起聊聊。'
          }
        ]);
      } finally {
        setLoading(false);
      }
    };
    bootstrap();
    // 依赖 email 与 student：等 student 请求返回后再触发一次；welcomedRef 保证只跑一次
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [email, sessionLoading, student]);

  // 消息变化时自动滚动到底部
  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, loading]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg = { role: 'user', content: text };
    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    setInput('');
    setLoading(true);

    try {
      const res = await sendChat({
        messages: nextMessages,
        student_name: student?.name || ''
      });
      setMessages((prev) => [...prev, { role: 'assistant', content: res.reply }]);
      setCanExtract(!!res.can_extract_task);
    } catch {
      setToast({ message: '小海暂时没能回应，请稍后再试一次。', type: 'error' });
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: '抱歉，我这边好像走神了 😅 能再说一遍吗？'
        }
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleAcceptTask = async () => {
    if (extracting) return;
    setExtracting(true);
    try {
      const res = await extractTask({ student_email: email, messages });
      const taskId = res?.data?.task?.id;
      if (taskId != null) {
        navigate(`/checkin?task_id=${taskId}`);
      } else {
        setToast({ message: '任务已生成，但未能获取任务ID。', type: 'error' });
      }
    } catch (err) {
      setToast({
        message: err.response?.data?.detail || '生成任务失败，请稍后再试。',
        type: 'error'
      });
    } finally {
      setExtracting(false);
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
                <div className="chat-bubble chat-bubble-ai chat-typing">
                  <span className="chat-typing-label">小海正在思考</span>
                  <span className="chat-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </span>
                </div>
              </div>
            )}
            <div ref={scrollAnchorRef} />
          </div>

          {/* 输入区 */}
          <div className="chat-input-bar">
            <textarea
              ref={inputRef}
              className="chat-input"
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
