import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';

const Landing = () => {
  return (
    <>
      <Navbar />
      <section className="hero">
        <div className="hero-copy">
          <p className="hero-eyebrow">升学、职业、未来可期</p>
          <h1 className="hero-title">AI 助你规划下一步</h1>
          <p className="hero-desc">
            Awaken 帮你发现真正适合的职业方向，量身打造分阶段路线图，为你的未来采取切实行动。
          </p>
          <div className="hero-cta">
            <Link to="/register" className="btn-hero-primary">免费注册</Link>
            <a href="#how-it-works" className="btn-hero-explore">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="7"/>
                <path d="M21 21l-4.3-4.3"/>
              </svg>
              探索 Awaken
            </a>
          </div>
        </div>

        <div className="hero-visual">
          <div className="hero-image-wrap">
            <img src="/hero-students-blue.jpg" alt="两位中国学生一起使用 Awaken 学习" />
          </div>

          <div className="float-card card-badge">
            <div className="badge-progress">
              <svg viewBox="0 0 56 56">
                <defs>
                  <linearGradient id="progressGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#4d94ff"/>
                    <stop offset="100%" stopColor="#1f6fe5"/>
                  </linearGradient>
                </defs>
                <circle className="progress-track" cx="28" cy="28" r="22"/>
                <circle className="progress-bar-circle" cx="28" cy="28" r="22"/>
              </svg>
              <span className="progress-dot">+25%</span>
            </div>
            <div className="badge-content">
              <span className="badge-label"><span className="trophy">🏆</span> 新徽章解锁！</span>
              <span className="badge-title">探路者</span>
            </div>
          </div>

          <div className="float-card card-actions">
            <span className="actions-header">待办行动</span>
            <div className="actions-item">
              <div className="actions-check">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </div>
              <span className="actions-text">报名一门 AI 方向的在线课程或工作坊</span>
            </div>
          </div>
        </div>
      </section>
    </>
  );
};

export default Landing;
