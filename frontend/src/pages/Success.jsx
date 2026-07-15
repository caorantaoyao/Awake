import { useLocation, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';

const Success = () => {
  const location = useLocation();
  const { student, message } = location.state || {};

  return (
    <>
      <Navbar variant="app" />
      <div className="page-section">
        <div className="form-card success-card">
          <div className="success-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </div>
          <h1 className="success-title">注册成功！🎉</h1>
          <p className="success-desc">
            {message || '欢迎加入 Awaken！请查收你的邮箱，点击邮件中的链接开始与「小海」的第一次对话。'}
          </p>

          {student && (
            <div className="success-email-box">
              <div className="success-email-label">欢迎邮件已发送至</div>
              <div className="success-email-text">{student.email}</div>
            </div>
          )}

          <div style={{ background: '#f8fafc', borderRadius: '12px', padding: '20px', textAlign: 'left', marginBottom: '24px' }}>
            <div style={{ fontSize: '14px', fontWeight: 600, color: '#1f2430', marginBottom: '12px' }}>接下来的步骤：</div>
            <ol style={{ paddingLeft: '20px', color: '#4b5563', fontSize: '14px', lineHeight: 2 }}>
              <li>前往邮箱查收欢迎邮件（可能在垃圾邮件中）</li>
              <li>点击邮件中的「开始与小海对话」按钮</li>
              <li>通过苏格拉底式对话探索你的兴趣方向</li>
              <li>接收定制的微行动任务并完成打卡</li>
            </ol>
          </div>

          <div style={{ display: 'flex', gap: '14px', flexDirection: 'column' }}>
            {student && (
              <Link
                to={`/chat?email=${encodeURIComponent(student.email)}`}
                className="btn-hero-primary"
                style={{ display: 'flex', justifyContent: 'center', textDecoration: 'none' }}
              >
                开始与小海对话 →
              </Link>
            )}
            <Link
              to="/"
              style={{ color: '#1f6fe5', fontSize: '15px', fontWeight: 500, textAlign: 'center' }}
            >
              返回首页
            </Link>
            {student && (
              <Link
                to={`/checkin/demo?email=${encodeURIComponent(student.email)}`}
                style={{ color: '#9ca3af', fontSize: '14px', fontWeight: 500, textAlign: 'center' }}
              >
                查看演示：打卡页面 →
              </Link>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default Success;
