import { useState, useEffect, useRef, useCallback } from 'react';
import { Link, useOutletContext } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Toast from '../components/Toast';
import {
  streamChat,
  extractTask,
  listConversations,
  getConversation,
  updateConversation,
  deleteConversation,
  getModels,
  getSkills,
  toggleSkill,
  getSuggestions,
  uploadFiles,
  getCurrentStudent,
  getAuthToken,
  clearAuthSession,
  polishInput,
  submitFeedback,
} from '../api/client';

const WELCOME_MESSAGE = '你好呀！我是小海 🌊，很高兴认识你。最近有没有哪件事，让你觉得有点好奇，或者有点烦心的？随便聊聊就好。';

const MarkdownMessage = ({ content }) => (
  <ReactMarkdown
    remarkPlugins={[remarkGfm]}
    components={{
      a: ({ node, ...props }) => (
        <a {...props} target="_blank" rel="noopener noreferrer" />
      ),
    }}
  >
    {content}
  </ReactMarkdown>
);

const ThinkingBlock = ({ content, streaming, open, onToggle }) => (
  <div className={`chat-thinking-block${open ? ' is-open' : ''}`}>
    <div className="chat-thinking-header" onClick={onToggle}>
      <svg className="chat-thinking-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z" />
        <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z" />
      </svg>
      <span className="chat-thinking-label">思考过程</span>
      {streaming && (
        <span className="chat-thinking-streaming">
          <span></span><span></span><span></span>
        </span>
      )}
      <svg className="chat-thinking-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="m6 9 6 6 6-6" />
      </svg>
    </div>
    <div className="chat-thinking-content">
      <div className="chat-markdown-wrap"><MarkdownMessage content={content} /></div>
    </div>
  </div>
);

