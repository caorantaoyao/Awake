import { useEffect, useMemo, useState, useCallback } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  getDeerflowStatus, getModels, getSkills, toggleSkill,
  listMcpServers, listRuns, listScheduledTasks, createScheduledTask,
} from '../api/client';

const createOfflineStatus = (message) => ({
  online: false,
  label: '离线',
  assistant_id: 'lead_agent',
  model: null,
  error: message
});

const createOfflineSkills = (message) => ({
  online: false,
  skills: [],
  error: message
});

const createOfflineModels = (message) => ({
  online: false,
  models: [],
  error: message
});

const getEnabledLabel = (enabled) => {
  if (enabled === true) return '已启用';
  if (enabled === false) return '已停用';
  return '未知';
};

const formatDuration = (ms) => {
  if (!ms || ms < 0) return '-';
  if (ms < 1000) return `${ms}ms`;
  const s = ms / 1000;
  if (s < 60) return `${s.toFixed(1)}s`;
  const m = Math.floor(s / 60);
  const rs = Math.round(s % 60);
  return `${m}m ${rs}s`;
};

const formatTime = (dateStr) => {
  try {
    const d = new Date(dateStr);
    return d.toLocaleString('zh-CN', {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  } catch { return '-'; }
};

const formatTokens = (t) => {
  if (!t && t !== 0) return '-';
  if (t >= 1000) return `${(t / 1000).toFixed(1)}k`;
  return `${t}`;
};

const getMcpIcon = (name, type) => {
  const n = (name || '').toLowerCase();
  const t = (type || '').toLowerCase();
  if (n.includes('web') || n.includes('search') || t.includes('search')) return '🔍';
  if (n.includes('file') || n.includes('fs') || t.includes('filesystem')) return '📁';
  if (n.includes('git') || n.includes('code') || t.includes('code')) return '💻';
  if (n.includes('db') || n.includes('database') || n.includes('sql')) return '🗄️';
  if (n.includes('browser') || n.includes('web') || t.includes('browser')) return '🌐';
  if (n.includes('doc') || n.includes('wiki') || t.includes('document')) return '📚';
  if (n.includes('mail') || n.includes('email')) return '📧';
  if (n.includes('calendar') || n.includes('schedule')) return '📅';
  return '🔌';
};

const getRunStatusStyle = (status) => {
  const s = (status || '').toLowerCase();
  if (s === 'success' || s === 'completed' || s === 'done') return { bg: '#dcfce7', color: '#166534', label: '成功' };
  if (s === 'running' || s === 'pending') return { bg: '#dbeafe', color: '#1e40af', label: '运行中' };
  if (s === 'error' || s === 'failed') return { bg: '#fee2e2', color: '#991b1b', label: '失败' };
  if (s === 'cancelled' || s === 'aborted') return { bg: '#f3f4f6', color: '#4b5563', label: '已取消' };
  return { bg: '#f3f4f6', color: '#6b7280', label: status || '未知' };
};

const getTaskTypeLabel = (type) => {
  const t = (type || '').toLowerCase();
  if (t.includes('daily') || t.includes('reminder')) return '每日提醒';
  if (t.includes('weekly') || t.includes('summary')) return '每周摘要';
  if (t.includes('report')) return '报告生成';
  if (t.includes('check')) return '检查任务';
  return type || '定时任务';
};

const Capabilities = () => {
  const outletContext = useOutletContext() || {};
  const workspaceStatus = outletContext.deerflowStatus;
  const workspaceCurrentModel = outletContext.currentModel;
  const refreshWorkspaceDeerflowStatus = outletContext.refreshDeerflowStatus;

  const [status, setStatus] = useState(() => workspaceStatus || null);
  const [skillsResponse, setSkillsResponse] = useState(null);
  const [modelsResponse, setModelsResponse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [togglingSkill, setTogglingSkill] = useState('');
  const [notice, setNotice] = useState('');

  const [mcpServers, setMcpServers] = useState([]);
  const [mcpLoading, setMcpLoading] = useState(false);
  const [runs, setRuns] = useState([]);
  const [runsLoading, setRunsLoading] = useState(false);
  const [scheduledTasks, setScheduledTasks] = useState([]);
  const [tasksLoading, setTasksLoading] = useState(false);
  const [taskCreating, setTaskCreating] = useState(false);
  const [showTaskForm, setShowTaskForm] = useState(false);
  const [newTask, setNewTask] = useState({ type: 'daily_reminder', schedule: '09:00', prompt: '' });

  const skills = skillsResponse?.skills || [];
  const models = modelsResponse?.models || [];
  const hasOfflineSignal =
    status?.online === false || skillsResponse?.online === false || modelsResponse?.online === false;
  const currentModel =
    status?.model || workspaceCurrentModel || models[0]?.name || models[0]?.id || '未返回模型';

  const offlineReason = useMemo(() => {
    if (!hasOfflineSignal) return '';
    return (
      status?.error ||
      skillsResponse?.error ||
      modelsResponse?.error ||
      'DeerFlow gateway 当前不可达，控制台已进入只读降级态。'
    );
  }, [hasOfflineSignal, modelsResponse, skillsResponse, status]);

  const fetchMcp = useCallback(async () => {
    setMcpLoading(true);
    try {
      const data = await listMcpServers();
      setMcpServers(data?.servers || data?.mcp_servers || Array.isArray(data) ? data : []);
    } catch {
      setMcpServers([]);
    }
    setMcpLoading(false);
  }, []);

  const fetchRuns = useCallback(async () => {
    setRunsLoading(true);
    try {
      const data = await listRuns();
      setRuns(Array.isArray(data) ? data : []);
    } catch {
      setRuns([]);
    }
    setRunsLoading(false);
  }, []);

  const fetchTasks = useCallback(async () => {
    setTasksLoading(true);
    try {
      const data = await listScheduledTasks();
      setScheduledTasks(data?.tasks || Array.isArray(data) ? data : []);
    } catch {
      setScheduledTasks([]);
    }
    setTasksLoading(false);
  }, []);

  const loadCapabilities = async ({ silent = false } = {}) => {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setNotice('');

    const [statusResult, skillsResult, modelsResult] = await Promise.allSettled([
      refreshWorkspaceDeerflowStatus ? refreshWorkspaceDeerflowStatus() : getDeerflowStatus(),
      getSkills(),
      getModels()
    ]);

    setStatus(
      statusResult.status === 'fulfilled'
        ? statusResult.value
        : createOfflineStatus('状态接口请求失败')
    );
    setSkillsResponse(
      skillsResult.status === 'fulfilled'
        ? skillsResult.value
        : createOfflineSkills('Skills 接口请求失败')
    );
    setModelsResponse(
      modelsResult.status === 'fulfilled'
        ? modelsResult.value
        : createOfflineModels('Models 接口请求失败')
    );

    await Promise.allSettled([fetchMcp(), fetchRuns(), fetchTasks()]);

    setLoading(false);
    setRefreshing(false);
  };

  useEffect(() => {
    loadCapabilities();
  }, []);

  useEffect(() => {
    if (workspaceStatus) {
      setStatus(workspaceStatus);
    }
  }, [workspaceStatus]);

  const handleToggleSkill = async (skill) => {
    if (!skill?.name || togglingSkill) return;

    const nextEnabled = skill.enabled !== true;
    setTogglingSkill(skill.name);
    setNotice('');

    try {
      const result = await toggleSkill(skill.name, nextEnabled);
      if (result.online === false) {
        setNotice(result.error || 'DeerFlow 离线，未能切换 skill。');
        setSkillsResponse((prev) => ({ ...(prev || {}), online: false }));
        return;
      }

      const nextSkill = result.skill || { ...skill, enabled: nextEnabled };
      setSkillsResponse((prev) => ({
        ...(prev || { online: true, skills: [] }),
        online: true,
        skills: (prev?.skills || []).map((item) =>
          item.name === skill.name ? { ...item, ...nextSkill } : item
        )
      }));
    } catch (err) {
      setNotice(err.response?.data?.detail || 'Skill 开关请求失败，请稍后重试。');
    } finally {
      setTogglingSkill('');
    }
  };

  const handleCreateTask = async () => {
    if (!newTask.prompt.trim()) return;
    setTaskCreating(true);
    try {
      await createScheduledTask(newTask);
      setShowTaskForm(false);
      setNewTask({ type: 'daily_reminder', schedule: '09:00', prompt: '' });
      await fetchTasks();
      setNotice('定时任务创建成功');
      setTimeout(() => setNotice(''), 3000);
    } catch (err) {
      setNotice(err.response?.data?.detail || '创建定时任务失败');
    }
    setTaskCreating(false);
  };

  if (loading) {
    return (
      <section className="workspace-view">
        <div className="workspace-state-card is-inline">
          <div className="workspace-state-mark">DF</div>
          <h2>正在读取 DeerFlow 能力</h2>
          <p>正在同步已加载的 skills、模型列表和当前对话引擎状态。</p>
        </div>
      </section>
    );
  }

  return (
    <section className="workspace-view capabilities-view">
      <div className="workspace-view-header">
        <div>
          <span className="workspace-kicker">DEERFLOW CONTROL</span>
          <h2>能力控制</h2>
          <p>查看 DeerFlow gateway 暴露的 skills、模型、MCP 服务器、运行历史与定时任务。</p>
        </div>
        <button
          type="button"
          className="workspace-secondary-button"
          onClick={() => loadCapabilities({ silent: true })}
          disabled={refreshing}
        >
          {refreshing ? '刷新中...' : '重试 / 刷新'}
        </button>
      </div>

      {hasOfflineSignal && (
        <div className="workspace-alert is-warning">
          <span>对话引擎离线</span>
          <p>{offlineReason}</p>
        </div>
      )}

      {notice && (
        <div className="workspace-alert is-info">
          <span>提示</span>
          <p>{notice}</p>
        </div>
      )}

      <div className="capability-summary-grid">
        <article className="workspace-metric-card">
          <span>DeerFlow</span>
          <strong>{status?.online ? '在线' : '离线'}</strong>
          <p>{status?.assistant_id || 'assistant_id 未返回'}</p>
        </article>
        <article className="workspace-metric-card">
          <span>当前模型</span>
          <strong>{currentModel}</strong>
          <p>由 `/deerflow/status` 或模型列表推断</p>
        </article>
        <article className="workspace-metric-card">
          <span>Skills</span>
          <strong>{skills.length}</strong>
          <p>{skillsResponse?.online === false ? '离线降级为空列表' : '已加载能力数量'}</p>
        </article>
        <article className="workspace-metric-card">
          <span>MCP 服务器</span>
          <strong>{mcpServers.length}</strong>
          <p>{mcpLoading ? '加载中...' : '已连接外部工具'}</p>
        </article>
        <article className="workspace-metric-card">
          <span>运行记录</span>
          <strong>{runs.length}</strong>
          <p>{runsLoading ? '加载中...' : '历史 Run 数量'}</p>
        </article>
        <article className="workspace-metric-card">
          <span>定时任务</span>
          <strong>{scheduledTasks.length}</strong>
          <p>{tasksLoading ? '加载中...' : '已调度任务数量'}</p>
        </article>
      </div>

      <div className="workspace-two-column">
        <section className="workspace-panel">
          <div className="workspace-panel-head">
            <div>
              <h3>Skills 开关</h3>
              <p>切换会调用 Awaken 后端代理，再转发到 DeerFlow。</p>
            </div>
          </div>

          {skills.length === 0 ? (
            <div className="panel-empty">
              {skillsResponse?.online === false ? 'DeerFlow 离线，暂无可展示 skills。' : '暂无 skills。'}
            </div>
          ) : (
            <div className="skill-list">
              {skills.map((skill) => {
                const isToggling = togglingSkill === skill.name;
                const enabled = skill.enabled === true;
                return (
                  <article key={skill.name} className="skill-row">
                    <div className="skill-row-copy">
                      <div className="skill-row-title">
                        <strong>{skill.name}</strong>
                        <span className={enabled ? 'is-enabled' : 'is-disabled'}>
                          {getEnabledLabel(skill.enabled)}
                        </span>
                      </div>
                      <p>{skill.description || 'DeerFlow 未返回描述。'}</p>
                    </div>
                    <button
                      type="button"
                      className={`skill-switch${enabled ? ' is-on' : ''}`}
                      onClick={() => handleToggleSkill(skill)}
                      disabled={isToggling || hasOfflineSignal}
                      aria-pressed={enabled}
                    >
                      <span>{isToggling ? '...' : enabled ? 'ON' : 'OFF'}</span>
                    </button>
                  </article>
                );
              })}
            </div>
          )}
        </section>

        <section className="workspace-panel">
          <div className="workspace-panel-head">
            <div>
              <h3>模型列表</h3>
              <p>用于确认当前 gateway 可选择的模型能力。</p>
            </div>
          </div>

          {models.length === 0 ? (
            <div className="panel-empty">
              {modelsResponse?.online === false ? 'DeerFlow 离线，暂无模型列表。' : '暂无模型。'}
            </div>
          ) : (
            <div className="model-list">
              {models.map((model) => (
                <article key={model.id} className="model-row">
                  <div>
                    <strong>{model.name || model.id}</strong>
                    <p>{model.id}</p>
                  </div>
                  <span>{model.provider || 'provider 未返回'}</span>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>

      <div className="workspace-two-column">
        <section className="workspace-panel">
          <div className="workspace-panel-head">
            <div>
              <h3>MCP 服务器</h3>
              <p>DeerFlow 已连接的外部工具服务器（Model Context Protocol）。</p>
            </div>
            <button
              type="button"
              className="workspace-mini-button"
              onClick={fetchMcp}
              disabled={mcpLoading}
            >
              {mcpLoading ? '...' : '刷新'}
            </button>
          </div>

          {mcpLoading ? (
            <div className="panel-empty">加载中...</div>
          ) : mcpServers.length === 0 ? (
            <div className="panel-empty">暂无 MCP 服务器连接。</div>
          ) : (
            <div className="mcp-list">
              {mcpServers.map((server, idx) => {
                const name = server.name || server.id || `server-${idx}`;
                const tools = server.tools || server.capabilities || [];
                const connected = server.connected !== false && server.status !== 'disconnected';
                return (
                  <article key={idx} className="mcp-row">
                    <div className="mcp-row-icon">{getMcpIcon(name, server.type)}</div>
                    <div className="mcp-row-copy">
                      <div className="mcp-row-title">
                        <strong>{name}</strong>
                        <span className={`mcp-status${connected ? ' is-connected' : ' is-disconnected'}`}>
                          {connected ? '已连接' : '未连接'}
                        </span>
                      </div>
                      {server.description && <p>{server.description}</p>}
                      {tools.length > 0 && (
                        <div className="mcp-tools">
                          {Array.isArray(tools) && tools.slice(0, 6).map((t, ti) => (
                            <span key={ti} className="mcp-tool-tag">
                              {typeof t === 'string' ? t : t.name || JSON.stringify(t).slice(0, 20)}
                            </span>
                          ))}
                          {tools.length > 6 && <span className="mcp-tool-more">+{tools.length - 6}</span>}
                        </div>
                      )}
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>

        <section className="workspace-panel">
          <div className="workspace-panel-head">
            <div>
              <h3>Run 历史</h3>
              <p>最近的对话运行记录，包含耗时、Token 用量与工具调用情况。</p>
            </div>
            <button
              type="button"
              className="workspace-mini-button"
              onClick={fetchRuns}
              disabled={runsLoading}
            >
              {runsLoading ? '...' : '刷新'}
            </button>
          </div>

          {runsLoading ? (
            <div className="panel-empty">加载中...</div>
          ) : runs.length === 0 ? (
            <div className="panel-empty">暂无运行记录。</div>
          ) : (
            <div className="runs-list">
              {runs.slice(0, 20).map((run, idx) => {
                const status = getRunStatusStyle(run.status);
                const duration = run.duration_ms || run.duration || (run.started_at && run.ended_at
                  ? new Date(run.ended_at) - new Date(run.started_at) : null);
                return (
                  <article key={run.id || run.run_id || idx} className="run-row">
                    <div className="run-row-header">
                      <span className="run-id">{(run.id || run.run_id || '').toString().slice(0, 12)}...</span>
                      <span className="run-status-badge" style={{ background: status.bg, color: status.color }}>
                        {status.label}
                      </span>
                    </div>
                    <div className="run-row-meta">
                      {run.model && <span className="run-meta-item">🤖 {run.model}</span>}
                      {duration && <span className="run-meta-item">⏱ {formatDuration(duration)}</span>}
                      {(run.tokens || run.usage) && (
                        <span className="run-meta-item">
                          📊 {formatTokens(run.tokens?.input || run.usage?.input_tokens || run.input_tokens)}
                          {' / '}
                          {formatTokens(run.tokens?.output || run.usage?.output_tokens || run.output_tokens)} tok
                        </span>
                      )}
                    </div>
                    {run.created_at && (
                      <div className="run-row-time">{formatTime(run.created_at)}</div>
                    )}
                  </article>
                );
              })}
            </div>
          )}
        </section>
      </div>

      <section className="workspace-panel workspace-panel-full">
        <div className="workspace-panel-head">
          <div>
            <h3>定时任务</h3>
            <p>配置自动化任务，如每日提醒、每周学习摘要等。</p>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              type="button"
              className="workspace-mini-button"
              onClick={fetchTasks}
              disabled={tasksLoading}
            >
              {tasksLoading ? '...' : '刷新'}
            </button>
            <button
              type="button"
              className="workspace-primary-button"
              onClick={() => setShowTaskForm(!showTaskForm)}
            >
              {showTaskForm ? '取消' : '+ 新建任务'}
            </button>
          </div>
        </div>

        {showTaskForm && (
          <div className="task-form">
            <div className="task-form-row">
              <label>任务类型</label>
              <select
                value={newTask.type}
                onChange={(e) => setNewTask(prev => ({ ...prev, type: e.target.value }))}
                className="task-form-input"
              >
                <option value="daily_reminder">每日提醒</option>
                <option value="weekly_summary">每周摘要</option>
                <option value="daily_report">每日报告</option>
                <option value="check_in_check">打卡检查</option>
              </select>
            </div>
            <div className="task-form-row">
              <label>执行时间</label>
              <input
                type="time"
                value={newTask.schedule}
                onChange={(e) => setNewTask(prev => ({ ...prev, schedule: e.target.value }))}
                className="task-form-input"
              />
            </div>
            <div className="task-form-row">
              <label>任务内容</label>
              <textarea
                value={newTask.prompt}
                onChange={(e) => setNewTask(prev => ({ ...prev, prompt: e.target.value }))}
                placeholder="例如：每天早上提醒我回顾昨天的学习进度，并生成今日的微行动建议"
                className="task-form-input task-form-textarea"
                rows={3}
              />
            </div>
            <div className="task-form-actions">
              <button
                type="button"
                className="workspace-secondary-button"
                onClick={() => setShowTaskForm(false)}
              >
                取消
              </button>
              <button
                type="button"
                className="workspace-primary-button"
                onClick={handleCreateTask}
                disabled={taskCreating || !newTask.prompt.trim()}
              >
                {taskCreating ? '创建中...' : '创建任务'}
              </button>
            </div>
          </div>
        )}

        {tasksLoading ? (
          <div className="panel-empty">加载中...</div>
        ) : scheduledTasks.length === 0 ? (
          <div className="panel-empty">暂无定时任务。点击"新建任务"创建一个。</div>
        ) : (
          <div className="tasks-list">
            {scheduledTasks.map((task, idx) => {
              const typeLabel = getTaskTypeLabel(task.type);
              const enabled = task.enabled !== false;
              return (
                <article key={task.id || idx} className="task-row">
                  <div className="task-row-icon">⏰</div>
                  <div className="task-row-copy">
                    <div className="task-row-title">
                      <strong>{task.name || task.prompt?.slice(0, 30) || typeLabel}</strong>
                      <span className={`task-status${enabled ? ' is-enabled' : ' is-disabled'}`}>
                        {enabled ? '启用中' : '已停用'}
                      </span>
                    </div>
                    <p>{task.prompt || '无描述'}</p>
                    <div className="task-row-meta">
                      <span className="task-type-badge">{typeLabel}</span>
                      <span className="task-schedule">🕐 {task.schedule || task.cron || '-'}</span>
                      {task.last_run && <span className="task-last-run">上次执行: {formatTime(task.last_run)}</span>}
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </section>
  );
};

export default Capabilities;
