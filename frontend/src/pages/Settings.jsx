import { useEffect, useMemo, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { healthCheck } from '../api/client';

const Settings = () => {
  const outletContext = useOutletContext() || {};
  const student = outletContext.student;
  const status = outletContext.deerflowStatus;

  const [health, setHealth] = useState(null);
  const [healthError, setHealthError] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const statusLabel = {
    online: '可以对话',
    degraded: '基础模式',
    unreachable: '暂时无法连接',
    private: '按需连接'
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

  const loadSettings = async ({ silent = false } = {}) => {
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

    setLoading(false);
    setRefreshing(false);
  };

  useEffect(() => {
    loadSettings();
  }, []);

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
          <p>查看你的账号、小海的可用状态和当前探索节奏。</p>
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

        <article className="settings-card">
          <span className="settings-label">对话方式</span>
          <strong>先探索，再行动</strong>
          <p>小海会先理解你的想法，不急着替你下结论。</p>
        </article>

        <article className="settings-card">
          <span className="settings-label">微行动节奏</span>
          <strong>探索 3 轮后解锁</strong>
          <p>聊得足够具体后，再把想法变成今天能完成的一步。</p>
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
