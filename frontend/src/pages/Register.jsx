import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Toast from '../components/Toast';
import { registerStudent } from '../api/client';

const Register = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    grade: '高一',
    password: '',
    confirmPassword: ''
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);

  const validateForm = () => {
    const newErrors = {};
    if (!formData.name.trim()) {
      newErrors.name = '请输入姓名';
    }
    if (!formData.email.trim()) {
      newErrors.email = '请输入邮箱';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = '请输入有效的邮箱地址';
    }
    if (!formData.grade) {
      newErrors.grade = '请选择年级';
    }
    if (!formData.password) {
      newErrors.password = '请输入密码';
    } else if (formData.password.length < 8) {
      newErrors.password = '密码至少需要 8 位';
    }
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = '请再次输入密码';
    } else if (formData.confirmPassword !== formData.password) {
      newErrors.confirmPassword = '两次输入的密码不一致';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setLoading(true);
    try {
      const registerPayload = {
        name: formData.name.trim(),
        email: formData.email.trim(),
        grade: formData.grade,
        password: formData.password
      };
      const result = await registerStudent(registerPayload);
      if (result.success) {
        navigate('/success', {
          state: {
            student: result.data.student,
            message: result.message
          }
        });
      }
    } catch (error) {
      const errorMessage = error.response?.data?.detail || '注册失败，请稍后重试';
      setToast({ message: errorMessage, type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
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
      <main className="auth-shell">
        <section className="auth-intro" aria-labelledby="register-title">
          <Link to="/" className="auth-back-link">返回首页</Link>
          <p className="auth-kicker">从一次真诚对话开始</p>
          <h1 id="register-title">创建你的探索空间</h1>
          <p>
            小海不会替你决定未来，而会从真实经历里陪你找到兴趣线索，并把想法变成今天就能完成的一小步。
          </p>
          <ul className="auth-benefits">
            <li>不贴标签，先理解你的真实感受</li>
            <li>每次只推进一个具体的小行动</li>
            <li>随时回来，继续上一次的探索</li>
          </ul>
        </section>

        <section className="auth-panel" aria-label="注册 Awaken">
          <div className="auth-panel-heading">
            <p>注册 Awaken</p>
            <h2>开始和小海对话</h2>
          </div>

          <form className="auth-form" onSubmit={handleSubmit} noValidate>
            <div className="auth-form-row">
              <div className="form-group">
                <label className="form-label" htmlFor="name">姓名</label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  className="form-input"
                  placeholder="怎么称呼你"
                  value={formData.name}
                  onChange={handleChange}
                  autoComplete="name"
                  aria-invalid={Boolean(errors.name)}
                  aria-describedby={errors.name ? 'name-error' : undefined}
                />
                {errors.name && <div className="form-error" id="name-error">{errors.name}</div>}
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="grade">当前年级</label>
                <select
                  id="grade"
                  name="grade"
                  className="form-select"
                  value={formData.grade}
                  onChange={handleChange}
                >
                  <option value="高一">高一</option>
                  <option value="高二">高二</option>
                  <option value="高三">高三</option>
                </select>
                {errors.grade && <div className="form-error">{errors.grade}</div>}
              </div>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="email">邮箱地址</label>
              <input
                type="email"
                id="email"
                name="email"
                className="form-input"
                placeholder="用于登录和接收重要提醒"
                value={formData.email}
                onChange={handleChange}
                autoComplete="email"
                aria-invalid={Boolean(errors.email)}
                aria-describedby={errors.email ? 'register-email-error' : undefined}
              />
              {errors.email && <div className="form-error" id="register-email-error">{errors.email}</div>}
            </div>

            <div className="auth-form-row">
              <div className="form-group">
                <label className="form-label" htmlFor="password">设置密码</label>
                <input
                  type="password"
                  id="password"
                  name="password"
                  className="form-input"
                  placeholder="至少 8 位"
                  value={formData.password}
                  onChange={handleChange}
                  autoComplete="new-password"
                  aria-invalid={Boolean(errors.password)}
                  aria-describedby={errors.password ? 'password-error' : undefined}
                />
                {errors.password && (
                  <div className="form-error" id="password-error">{errors.password}</div>
                )}
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="confirmPassword">确认密码</label>
                <input
                  type="password"
                  id="confirmPassword"
                  name="confirmPassword"
                  className="form-input"
                  placeholder="再次输入"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  autoComplete="new-password"
                  aria-invalid={Boolean(errors.confirmPassword)}
                  aria-describedby={errors.confirmPassword ? 'confirm-password-error' : undefined}
                />
                {errors.confirmPassword && (
                  <div className="form-error" id="confirm-password-error">{errors.confirmPassword}</div>
                )}
              </div>
            </div>

            <button
              type="submit"
              className="form-submit"
              disabled={loading}
            >
              {loading ? '正在创建探索空间...' : '创建账号并进入对话'}
            </button>
          </form>

          <p className="auth-legal">注册即表示你同意服务条款和隐私政策。</p>
          <p className="auth-switch">
            已有账号？<Link to="/login">直接登录</Link>
          </p>
        </section>
      </main>
    </>
  );
};

export default Register;
