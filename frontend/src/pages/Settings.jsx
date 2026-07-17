import { useEffect, useMemo, useState, useCallback } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  healthCheck,
  getPreferences,
  updatePreferences,
  getCurrentStudent,
  saveAuthSession,
  getStoredStudent,
  getAuthToken,
} from '../api/client';

const CHAT_MODE_OPTIONS = [
  { value: 'explore_first', label: '先探索，再行动', desc: '小海会先理解你的想法，不急着替你下结论。' },
  { value: 'balanced', label: '平衡模式', desc: '适时追问，也适时给出建议，在探索和行动间保持平衡。' },
  { value: 'direct_action', label: '直接给建议', desc: '减少追问，更快进入可行动的方向。' },
];

const UNLOCK_OPTIONS = [
  { value: 2, label: '快速解锁', desc: '2 轮对话后即可生成微行动' },
  { value: 3, label: '推荐', desc: '3 轮对话后生成微行动' },
  { value: 5, label: '深入探索', desc: '5 轮对话后再生成微行动' },
];

const Settings = () => {
  const outletContext = useOutletContext() || {};
  const student = outletContext.student;
  const setStudent = outletContext.setStudent;
  const status = outletContext.deerflowStatus;
  const isAuthenticated = Boolean(student?.email);

  const [health, setHealth] = useState(null);
  const [healthError, setHealthError] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [prefs, setPrefs] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState(null);

  const statusLabel = {
    online: '可以对话',
    degraded: '基础模式',
    unreachable: '暂时无法连接',
    private: '按需连接',
  }[status?.availability] || '检测中';
  const statusTone =
    status?.availability === 'online'
      ? 'is-good'
      : ['degraded', 'unreachable'].includes(status?.availability)
        ? 'is-bad'
        : '';

  const healthLabel = useMemo(() => {
    if (health?.status) return '连接正常';
    if (healthError) return '暂时未连接';
    return '检测中';
  }, [health, healthError]);

  const loadSettings = useCallback(async ({ silent = false } = {}) => {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setHealthError('');

    try {
      setHealth(await healthCheck());
    } catch {
      setHealth(null);
      setHealthError('健康检查接口请求失败');
    }

    const defaultPrefs = {
      chat_mode: 'explore_first',
      unlock_after_turns: 3,
      chat_mode_label: '先探索，再行动',
      unlock_label: '探索 3 轮后解锁',
    };

    if (!isAuthenticated) {
      setPrefs(defaultPrefs);
    } else {
      try {
        const p = await getPreferences();
        setPrefs(p);
      } catch {
        setPrefs(defaultPrefs);
      }
    }

    setLoading(false);
    setRefreshing(false);
  }, [isAuthenticated]);

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  const handlePrefChange = useCallback(async (key, value) => {
    if (!prefs || saving || !isAuthenticated) return;
    const nextPrefs = { ...prefs, [key]: value };
    setPrefs(nextPrefs);
    setSaving(true);
    setSaveMessage(null);
    try {
      const updated = await updatePreferences({ [key]: value });
      setPrefs(updated);
      setSaveMessage({ type: 'success', text: '偏好已保存' });
      if (setStudent) {
        try {
          const fresh = await getCurrentStudent();
          const token = getAuthToken();
          if (token) saveAuthSession({ accessToken: token, student: fresh });
          setStudent(fresh);
        } catch {
          // 静默失败
        }
      }
    } catch {
      setPrefs(prefs);
      setSaveMessage({ type: 'error', text: '保存失败，请稍后重试' });
    } finally {
      setSaving(false);
      setTimeout(() => setSaveMessage(null), 2500);
    }
  }, [prefs, saving, setStudent]);

  if (loading) {
    return (
      <section className="workspace-view">
        <div className="workspace-state-card is-inline">
          <div className="workspace-state-mark">HI</div>
          <h2>正在准备你的成长空间</h2>
          <p>正在确认账号信息和小海的可用状态。</p>
        </div>
      </section>
    );
  }

  return (
    <section className="workspace-view settings-view">
      <div className="workspace-view-header">
        <div>
          <span className="workspace-kicker">MY SPACE</span>
          <h2>设置</h2>
          <p>查看你的账号、小海的可用状态，调整对话方式与行动节奏。</p>
        </div>
        <button
          type="button"
          className="workspace-secondary-button"
          onClick={() => loadSettings({ silent: true })}
          disabled={refreshing}
        >
          {refreshing ? '刷新中...' : '刷新状态'}
        </button>
      </div>

      {saveMessage && (
        <div className={`workspace-alert ${saveMessage.type === 'error' ? 'is-error' : 'is-success'}`}>
          <span>{saveMessage.text}</span>
        </div>
      )}

      {status?.availability === 'degraded' && (
        <div className="workspace-alert is-warning">
          <span>小海正在使用基础模式</span>
          <p>增强能力暂时不可用，但你仍然可以继续对话和整理下一步行动。</p>
        </div>
      )}
      {status?.availability === 'unreachable' && (
        <div className="workspace-alert is-error">
          <span>暂时无法连接小海</span>
          <p>当前无法确认对话服务是否可用，请稍后刷新状态。</p>
        </div>
      )}

      <div className="settings-grid">
        <article className="settings-card">
          <span className="settings-label">当前账号</span>
          <strong>{student?.name || '访客同学'}</strong>
          <p>{student?.email || '登录后可保存对话与行动记录'}</p>
        </article>

        <article className="settings-card">
          <span className="settings-label">小海状态</span>
          <strong className={statusTone}>{statusLabel}</strong>
          <p>
            {status?.availability === 'degraded'
              ? '当前使用基础陪伴能力'
              : status?.availability === 'unreachable'
                ? '请稍后刷新状态'
                : status?.availability === 'private'
                  ? '开始对话时自动连接小海'
                  : '可以继续探索你的方向'}
          </p>
        </article>

        <article className="settings-card is-editable">
          <span className="settings-label">对话方式</span>
          <strong>{prefs?.chat_mode_label}</strong>
          <p>选择你希望小海陪伴你的节奏。</p>
          <div className="settings-segmented" role="radiogroup" aria-label="对话方式">
            {CHAT_MODE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                role="radio"
                aria-checked={prefs?.chat_mode === opt.value}
                className={`settings-segment${prefs?.chat_mode === opt.value ? ' is-active' : ''}`}
                onClick={() => handlePrefChange('chat_mode', opt.value)}
                disabled={saving || !isAuthenticated}
                title={opt.desc}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <p className="settings-hint">
            {isAuthenticated
              ? CHAT_MODE_OPTIONS.find((o) => o.value === prefs?.chat_mode)?.desc
              : '登录后可调整小海与你的对话节奏。'}
          </p>
        </article>

        <article className="settings-card is-editable">
          <span className="settings-label">微行动节奏</span>
          <strong>{prefs?.unlock_label}</strong>
          <p>决定聊多少轮后，小海会为你生成今天的微行动。</p>
          <div className="settings-segmented" role="radiogroup" aria-label="微行动节奏">
            {UNLOCK_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                role="radio"
                aria-checked={prefs?.unlock_after_turns === opt.value}
                className={`settings-segment${prefs?.unlock_after_turns === opt.value ? ' is-active' : ''}`}
                onClick={() => handlePrefChange('unlock_after_turns', opt.value)}
                disabled={saving || !isAuthenticated}
                title={opt.desc}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <p className="settings-hint">
            {isAuthenticated
              ? UNLOCK_OPTIONS.find((o) => o.value === prefs?.unlock_after_turns)?.desc
              : '登录后可设置生成微行动的探索轮次。'}
          </p>
        </article>
      </div>

      <section className="workspace-panel settings-health-panel">
        <div className="workspace-panel-head">
          <div>
            <h3>服务连接</h3>
            <p>确认你的成长记录能否正常读取和保存。</p>
          </div>
          <span className={`health-badge ${healthError ? 'is-bad' : 'is-good'}`}>{healthLabel}</span>
        </div>

        <dl className="settings-detail-list">
          <div>
            <dt>状态</dt>
            <dd>{healthLabel}</dd>
          </div>
          <div>
            <dt>最近检查</dt>
            <dd>{health?.timestamp || '刚刚'}</dd>
          </div>
          <div>
            <dt>说明</dt>
            <dd>{healthError ? '暂时无法同步，请稍后刷新' : '对话与行动记录服务可用'}</dd>
          </div>
        </dl>
      </section>
    </section>
  );
};

export default Settings;
