import { NavLink, useLocation } from 'react-router-dom';

const NAV_ITEMS = [
  {
    key: 'chat',
    label: '对话',
    description: '小海探索',
    to: '/app/chat',
    icon: (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M5.5 16.5V7.8C5.5 6.2 6.8 5 8.4 5h7.2c1.6 0 2.9 1.2 2.9 2.8v4.7c0 1.6-1.3 2.8-2.9 2.8H11l-4 3.4c-.6.5-1.5.1-1.5-.7v-1.5Z" />
      </svg>
    )
  },
  {
    key: 'tasks',
    label: '任务',
    description: '微行动',
    to: '/app/tasks',
    icon: (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M7 6.5h10M7 12h10M7 17.5h6" />
        <path d="M4.8 6.5h.1M4.8 12h.1M4.8 17.5h.1" />
      </svg>
    )
  },
  {
    key: 'capabilities',
    label: '能力',
    description: 'DeerFlow',
    to: '/app/capabilities',
    icon: (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 3.8 19.1 8v8L12 20.2 4.9 16V8L12 3.8Z" />
        <path d="M12 8v8M8.6 10l6.8 4M15.4 10l-6.8 4" />
      </svg>
    )
  },
  {
    key: 'settings',
    label: '设置',
    description: '运行信息',
    to: '/app/settings',
    icon: (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 15.2a3.2 3.2 0 1 0 0-6.4 3.2 3.2 0 0 0 0 6.4Z" />
        <path d="M19 12a7.4 7.4 0 0 0-.1-1.2l2-1.5-2-3.4-2.4 1a7.2 7.2 0 0 0-2-1.2L14.2 3h-4.4l-.3 2.7a7.2 7.2 0 0 0-2 1.2l-2.4-1-2 3.4 2 1.5A7.4 7.4 0 0 0 5 12c0 .4 0 .8.1 1.2l-2 1.5 2 3.4 2.4-1a7.2 7.2 0 0 0 2 1.2l.3 2.7h4.4l.3-2.7a7.2 7.2 0 0 0 2-1.2l2.4 1 2-3.4-2-1.5c.1-.4.1-.8.1-1.2Z" />
      </svg>
    )
  }
];

const withCurrentSearch = (path, search) => {
  if (!search) return path;
  return `${path}${search}`;
};

const Sidebar = ({ collapsed = false, mobileOpen = false, onToggleCollapse, onCloseMobile }) => {
  const location = useLocation();

  return (
    <aside
      className={`workspace-sidebar${collapsed ? ' is-collapsed' : ''}${
        mobileOpen ? ' is-mobile-open' : ''
      }`}
      aria-label="工作台导航"
    >
      <div className="sidebar-top">
        <NavLink to={withCurrentSearch('/app/chat', location.search)} className="sidebar-brand">
          <span className="sidebar-brand-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path d="M12 3.6 21 19.4h-5.1L12 12.2 9.4 17H14l1.3 2.4H3L12 3.6Zm0 4.9-2.1 3.8h4.2L12 8.5Z" />
            </svg>
          </span>
          <span className="sidebar-brand-copy">
            <span className="sidebar-brand-name">Awaken</span>
            <span className="sidebar-brand-meta">Console</span>
          </span>
        </NavLink>

        <button
          type="button"
          className="sidebar-mobile-close"
          onClick={onCloseMobile}
          aria-label="关闭导航"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="m6 6 12 12M18 6 6 18" />
          </svg>
        </button>
      </div>

      <nav className="sidebar-nav" aria-label="工作台主导航">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.key}
            to={withCurrentSearch(item.to, location.search)}
            className={({ isActive }) => `sidebar-link${isActive ? ' is-active' : ''}`}
            onClick={onCloseMobile}
            title={collapsed ? item.label : undefined}
          >
            <span className="sidebar-link-icon">{item.icon}</span>
            <span className="sidebar-link-copy">
              <span className="sidebar-link-label">{item.label}</span>
              <span className="sidebar-link-desc">{item.description}</span>
            </span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-bottom">
        <div className="sidebar-status-card">
          <span className="sidebar-status-dot" aria-hidden="true" />
          <span className="sidebar-status-copy">
            <span className="sidebar-status-title">MVP Workspace</span>
            <span className="sidebar-status-desc">本地 DeerFlow 编排</span>
          </span>
        </div>

        <button
          type="button"
          className="sidebar-collapse"
          onClick={onToggleCollapse}
          aria-label={collapsed ? '展开侧边栏' : '折叠侧边栏'}
          aria-pressed={collapsed}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="m15 18-6-6 6-6" />
          </svg>
          <span>{collapsed ? '展开' : '折叠'}</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
