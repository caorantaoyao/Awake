import { useLocation } from 'react-router-dom';

const SECTION_TITLES = {
  '/app/today': {
    title: '今日',
    eyebrow: 'TODAY'
  },
  '/app/chat': {
    title: '对话',
    eyebrow: 'XIAOHAI'
  },
  '/app/tasks': {
    title: '微行动',
    eyebrow: 'ACTIONS'
  },
  '/app/checkin': {
    title: '行动打卡',
    eyebrow: 'CHECK IN'
  },
  '/app/explore': {
    title: '探索',
    eyebrow: 'EXPLORE'
  },
  '/app/growth': {
    title: '成长',
    eyebrow: 'GROWTH'
  },
  '/app/settings': {
    title: '账号设置',
    eyebrow: 'ACCOUNT'
  }
};

const getStatusMeta = (status) => {
  if (status?.availability === 'online') {
    return { className: 'is-online', label: '可以开始对话' };
  }
  if (status?.availability === 'degraded') {
    return { className: 'is-offline', label: '基础模式可用' };
  }
  if (status?.availability === 'unreachable') {
    return { className: 'is-offline', label: '暂时无法连接' };
  }
  if (status?.availability === 'private') {
    return { className: 'is-unknown', label: '按需连接' };
  }
  return { className: 'is-unknown', label: '正在连接' };
};

const ContextBar = ({
  student,
  deerflowStatus,
  onMenuClick,
  mobileSidebarOpen = false
}) => {
  const location = useLocation();
  const section = SECTION_TITLES[location.pathname] || SECTION_TITLES['/app/today'];
  const statusMeta = getStatusMeta(deerflowStatus);
  const displayName = student?.name || '访客同学';
  const displayEmail = student?.email || '登录后保存成长记录';

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
            <span className="context-pill-label">小海状态</span>
            <span className="context-pill-value">{statusMeta.label}</span>
          </span>
        </div>
      </div>
    </header>
  );
};

export default ContextBar;
