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
    grade: '高一'
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
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setLoading(true);
    try {
      const result = await registerStudent(formData);
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
      <Navbar />
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
      <div className="page-section">
        <h1 className="page-title">开始你的成长之旅</h1>
        <p className="page-subtitle">
          填写信息注册 Awaken，AI 学长「小海」将通过苏格拉底式对话，帮你找到真正适合的方向。
        </p>

        <div className="form-card">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label" htmlFor="name">姓名</label>
              <input
                type="text"
                id="name"
                name="name"
                className="form-input"
                placeholder="请输入你的姓名"
                value={formData.name}
                onChange={handleChange}
              />
              {errors.name && <div className="form-error">{errors.name}</div>}
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="email">邮箱地址</label>
              <input
                type="email"
                id="email"
                name="email"
                className="form-input"
                placeholder="example@qq.com"
                value={formData.email}
                onChange={handleChange}
              />
              {errors.email && <div className="form-error">{errors.email}</div>}
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

            <button
              type="submit"
              className="form-submit"
              disabled={loading}
            >
              {loading ? '注册中...' : '免费注册开始体验'}
            </button>
          </form>

          <div style={{ marginTop: '24px', textAlign: 'center', fontSize: '14px', color: '#6b7280' }}>
            注册即表示你同意我们的服务条款和隐私政策
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

export default Register;
