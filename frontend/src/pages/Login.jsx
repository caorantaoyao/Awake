import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Toast from '../components/Toast';
import { loginStudent, saveAuthSession } from '../api/client';

const Login = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);

  const validateForm = () => {
    const newErrors = {};
    const value = email.trim();
    if (!value) {
      newErrors.email = '请输入邮箱';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
      newErrors.email = '请输入有效的邮箱地址';
    }
    if (!password) {
      newErrors.password = '请输入密码';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setLoading(true);
    try {
      const result = await loginStudent({ email: email.trim(), password });
      if (result.success) {
        saveAuthSession({
          accessToken: result.data.access_token,
          student: result.data.student
        });
        navigate(`/chat?email=${encodeURIComponent(result.data.student.email)}`);
      }
    } catch (err) {
      const errorMessage = err.response?.data?.detail || '登录失败，请稍后重试';
      setToast({ message: errorMessage, type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Navbar />
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
      <div className="page-section">
        <h1 className="page-title">欢迎回来</h1>
        <p className="page-subtitle">
          输入注册邮箱和密码登录 Awaken，继续和 AI 学长「小海」探索你的成长方向。
        </p>

        <div className="form-card">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label" htmlFor="email">邮箱地址</label>
              <input
                type="email"
                id="email"
                name="email"
                className="form-input"
                placeholder="example@qq.com"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (errors.email) setErrors(prev => ({ ...prev, email: '' }));
                }}
                autoComplete="email"
                aria-invalid={Boolean(errors.email)}
                aria-describedby={errors.email ? 'email-error' : undefined}
              />
              {errors.email && <div className="form-error" id="email-error">{errors.email}</div>}
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="password">密码</label>
              <input
                type="password"
                id="password"
                name="password"
                className="form-input"
                placeholder="请输入密码"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (errors.password) setErrors(prev => ({ ...prev, password: '' }));
                }}
                autoComplete="current-password"
                aria-invalid={Boolean(errors.password)}
                aria-describedby={errors.password ? 'password-error' : undefined}
              />
              {errors.password && (
                <div className="form-error" id="password-error">{errors.password}</div>
              )}
            </div>

            <button
              type="submit"
              className="form-submit"
              disabled={loading}
            >
              {loading ? '登录中...' : '登录并继续对话'}
            </button>
          </form>

          <div style={{ marginTop: '24px', textAlign: 'center', fontSize: '14px', color: '#6b7280' }}>
            还没有账号？{' '}
            <Link to="/register" style={{ color: '#1f6fe5', fontWeight: 600 }}>
              先完成注册
            </Link>
          </div>
        </div>

        <div style={{ marginTop: '32px', textAlign: 'center' }}>
          <Link to="/" style={{ color: '#1f6fe5', fontSize: '15px', fontWeight: 500 }}>
            ← 返回首页
          </Link>
        </div>
      </div>
    </>
  );
};

export default Login;
