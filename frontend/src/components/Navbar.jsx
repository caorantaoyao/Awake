import { Link } from 'react-router-dom';

// marketing 仅用于首页；功能页使用 app 变体，避免出现失效锚点。
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
          <nav aria-label="首页导航">
            <ul className="nav-links">
              <li><a href="#how-it-works" className="nav-link">产品原理</a></li>
              <li><a href="#meet-xiaohai" className="nav-link">认识小海</a></li>
              <li><a href="#micro-actions" className="nav-link">微行动</a></li>
              <li><a href="#trust" className="nav-link">安心使用</a></li>
            </ul>
          </nav>
        )}
      </div>
      {!isApp && (
        <div className="nav-right">
          <Link to="/register" className="btn-primary">开始和小海对话</Link>
          <Link to="/login" className="link-login">登录</Link>
        </div>
      )}
    </header>
  );
};

export default Navbar;
