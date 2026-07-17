import { useLocation, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';

const Success = () => {
  const location = useLocation();
  const { student, message } = location.state || {};
  const loginLink = {
    pathname: '/login',
    state: student?.email ? { prefillEmail: student.email } : undefined,
  };

  return (
    <>
      <Navbar variant="app" />
      <main className="success-page">
        <section className="form-card success-card" aria-labelledby="success-title">
          <div className="success-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </div>
          <p className="success-kicker">探索空间已准备好</p>
          <h1 className="success-title" id="success-title">现在，去登录开始对话</h1>
          <p className="success-desc">
            {message || '注册成功！请用刚才设置的邮箱和密码登录，然后和小海开始第一次对话。'}
          </p>

          {student && (
            <div className="success-email-box">
              <div className="success-email-label">你的注册邮箱</div>
              <div className="success-email-text">{student.email}</div>
            </div>
          )}

          <div className="success-steps">
            <p className="success-steps-title">接下来会发生什么</p>
            <ol>
              <li><span>1</span>登录后进入工作台</li>
              <li><span>2</span>和小海聊一件真实发生过的小事</li>
              <li><span>3</span>通过追问找到兴趣和选择背后的线索</li>
              <li><span>4</span>带走一个今天就能完成的微行动</li>
            </ol>
          </div>

          <div className="success-actions">
            <Link to={loginLink} className="btn-hero-primary">
              去登录
            </Link>
            <Link to="/" className="success-home-link">返回首页</Link>
          </div>
        </section>
      </main>
    </>
  );
};

export default Success;
