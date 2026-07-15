import { Link } from 'react-router-dom';

// variant="marketing"：落地页完整导航 + 注册/登录（转化入口）
// variant="app"：App 内页（对话/打卡/注册成功等），仅保留可返回首页的 Logo，
//   不展示会跳空的营销锚点与自相矛盾的注册/登录
const Navbar = ({ variant = 'marketing' }) => {
  const isApp = variant === 'app';

  return (
    <header className="navbar">
      <div className="nav-left">
        <Link to="/" className="logo">
          <div className="logo-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path fill="white" fillRule="evenodd" clipRule="evenodd" d="M12 3.6L21 19.4H15.9L12 12.2L9.4 17H14L15.3 19.4H3L12 3.6ZM12 8.5L9.9 12.3H14.1L12 8.5Z"/>
            </svg>
          </div>
          <span className="logo-text">Awaken<span className="tm">™</span></span>
        </Link>
        {!isApp && (
          <nav>
            <ul className="nav-links">
              <li><a href="#how-it-works" className="nav-link">产品原理</a></li>
              <li><a href="#features" className="nav-link">升学顾问</a></li>
              <li><a href="#testimonials" className="nav-link">用户心声</a></li>
              <li>
                <a href="#" className="nav-link">
                  资源中心
                  <svg className="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="6 9 12 15 18 9"/>
                  </svg>
                </a>
              </li>
              <li><a href="#" className="nav-link">联系我们</a></li>
            </ul>
          </nav>
        )}
      </div>
      {!isApp && (
        <div className="nav-right">
          <Link to="/register" className="btn-primary">立即注册</Link>
          <a href="#" className="link-login">登录</a>
        </div>
      )}
    </header>
  );
};

export default Navbar;
