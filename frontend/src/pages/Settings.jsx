import { useEffect, useMemo, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { getDeerflowStatus, healthCheck } from '../api/client';

const fallbackStatus = {
  online: false,
  label: '离线',
  assistant_id: 'lead_agent',
  model: null,
  error: 'DeerFlow 状态接口请求失败'
};

const Settings = () => {
  const outletContext = useOutletContext() || {};
  const workspaceStatus = outletContext.deerflowStatus;
  const refreshWorkspaceDeerflowStatus = outletContext.refreshDeerflowStatus;

  const [status, setStatus] = useState(() => workspaceStatus || null);
  const [health, setHealth] = useState(null);
  const [healthError, setHealthError] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const statusLabel = status?.online === true ? '在线' : status?.online === false ? '离线' : '检测中';
  const statusTone = status?.online === true ? 'is-good' : status?.online === false ? 'is-bad' : '';

  const healthLabel = useMemo(() => {
    if (health?.status) return health.status;
    if (healthError) return 'unreachable';
    return 'unknown';
  }, [health, healthError]);

  const loadSettings = async ({ silent = false } = {}) => {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setHealthError('');

    const [statusResult, healthResult] = await Promise.allSettled([
      refreshWorkspaceDeerflowStatus ? refreshWorkspaceDeerflowStatus() : getDeerflowStatus(),
      healthCheck()
    ]);

    setStatus(statusResult.status === 'fulfilled' ? statusResult.value : fallbackStatus);

    if (healthResult.status === 'fulfilled') {
      setHealth(healthResult.value);
    } else {
      setHealth(null);
      setHealthError('健康检查接口请求失败');
    }

    setLoading(false);
    setRefreshing(false);
  };

  useEffect(() => {
    loadSettings();
  }, []);

  useEffect(() => {
    if (workspaceStatus) {
      setStatus(workspaceStatus);
    }
  }, [workspaceStatus]);

  if (loading) {
    return (
      <section className="workspace-view">
        <div className="workspace-state-card is-inline">
          <div className="workspace-state-mark">SYS</div>
          <h2>正在读取运行信息</h2>
          <p>正在检查 Awaken API 与 DeerFlow gateway 的当前状态。</p>
        </div>
      </section>
    );
  }

  return (
    <section className="workspace-view settings-view">
      <div className="workspace-view-header">
        <div>
          <span className="workspace-kicker">SYSTEM SNAPSHOT</span>
          <h2>设置 / 关于</h2>
          <p>只读展示当前工作台运行信息，用于联调时确认对话引擎与健康检查状态。</p>
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

      {status?.online === false && (
        <div className="workspace-alert is-warning">
          <span>DeerFlow 当前不可达</span>
          <p>{status.error || '后端已返回离线降级状态，对话链路会继续使用 mock 降级。'}</p>
        </div>
      )}

      <div className="settings-grid">
        <article className="settings-card">
          <span className="settings-label">DeerFlow 状态</span>
          <strong className={statusTone}>{statusLabel}</strong>
          <p>{status?.error || 'Gateway 状态正常返回。'}</p>
        </article>

        <article className="settings-card">
          <span className="settings-label">assistant_id</span>
          <strong>{status?.assistant_id || '未返回'}</strong>
          <p>当前 DeerFlow assistant/agent 标识。</p>
        </article>

        <article className="settings-card">
          <span className="settings-label">当前模型</span>
          <strong>{status?.model || '未返回'}</strong>
          <p>若 DeerFlow 离线，模型字段会保持为空。</p>
        </article>

        <article className="settings-card">
          <span className="settings-label">阶段阈值</span>
          <strong>探索 3 轮后解锁</strong>
          <p>与后端 `can_extract_task` 当前阈值保持一致。</p>
        </article>
      </div>

      <section className="workspace-panel settings-health-panel">
        <div className="workspace-panel-head">
          <div>
            <h3>Awaken API 健康检查</h3>
            <p>来自 `GET /api/health`，用于确认 FastAPI 服务是否可达。</p>
          </div>
          <span className={`health-badge ${healthError ? 'is-bad' : 'is-good'}`}>{healthLabel}</span>
        </div>

        <dl className="settings-detail-list">
          <div>
            <dt>状态</dt>
            <dd>{healthLabel}</dd>
          </div>
          <div>
            <dt>时间戳</dt>
            <dd>{health?.timestamp || '未返回'}</dd>
          </div>
          <div>
            <dt>错误</dt>
            <dd>{healthError || '无'}</dd>
          </div>
        </dl>
      </section>
    </section>
  );
};

export default Settings;