const PlanBlock = ({ steps, onApprove, onEdit, onStepUpdate }) => {
  const [editingIdx, setEditingIdx] = useState(-1);
  const [editText, setEditText] = useState('');

  const handleStartEdit = (idx, text) => {
    setEditingIdx(idx);
    setEditText(text);
  };

  const handleSaveEdit = (idx) => {
    if (editText.trim()) {
      onStepUpdate(idx, editText.trim());
    }
    setEditingIdx(-1);
  };

  return (
    <div className="chat-plan-block">
      <div className="chat-plan-header">
        <svg className="chat-plan-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" />
        </svg>
        <span className="chat-plan-title">执行计划</span>
        <div className="chat-plan-actions">
          <button className="chat-plan-btn chat-plan-btn-edit" onClick={onEdit}>调整</button>
          <button className="chat-plan-btn chat-plan-btn-approve" onClick={onApprove}>确认执行</button>
        </div>
      </div>
      <div className="chat-plan-list">
        {steps.map((step, idx) => {
          const stepText = typeof step === 'string' ? step : step.title || step.description || JSON.stringify(step);
          return (
            <div key={idx} className={`chat-plan-step${editingIdx === idx ? ' is-editing' : ''}`}>
              <div className="chat-plan-step-num">{idx + 1}</div>
              {editingIdx === idx ? (
                <>
                  <textarea
                    className="chat-plan-step-edit-input"
                    value={editText}
                    onChange={(e) => setEditText(e.target.value)}
                    autoFocus
                  />
                  <div className="chat-plan-step-actions">
                    <button className="chat-plan-step-btn is-save" onClick={() => handleSaveEdit(idx)} title="保存">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="16" height="16">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    </button>
                    <button className="chat-plan-step-btn" onClick={() => setEditingIdx(-1)} title="取消">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="16" height="16">
                        <path d="M18 6 6 18M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <div className="chat-plan-step-text">{stepText}</div>
                  <div className="chat-plan-step-actions">
                    <button className="chat-plan-step-btn" onClick={() => handleStartEdit(idx, stepText)} title="编辑此步骤">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="14" height="14">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                      </svg>
                    </button>
                  </div>
                </>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

const getArtifactIcon = (type, name) => {
  const n = (name || '').toLowerCase();
  const t = (type || '').toLowerCase();
  if (n.endsWith('.pdf') || t.includes('pdf')) return '📕';
  if (n.endsWith('.md') || n.endsWith('.txt') || t.includes('text') || t.includes('markdown')) return '📝';
  if (n.endsWith('.docx') || n.endsWith('.doc') || t.includes('word')) return '📄';
  if (n.endsWith('.xlsx') || n.endsWith('.csv') || t.includes('sheet') || t.includes('excel')) return '📊';
  if (n.endsWith('.pptx') || n.endsWith('.ppt') || t.includes('presentation') || t.includes('slide')) return '📽️';
  if (n.endsWith('.png') || n.endsWith('.jpg') || n.endsWith('.jpeg') || n.endsWith('.gif') || n.endsWith('.svg') || t.includes('image')) return '🖼️';
  if (n.endsWith('.html') || t.includes('html') || t.includes('web')) return '🌐';
  if (t.includes('mindmap') || t.includes('mind_map')) return '🧠';
  if (t.includes('plan') || t.includes('report')) return '📋';
  if (t.includes('study') || t.includes('learn')) return '📚';
  return '📎';
};

const getArtifactTypeLabel = (type, name) => {
  const t = (type || '').toLowerCase();
  const n = (name || '').toLowerCase();
  if (t.includes('pdf') || n.endsWith('.pdf')) return 'PDF 文档';
  if (t.includes('markdown') || t.includes('text') || n.endsWith('.md') || n.endsWith('.txt')) return '文本文档';
  if (t.includes('report')) return '分析报告';
  if (t.includes('plan')) return '学习计划';
  if (t.includes('mindmap') || t.includes('mind_map')) return '思维导图';
  if (t.includes('image')) return '图片';
  if (t.includes('sheet') || t.includes('excel') || n.endsWith('.csv') || n.endsWith('.xlsx')) return '表格数据';
  return '产出物';
};

const ArtifactCard = ({ artifact }) => {
  const icon = getArtifactIcon(artifact.type, artifact.name);
  const typeLabel = getArtifactTypeLabel(artifact.type, artifact.name);
  return (
    <a href={artifact.url} target="_blank" rel="noopener noreferrer" className="chat-artifact-card">
      <span className="chat-artifact-emoji">{icon}</span>
      <div className="chat-artifact-body">
        <div className="chat-artifact-name">{artifact.name || '产出物'}</div>
        <div className="chat-artifact-meta">
          <span className="chat-artifact-type-badge">{typeLabel}</span>
          {artifact.size && <span className="chat-artifact-size">{artifact.size}</span>}
        </div>
      </div>
      <svg className="chat-artifact-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="14" height="14">
        <path d="M7 17L17 7M17 7H7M17 7v10" />
      </svg>
    </a>
  );
};

const FeedbackButtons = ({ onFeedback }) => {
  const [rated, setRated] = useState(null);

  const handleRate = (rating) => {
    setRated(rating);
    onFeedback(rating);
  };

  return (
    <div className="chat-feedback">
      <button
        className={`chat-feedback-btn${rated === 'up' ? ' is-up' : ''}`}
        onClick={() => handleRate('up')}
        title="有帮助"
        disabled={rated !== null}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M7 10v12" />
          <path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z" />
        </svg>
      </button>
      <button
        className={`chat-feedback-btn${rated === 'down' ? ' is-down' : ''}`}
        onClick={() => handleRate('down')}
        title="没帮助"
        disabled={rated !== null}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M17 14V2" />
          <path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3.13 3.13 0 0 1-3-3.88Z" />
        </svg>
      </button>
      {rated && <span className="chat-feedback-label">感谢反馈</span>}
    </div>
  );
};

const PerMessageThinking = ({ content, defaultOpen }) => {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <ThinkingBlock
      content={content}
      streaming={false}
      open={open}
      onToggle={() => setOpen(!open)}
    />
  );
};

const Chat = () => {
  const outletContext = useOutletContext() || {};
  const setWorkspaceStudent = outletContext.setStudent;

  const [student, setStudent] = useState(null);
  const [sessionLoading, setSessionLoading] = useState(true);
  const [welcomeMessage, setWelcomeMessage] = useState(WELCOME_MESSAGE);

  const [conversations, setConversations] = useState([]);
  const [activeConvId, setActiveConvId] = useState(null);
  const [convListOpen, setConvListOpen] = useState(true);
  const [skillsPanelOpen, setSkillsPanelOpen] = useState(false);

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const [streamingThinking, setStreamingThinking] = useState('');
  const [thinkingOpen, setThinkingOpen] = useState(true);
  const [toolCalls, setToolCalls] = useState([]);
  const [artifacts, setArtifacts] = useState([]);
  const [planSteps, setPlanSteps] = useState([]);
  const [planApproved, setPlanApproved] = useState(false);
  const [canExtract, setCanExtract] = useState(false);
  const [extracting, setExtracting] = useState(false);

  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [thinkingEnabled, setThinkingEnabled] = useState(false);
  const [isPlanMode, setIsPlanMode] = useState(false);

  const [skills, setSkills] = useState([]);
  const [skillsLoading, setSkillsLoading] = useState(false);

  const [suggestions, setSuggestions] = useState([]);

  const [uploadedFileIds, setUploadedFileIds] = useState([]);
  const [uploadedFileNames, setUploadedFileNames] = useState([]);
  const [polishPreview, setPolishPreview] = useState(null);
  const [polishing, setPolishing] = useState(false);

  const [toast, setToast] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [currentRunId, setCurrentRunId] = useState(null);

  const scrollAnchorRef = useRef(null);
  const inputRef = useRef(null);
  const abortControllerRef = useRef(null);
  const fileInputRef = useRef(null);
  const controlsRef = useRef(null);
  const convListFetchedRef = useRef(false);

  useEffect(() => {
    let alive = true;
    const init = async () => {
      if (!getAuthToken()) {
        clearAuthSession();
        setStudent(null);
        setWorkspaceStudent?.(null);
        setSessionLoading(false);
        return;
      }
      try {
        const pendingWelcome = localStorage.getItem('awaken_welcome_message');
        if (pendingWelcome) {
          setWelcomeMessage(pendingWelcome);
          localStorage.removeItem('awaken_welcome_message');
        }
        const s = await getCurrentStudent();
        if (!alive) return;
        setStudent(s);
        setWorkspaceStudent?.(s);
      } catch {
        clearAuthSession();
        if (alive) { setStudent(null); setWorkspaceStudent?.(null); }
        if (alive) setSessionLoading(false);
        return;
      }

      if (alive) setSessionLoading(false);
    };
    init();
    return () => { alive = false; };
  }, [setWorkspaceStudent]);

  useEffect(() => {
    if (!student || convListFetchedRef.current) return;
    convListFetchedRef.current = true;
    refreshConversations();
    refreshModels();
  }, [student]);

  const refreshConversations = useCallback(async () => {
    try {
      const convs = await listConversations();
      setConversations(convs);
      return convs;
    } catch {
      return [];
    }
  }, []);

  const refreshModels = useCallback(async () => {
    try {
      const res = await getModels();
      if (res.online && res.models?.length) {
        setModels(res.models);
        if (!selectedModel) setSelectedModel(res.models[0].id);
      }
    } catch {}
  }, [selectedModel]);

  const refreshSkills = useCallback(async () => {
    setSkillsLoading(true);
    try {
      const res = await getSkills();
      if (res.online) setSkills(res.skills || []);
    } catch {}
    setSkillsLoading(false);
  }, []);

  useEffect(() => {
    if (skillsPanelOpen && skills.length === 0) {
      refreshSkills();
    }
  }, [skillsPanelOpen, skills.length, refreshSkills]);

  useEffect(() => {
    if (!skillsPanelOpen) return;
    const handleClickOutside = (e) => {
      if (controlsRef.current && !controlsRef.current.contains(e.target)) {
        setSkillsPanelOpen(false);
      }
    };
    const handleEsc = (e) => {
      if (e.key === 'Escape') setSkillsPanelOpen(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEsc);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEsc);
    };
  }, [skillsPanelOpen]);

  const loadConversation = useCallback(async (convId) => {
    if (streaming) return;
    setErrorMsg(null);
    setToolCalls([]);
    setStreamingText('');
    setStreamingThinking('');
    setArtifacts([]);
    setPlanSteps([]);
    setCanExtract(false);
    setSuggestions([]);
    setUploadedFileIds([]);
    setUploadedFileNames([]);
    try {
      const conv = await getConversation(convId);
      setActiveConvId(convId);
      setMessages(conv.messages || []);
      if (conv.model_name) setSelectedModel(conv.model_name);
      setThinkingEnabled(!!conv.thinking_enabled);
      setIsPlanMode(!!conv.is_plan_mode);
    } catch (e) {
      setToast({ message: '加载会话失败', type: 'error' });
    }
  }, [streaming]);

  const handleNewConversation = useCallback(async () => {
    if (streaming) {
      abortControllerRef.current?.abort();
    }
    setErrorMsg(null);
    setToolCalls([]);
    setStreamingText('');
    setStreamingThinking('');
    setArtifacts([]);
    setPlanSteps([]);
    setCanExtract(false);
    setSuggestions([]);
    setUploadedFileIds([]);
    setUploadedFileNames([]);
    setMessages([]);
    setActiveConvId(null);
    setTimeout(() => inputRef.current?.focus(), 0);
  }, [streaming]);

  const handleDeleteConversation = useCallback(async (e, convId) => {
    e.stopPropagation();
    try {
      await deleteConversation(convId);
      if (activeConvId === convId) {
        setActiveConvId(null);
        setMessages([]);
        setCanExtract(false);
      }
      await refreshConversations();
    } catch {
      setToast({ message: '删除会话失败', type: 'error' });
    }
  }, [activeConvId, refreshConversations]);

  const handleToggleSkill = useCallback(async (name, enabled) => {
    try {
      await toggleSkill(name, enabled);
      setSkills(prev => prev.map(s => s.name === name ? { ...s, enabled } : s));
    } catch {
      setToast({ message: '切换技能失败', type: 'error' });
    }
  }, []);

  const handleFileUpload = useCallback(async (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) {
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }
    let convIdForUpload = activeConvId;
    if (!convIdForUpload) {
      setToast({ message: '请先发送一条消息开始对话，再上传文件', type: 'error' });
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }
    try {
      const res = await uploadFiles(convIdForUpload, files);
      const newFileIds = [];
      const newFileNames = [];
      (res.files || []).forEach(f => {
        if (f.file_id && !f.error) {
          newFileIds.push(f.file_id);
          newFileNames.push(f.filename);
        }
      });
      if (newFileIds.length > 0) {
        setUploadedFileIds(prev => [...prev, ...newFileIds]);
        setUploadedFileNames(prev => [...prev, ...newFileNames]);
        setToast({ message: `已上传 ${newFileIds.length} 个文件，将在发送下一条消息时使用`, type: 'success' });
      } else {
        setToast({ message: '文件上传失败', type: 'error' });
      }
    } catch {
      setToast({ message: '文件上传失败', type: 'error' });
    }
    if (fileInputRef.current) fileInputRef.current.value = '';
  }, [activeConvId]);

  const removeUploadedFile = useCallback((idx) => {
    setUploadedFileIds(prev => prev.filter((_, i) => i !== idx));
    setUploadedFileNames(prev => prev.filter((_, i) => i !== idx));
  }, []);

  const handlePolish = useCallback(async () => {
    const text = input.trim();
    if (!text || polishing) return;
    setPolishing(true);
    try {
      const polished = await polishInput(text);
      setPolishPreview({ original: text, polished });
    } catch {
      setToast({ message: '润色失败，请重试', type: 'error' });
    }
    setPolishing(false);
  }, [input, polishing]);

  const handlePolishConfirm = useCallback(() => {
    if (polishPreview) {
      setInput(polishPreview.polished);
      setPolishPreview(null);
      setTimeout(() => handleSend(polishPreview.polished), 50);
    }
  }, [polishPreview]);

  const handlePolishCancel = useCallback(() => {
    setPolishPreview(null);
  }, []);

  const fetchSuggestions = useCallback(async (msgs) => {
    try {
      const s = await getSuggestions(msgs);
      setSuggestions(s || []);
    } catch {
      setSuggestions([]);
    }
  }, []);

  const handleSend = useCallback(async (text) => {
    const msgText = (text ?? input).trim();
    if (!msgText || streaming) return;

    setPolishPreview(null);
    setErrorMsg(null);
    setToolCalls([]);
    setStreamingText('');
    setStreamingThinking('');
    setArtifacts([]);
    setPlanSteps([]);
    setPlanApproved(false);

    const currentFileIds = [...uploadedFileIds];
    const userMsg = { role: 'user', content: msgText };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput('');
    setSuggestions([]);
    setStreaming(true);
    setUploadedFileIds([]);
    setUploadedFileNames([]);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    let convId = activeConvId;
    let replyParts = [];
    let thinkingParts = [];
    let gotError = null;
    let finalCanExtract = false;
    let runId = null;

    try {
      await streamChat({
        message: msgText,
        conversationId: convId || undefined,
        modelName: selectedModel || undefined,
        thinkingEnabled,
        isPlanMode,
        fileIds: currentFileIds.length > 0 ? currentFileIds : undefined,
        signal: controller.signal,
        onEvent: (evt) => {
          if (evt.type === 'meta') {
            if (evt.conversation_id && !convId) {
              convId = evt.conversation_id;
              setActiveConvId(convId);
              refreshConversations();
            }
            if (evt.run_id) runId = evt.run_id;
            finalCanExtract = !!evt.can_extract_task;
          } else if (evt.type === 'text') {
            replyParts.push(evt.content);
            setStreamingText(replyParts.join(''));
          } else if (evt.type === 'thinking') {
            thinkingParts.push(evt.content);
            setStreamingThinking(thinkingParts.join(''));
          } else if (evt.type === 'plan') {
            if (evt.steps && Array.isArray(evt.steps)) {
              setPlanSteps(evt.steps);
            }
          } else if (evt.type === 'artifact') {
            if (evt.artifact) {
              setArtifacts(prev => {
                const exists = prev.some(a => a.path === evt.artifact.path);
                return exists ? prev : [...prev, evt.artifact];
              });
            }
          } else if (evt.type === 'tool') {
            setToolCalls(prev => {
              const existing = prev.find(t => t.name === evt.name);
              if (existing) return prev;
              return [...prev, { name: evt.name, input: evt.input }];
            });
          } else if (evt.type === 'error') {
            gotError = evt.message;
          } else if (evt.type === 'done') {
            finalCanExtract = !!evt.can_extract_task;
            if (evt.thinking) setStreamingThinking(evt.thinking);
            if (evt.artifacts) setArtifacts(evt.artifacts);
            if (evt.plan_steps) setPlanSteps(evt.plan_steps);
            if (evt.run_id) runId = evt.run_id;
          }
        },
      });
    } catch (err) {
      if (err.name !== 'AbortError') {
        gotError = err.message || '对话出错';
      }
    }

    abortControllerRef.current = null;
    setStreaming(false);

    if (gotError) {
      setErrorMsg(gotError);
      setStreamingText('');
      setStreamingThinking('');
    } else if (replyParts.length > 0) {
      const fullReply = replyParts.join('');
      const fullThinking = thinkingParts.join('');
      setStreamingText('');
      setStreamingThinking('');
      const assistantMsg = {
        role: 'assistant',
        content: fullReply,
        thinking: fullThinking,
        artifacts: [...artifacts],
        planSteps: [...planSteps],
        runId: runId || `run_${Date.now()}`,
      };
      const finalMessages = [...newMessages, assistantMsg];
      setMessages(finalMessages);
      setCurrentRunId(assistantMsg.runId);
      setCanExtract(finalCanExtract);
      if (convId && !activeConvId) {
        try {
          await updateConversation(convId, {
            title: msgText.slice(0, 30) + (msgText.length > 30 ? '…' : ''),
          });
          refreshConversations();
        } catch {}
      }
      if (finalCanExtract) {
        fetchSuggestions(finalMessages.slice(-6));
      }
      setTimeout(() => inputRef.current?.focus(), 0);
    } else {
      setStreamingText('');
      setStreamingThinking('');
    }
  }, [input, streaming, messages, activeConvId, selectedModel, thinkingEnabled, isPlanMode, uploadedFileIds, refreshConversations, fetchSuggestions, artifacts, planSteps]);

  const handleCancel = useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setStreaming(false);
    setStreamingText('');
  }, []);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !polishPreview) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleAcceptTask = async () => {
    if (extracting) return;
    setExtracting(true);
    try {
      const msgsForApi = messages.map(m => ({ role: m.role, content: m.content }));
      const res = await extractTask({
        student_email: student?.email || '',
        messages: msgsForApi,
      });
      const taskId = res?.data?.task?.id;
      if (taskId != null) {
        setToast({ message: '微行动任务已创建！', type: 'success' });
        setCanExtract(false);
      }
    } catch (err) {
      setToast({
        message: err.response?.data?.detail || '生成任务失败，请稍后再试',
        type: 'error',
      });
    }
    setExtracting(false);
  };

  const handleFeedback = useCallback(async (rating) => {
    if (!activeConvId || !currentRunId) return;
    try {
      await submitFeedback(activeConvId, currentRunId, { rating });
    } catch {
      // Silently fail
    }
  }, [activeConvId, currentRunId]);

  const handlePlanApprove = useCallback(() => {
    setPlanApproved(true);
    setToast({ message: '计划已确认，开始执行', type: 'success' });
  }, []);

  const handlePlanStepUpdate = useCallback((idx, newText) => {
    setPlanSteps(prev => prev.map((step, i) => {
      if (i === idx) {
        if (typeof step === 'string') return newText;
        return { ...step, title: newText, description: newText };
      }
      return step;
    }));
  }, []);

  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, streamingText, streamingThinking, toolCalls, errorMsg, artifacts, planSteps]);

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  const formatTime = (dateStr) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
    } catch { return ''; }
  };

  if (sessionLoading) {
    return (
      <div className="workspace-state">
        <div className="workspace-state-card">
          <div className="workspace-state-mark">ID</div>
          <h2>正在恢复登录状态</h2>
          <p>正在读取你的 Awake 会话…</p>
        </div>
      </div>
    );
  }

  if (!student) {
    return (
      <div className="workspace-state">
        <div className="workspace-state-card">
          <div className="workspace-state-mark">小海</div>
          <h2>先登录，小海在这里等你</h2>
          <p>与小海的对话需要一个专属入口。登录后直接回到对话空间。</p>
          <Link to="/login" className="workspace-primary-link">登录已有账号 →</Link>
          <Link to="/register" className="workspace-secondary-link">还没有账号？先注册</Link>
        </div>
      </div>
    );
  }

  const showWelcome = messages.length === 0 && !streaming;

  return (
    <>
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      <div className="chat-page">
        <div className={`chat-conv-sidebar${convListOpen ? ' is-open' : ''}`}>
          <div className="chat-conv-header">
            <span className="chat-conv-title">对话记录</span>
            <button className="chat-icon-btn" onClick={handleNewConversation} title="新对话">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M12 5v14M5 12h14" /></svg>
            </button>
          </div>
          <div className="chat-conv-list">
            {conversations.length === 0 && (
              <div className="chat-conv-empty">暂无历史对话</div>
            )}
            {conversations.map(conv => (
              <div
                key={conv.id}
                className={`chat-conv-item${activeConvId === conv.id ? ' is-active' : ''}`}
                onClick={() => loadConversation(conv.id)}
              >
                <div className="chat-conv-item-title">{conv.title || '新对话'}</div>
                <div className="chat-conv-item-meta">
                  <span>{formatTime(conv.updated_at)}</span>
                  {conv.model_name && <span className="chat-conv-model">{conv.model_name}</span>}
                </div>
                <button
                  className="chat-conv-delete"
                  onClick={(e) => handleDeleteConversation(e, conv.id)}
                  title="删除"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" /></svg>
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="chat-main">
          <div className="chat-container">
            <div className="chat-header">
              <div className="chat-header-left">
                <button
                  className="chat-icon-btn chat-toggle-conv"
                  onClick={() => setConvListOpen(!convListOpen)}
                  title={convListOpen ? '隐藏对话列表' : '显示对话列表'}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M3 6h18M3 12h18M3 18h18" /></svg>
                </button>
                <div className="chat-avatar chat-avatar-lg">🌊</div>
                <div className="chat-header-text">
                  <h1 className="chat-title">与小海对话</h1>
                  <p className="chat-subtitle">
                    {student?.name ? `${student.name}，` : ''}跟着好奇心聊聊，让我陪你找到今天的一小步。
                  </p>
                </div>
              </div>
              <div className="chat-header-controls" ref={controlsRef}>
                {models.length > 0 && (
                  <select
                    className="chat-model-select"
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    disabled={streaming}
                    title="选择模型"
                  >
                    {models.map(m => (
                      <option key={m.id} value={m.id}>{m.name || m.id}</option>
                    ))}
                  </select>
                )}

                <button
                  className={`chat-toggle-btn${thinkingEnabled ? ' is-active' : ''}`}
                  onClick={() => setThinkingEnabled(!thinkingEnabled)}
                  disabled={streaming}
                  title={thinkingEnabled ? '深度思考已开启' : '开启深度思考'}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z" /><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z" /></svg>
                  思考
                </button>

                <button
                  className={`chat-toggle-btn${isPlanMode ? ' is-active' : ''}`}
                  onClick={() => setIsPlanMode(!isPlanMode)}
                  disabled={streaming}
                  title={isPlanMode ? '计划模式已开启' : '开启计划模式'}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" /></svg>
                  计划
                </button>

                <button
                  className="chat-icon-btn"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={streaming}
                  title="上传文件"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 17.93 8.8l-8.58 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48" /></svg>
                </button>
                <input ref={fileInputRef} type="file" multiple style={{ display: 'none' }} onChange={handleFileUpload} />

                <button
                  className={`chat-icon-btn${skillsPanelOpen ? ' is-active' : ''}`}
                  onClick={() => setSkillsPanelOpen(!skillsPanelOpen)}
                  title="技能面板"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z" /></svg>
                </button>

                <button
                  type="button"
                  className="chat-new-btn"
                  onClick={handleNewConversation}
                  title="新对话"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M12 5v14M5 12h14" /></svg>
                  新对话
                </button>

                {skillsPanelOpen && (
                  <div className="chat-skills-panel" onClick={e => e.stopPropagation()}>
                    <div className="chat-skills-header">
                      <span>Tools</span>
                      <button className="chat-icon-btn" onClick={refreshSkills} title="刷新">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" style={{width:14,height:14}}><path d="M21 12a9 9 0 1 1-9-9c2.5 0 4.8 1 6.5 2.7L21 8" /><path d="M21 3v5h-5" /></svg>
                      </button>
                    </div>
                    <div className="chat-skills-list">
                      {skillsLoading && <div className="chat-skills-empty">加载中…</div>}
                      {!skillsLoading && skills.length === 0 && <div className="chat-skills-empty">暂无技能</div>}
                      {skills.map(s => (
                        <label key={s.name} className="chat-skill-item">
                          <input
                            type="checkbox"
                            checked={s.enabled !== false}
                            onChange={(e) => handleToggleSkill(s.name, e.target.checked)}
                          />
                          <div className="chat-skill-info">
                            <span className="chat-skill-name">{s.name}</span>
                            {s.description && <span className="chat-skill-desc">{s.description}</span>}
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {canExtract && !streaming && (
              <div className="chat-extract-card">
                <div className="chat-extract-copy">
                  <div className="chat-extract-title">✨ 灵感已就绪</div>
                  <div className="chat-extract-desc">
                    小海从这次对话里为你准备了一个微行动任务。
                  </div>
                </div>
                <button className="chat-extract-btn" onClick={handleAcceptTask} disabled={extracting}>
                  {extracting ? '生成中…' : '提炼微行动'}
                </button>
              </div>
            )}

            <div className="chat-messages">
              {showWelcome && (
                <div className="chat-welcome">
                  <div className="chat-welcome-avatar">🌊</div>
                  <div className="chat-welcome-text">
                    <h2>你好，{student?.name}！</h2>
                    {welcomeMessage.split('\n\n').map((para, i) => (
                      <p key={i}>{para}</p>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((msg, idx) => (
                msg.role === 'user' ? (
                  <div key={idx} className="chat-row chat-row-user">
                    <div className="chat-bubble chat-bubble-user">{msg.content}</div>
                  </div>
                ) : (
                  <div key={idx} className="chat-row chat-row-ai">
                    <div className="chat-avatar chat-avatar-sm">🌊</div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      {msg.thinking && (
                        <PerMessageThinking content={msg.thinking} defaultOpen={thinkingEnabled} />
                      )}
                      {msg.planSteps && msg.planSteps.length > 0 && !msg.planApproved && (
                        <PlanBlock
                          steps={msg.planSteps}
                          onApprove={() => {
                            setMessages(prev => prev.map((m, i) =>
                              i === idx ? { ...m, planApproved: true } : m
                            ));
                            setToast({ message: '计划已确认，开始执行', type: 'success' });
                          }}
                          onEdit={() => {}}
                          onStepUpdate={(stepIdx, newText) => {
                            setMessages(prev => prev.map((m, i) => {
                              if (i !== idx) return m;
                              const newSteps = (m.planSteps || []).map((s, si) => {
                                if (si !== stepIdx) return s;
                                if (typeof s === 'string') return newText;
                                return { ...s, title: newText, description: newText };
                              });
                              return { ...m, planSteps: newSteps };
                            }));
                          }}
                        />
                      )}
                      <div className="chat-bubble chat-bubble-ai"><MarkdownMessage content={msg.content} /></div>
                      {msg.artifacts && msg.artifacts.length > 0 && (
                        <div className="chat-artifacts">
                          {msg.artifacts.map((a, ai) => (
                            <ArtifactCard key={ai} artifact={a} />
                          ))}
                        </div>
                      )}
                      {idx === messages.length - 1 && !streaming && <FeedbackButtons onFeedback={handleFeedback} />}
                    </div>
                  </div>
                )
              ))}

              {streaming && (
                <div className="chat-row chat-row-ai">
                  <div className="chat-avatar chat-avatar-sm">🌊</div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    {(streamingThinking || thinkingEnabled) && (
                      <ThinkingBlock
                        content={streamingThinking}
                        streaming={!streamingText}
                        open={thinkingOpen}
                        onToggle={() => setThinkingOpen(!thinkingOpen)}
                      />
                    )}
                    {planSteps.length > 0 && (
                      <PlanBlock
                        steps={planSteps}
                        onApprove={handlePlanApprove}
                        onEdit={() => {}}
                        onStepUpdate={handlePlanStepUpdate}
                      />
                    )}
                    <div className="chat-bubble chat-bubble-ai">
                      {toolCalls.length > 0 && (
                        <div className="chat-tools">
                          {toolCalls.map((tc, i) => (
                            <div key={i} className="chat-tool-tag">
                              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z" /></svg>
                              {tc.name}
                            </div>
                          ))}
                        </div>
                      )}
                      {streamingText ? (
                        <span className="chat-streaming-md"><MarkdownMessage content={streamingText} /></span>
                      ) : (
                        <span className="chat-typing-label">
                          <span className="chat-dots" aria-hidden="true">
                            <span></span><span></span><span></span>
                          </span>
                          小海正在思考…
                        </span>
                      )}
                    </div>
                    {artifacts.length > 0 && (
                      <div className="chat-artifacts">
                        {artifacts.map((a, ai) => (
                          <ArtifactCard key={ai} artifact={a} />
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {streaming && (
                <div className="chat-row chat-row-ai">
                  <button className="chat-cancel-btn" onClick={handleCancel}>停止生成</button>
                </div>
              )}

              {errorMsg && !streaming && (
                <div className="chat-retry-card" role="status">
                  <span>⚠️ {errorMsg}</span>
                  <button className="chat-inline-action" onClick={() => { setErrorMsg(null); inputRef.current?.focus(); }}>
                    重新输入
                  </button>
                </div>
              )}

              {!streaming && suggestions.length > 0 && (
                <div className="chat-suggestions">
                  {suggestions.map((s, i) => (
                    <button key={i} className="chat-suggestion-chip" onClick={() => { setInput(s); setTimeout(() => handleSend(s), 0); }}>
                      {s}
                    </button>
                  ))}
                </div>
              )}

              <div ref={scrollAnchorRef} />
            </div>

            <div className="chat-input-wrapper">
              {uploadedFileNames.length > 0 && (
                <div className="chat-uploaded-files">
                  {uploadedFileNames.map((name, idx) => (
                    <span key={idx} className="chat-uploaded-file">
                      📎 {name}
                      <button className="chat-uploaded-file-remove" onClick={() => removeUploadedFile(idx)} title="移除">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round"><path d="M18 6 6 18M6 6l12 12" /></svg>
                      </button>
                    </span>
                  ))}
                </div>
              )}

              {polishPreview && (
                <div className="chat-polish-preview">
                  <div className="chat-polish-preview-title">
                    ✨ 润色建议
                  </div>
                  <div className="chat-polish-preview-text">{polishPreview.polished}</div>
                  <div className="chat-polish-preview-actions">
                    <button className="chat-polish-preview-btn chat-polish-preview-btn-cancel" onClick={handlePolishCancel}>取消</button>
                    <button className="chat-polish-preview-btn chat-polish-preview-btn-send" onClick={handlePolishConfirm}>发送润色后内容</button>
                  </div>
                </div>
              )}

              <div className="chat-input-bar">
                <button
                  className={`chat-polish-btn${polishing ? ' is-polishing' : ''}`}
                  onClick={handlePolish}
                  disabled={streaming || !input.trim() || polishing}
                  title="润色输入"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z" />
                  </svg>
                </button>
                <textarea
                  ref={inputRef}
                  className="chat-input"
                  aria-label="输入给小海的消息"
                  placeholder={streaming ? '小海正在思考…' : '说点什么，回车发送（Shift+Enter 换行）'}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={streaming}
                  rows={1}
                />
                <button
                  className="chat-send-btn"
                  onClick={() => handleSend()}
                  disabled={streaming || !input.trim()}
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
        </div>
      </div>
    </>
  );
};

export default Chat;
