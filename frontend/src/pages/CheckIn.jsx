import { useState, useEffect } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Toast from '../components/Toast';
import { getTask, completeTask, getStudent, createTask } from '../api/client';

const CheckIn = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const taskId = searchParams.get('task_id');
  const email = searchParams.get('email');
  const isDemo = window.location.pathname.includes('/demo');

  const [task, setTask] = useState(null);
  const [student, setStudent] = useState(null);
  const [feedback, setFeedback] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState(null);
  const [completed, setCompleted] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        if (isDemo && email) {
          try {
            const studentData = await getStudent(email);
            setStudent(studentData);
            if (studentData.tasks && studentData.tasks.length > 0) {
              setTask(studentData.tasks[0]);
            } else {
              const newTask = await createTask({
                student_email: email,
                description: '花 10 分钟在 B 站搜索你感兴趣的职业方向，观看一个相关的科普视频，并记录下你的三点感受。'
              });
              setTask(newTask.data.task);
            }
          } catch {
            setTask({
              id: 0,
              description: '花 10 分钟在 B 站搜索你感兴趣的职业方向，观看一个相关的科普视频，并记录下你的三点感受。',
              status: '进行中'
            });
            setStudent({ name: '演示用户', email: email });
          }
        } else if (taskId) {
          const taskData = await getTask(taskId);
          setTask(taskData);
        } else {
          setError('缺少任务ID或邮箱参数');
        }
      } catch (err) {
        setError(err.response?.data?.detail || '加载任务失败');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [taskId, email, isDemo]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!task || task.id === 0) {
      setCompleted(true);
      setToast({ message: '演示模式：打卡成功！', type: 'success' });
      return;
    }

    setSubmitting(true);
    try {
      const result = await completeTask({
        task_id: task.id,
        feedback: feedback.trim() || null
      });
      if (result.success) {
        setTask(result.data.task);
        setCompleted(true);
        setToast({ message: result.message, type: 'success' });
      }
    } catch (err) {
      setToast({ message: err.response?.data?.detail || '打卡失败', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <>
        <Navbar variant="app" />
        <div className="page-section" style={{ textAlign: 'center', padding: '100px 20px' }}>
          <div style={{ fontSize: '18px', color: '#6b7280' }}>加载中...</div>
        </div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <Navbar variant="app" />
        <div className="page-section">
          <div className="form-card" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>😕</div>
            <h2 style={{ fontSize: '24px', marginBottom: '12px' }}>出问题了</h2>
            <p style={{ color: '#6b7280', marginBottom: '24px' }}>{error}</p>
            <Link to="/" className="btn-primary">返回首页</Link>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar variant="app" />
      {toast && (
        <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />
      )}
      <div className="page-section">
        <h1 className="page-title">任务打卡</h1>
        <p className="page-subtitle">
          {student ? `${student.name}，` : ''}完成微行动任务后，在这里记录你的感受吧。
        </p>

        <div className="form-card">
          {task && (
            <>
              <span className={`checkin-status-badge ${completed || task.status === '已完成' ? 'status-completed' : 'status-in-progress'}`}>
                {completed || task.status === '已完成' ? '✅ 已完成' : '⏳ 进行中'}
              </span>

              <div className="checkin-task">
                <div className="checkin-task-label">今日微行动</div>
                <div className="checkin-task-text">{task.description}</div>
              </div>

              {!completed && task.status !== '已完成' ? (
                <form onSubmit={handleSubmit}>
                  <div className="form-group">
                    <label className="form-label">打卡感言（可选）</label>
                    <textarea
                      className="feedback-textarea"
                      placeholder="完成这个任务后，你有什么感受或收获？"
                      value={feedback}
                      onChange={(e) => setFeedback(e.target.value)}
                    />
                  </div>
                  <button type="submit" className="form-submit" disabled={submitting}>
                    {submitting ? '提交中...' : '完成打卡 🎉'}
                  </button>
                </form>
              ) : (
                <div style={{ textAlign: 'center', padding: '24px 0' }}>
                  <div style={{ fontSize: '48px', marginBottom: '16px' }}>🎊</div>
                  <div style={{ fontSize: '20px', fontWeight: 600, color: '#166534', marginBottom: '8px' }}>
                    太棒了！你完成了今天的任务
                  </div>
                  <p style={{ color: '#6b7280', fontSize: '15px' }}>
                    {task.feedback ? `你的感言：${task.feedback}` : '继续保持，每一步都在向目标靠近！'}
                  </p>
                  <div style={{ marginTop: '24px' }}>
                    <Link to="/" className="btn-primary">返回首页</Link>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        <div style={{ marginTop: '32px', textAlign: 'center' }}>
          <Link to="/register" style={{ color: '#1f6fe5', fontSize: '15px', fontWeight: 500 }}>
            还没注册？立即加入 Awaken →
          </Link>
        </div>
      </div>
    </>
  );
};

export default CheckIn;
