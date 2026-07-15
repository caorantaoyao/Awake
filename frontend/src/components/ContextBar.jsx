import { useLocation } from 'react-router-dom';

const SECTION_TITLES = {
  '/app/chat': {
    title: '对话工作区',
    eyebrow: 'XIAOHAI'
  },
  '/app/tasks': {
    title: '任务管理',
    eyebrow: 'ACTIONS'
  },
  '/app/capabilities': {
    title: '能力控制',
    eyebrow: 'DEERFLOW'
  },
  '/app/settings': {
    title: '设置',
    eyebrow: 'SYSTEM'
  }
};

const getStatusMeta = (status) => {
  if (status?.online === true) {
    return { className: 'is-online', label: status.label || '在线' };
  }
  if (status?.online === false) {
    return { className: 'is-offline', label: status.label || '离线' };
  }
  return { className: 'is-unknown', label: status?.label || '待接入' };
};

const ContextBar = ({
  student,
  deerflowStatus,
  currentModel,
  onMenuClick,
  mobileSidebarOpen = false
}) => {
  const location = useLocation();
  const section = SECTION_TITLES[location.pathname] || SECTION_TITLES['/app/chat'];
  const statusMeta = getStatusMeta(deerflowStatus);
  const displayName = student?.name || '未登录学生';
  const displayEmail = student?.email || '等待会话身份';
  const modelName = currentModel || deerflowStatus?.model || '模型待接入';

  return (
    <header className="context-bar">
      <div className="context-left">
        <button
          type="button"
          className="context-menu-button"
          onClick={onMenuClick}
          aria-label="打开工作台导航"
          aria-expanded={mobileSidebarOpen}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M4 7h16M4 12h16M4 17h16" />
          </svg>
        </button>

        <div className="context-section">
          <span className="context-eyebrow">{section.eyebrow}</span>
          <h1>{section.title}</h1>
        </div>
      </div>

      <div className="context-meta" aria-label="当前工作台上下文">
        <div className="context-pill context-student">
          <span className="context-avatar" aria-hidden="true">
            {displayName.slice(0, 1).toUpperCase()}
          </span>
          <span className="context-pill-copy">
            <span className="context-pill-label">{displayName}</span>
            <span className="context-pill-value">{displayEmail}</span>
          </span>
        </div>

        <div className="context-pill context-engine" aria-live="polite">
          <span className={`engine-dot ${statusMeta.className}`} aria-hidden="true" />
          <span className="context-pill-copy">
            <span className="context-pill-label">DeerFlow</span>
            <span className="context-pill-value">{statusMeta.label}</span>
          </span>
        </div>

        <div className="context-pill context-model">
          <span className="model-chip" aria-hidden="true">
            M
          </span>
          <span className="context-pill-copy">
            <span className="context-pill-label">当前模型</span>
            <span className="context-pill-value">{modelName}</span>
          </span>
        </div>
      </div>
    </header>
  );
};

export default ContextBar;
