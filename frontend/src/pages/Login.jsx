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
        navigate(`/app/chat?email=${encodeURIComponent(result.data.student.email)}`);
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
      <Navbar variant="app" />
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
      <main className="auth-shell auth-shell-login">
        <section className="auth-intro" aria-labelledby="login-title">
          <Link to="/" className="auth-back-link">返回首页</Link>
          <p className="auth-kicker">继续上一次的探索</p>
          <h1 id="login-title">欢迎回来</h1>
          <p>
            登录后，小海会带你回到专属对话空间。已经聊过的方向和生成的微行动，都在原来的位置。
          </p>
          <ul className="auth-benefits">
            <li>继续和小海梳理兴趣线索</li>
            <li>查看进行中的微行动</li>
            <li>记录每一次真实体验</li>
          </ul>
        </section>

        <section className="auth-panel" aria-label="登录 Awaken">
          <div className="auth-panel-heading">
            <p>登录 Awaken</p>
            <h2>回到你的探索空间</h2>
          </div>

          <form className="auth-form" onSubmit={handleSubmit} noValidate>
            <div className="form-group">
              <label className="form-label" htmlFor="email">邮箱地址</label>
              <input
                type="email"
                id="email"
                name="email"
                className="form-input"
                placeholder="输入注册邮箱"
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
              {loading ? '正在回到探索空间...' : '登录并继续对话'}
            </button>
          </form>

          <p className="auth-switch">
            还没有账号？<Link to="/register">创建探索空间</Link>
          </p>
        </section>
      </main>
    </>
  );
};

export default Login;
