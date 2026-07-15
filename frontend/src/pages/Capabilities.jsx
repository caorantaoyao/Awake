import { useEffect, useMemo, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { getDeerflowStatus, getModels, getSkills, toggleSkill } from '../api/client';

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
          <p>查看 DeerFlow gateway 暴露的 skills 与模型，按需开启或停用单项能力。</p>
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
        <div className="workspace-alert is-error">
          <span>操作未完成</span>
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
    </section>
  );
};

export default Capabilities;
