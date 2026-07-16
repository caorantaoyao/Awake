import { useState, useEffect, useRef } from 'react';
import { useSearchParams, Link, useOutletContext } from 'react-router-dom';
import Toast from '../components/Toast';
import { getTask, completeTask, getStudent, createTask } from '../api/client';

const CheckIn = () => {
  const [searchParams] = useSearchParams();
  const outletContext = useOutletContext() || {};
  const taskId = searchParams.get('task_id');
  const email = searchParams.get('email');
  const isDemo = searchParams.get('demo') === '1';
  const requestKey = `${taskId || ''}:${isDemo ? `demo:${email || ''}` : 'live'}`;
  const tasksHref = '/app/tasks';

  const [task, setTask] = useState(null);
  const [student, setStudent] = useState(null);
  const [feedback, setFeedback] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState(null);
  const [completed, setCompleted] = useState(false);
  const [error, setError] = useState(null);
  const requestSequenceRef = useRef(0);
  const loadedRequestKeyRef = useRef(null);

  useEffect(() => {
    const requestSequence = requestSequenceRef.current + 1;
    requestSequenceRef.current = requestSequence;
    let alive = true;
    const isCurrentRequest = () =>
      alive && requestSequenceRef.current === requestSequence;

    setLoading(true);
    setTask(null);
    setStudent(null);
    setError(null);
    setCompleted(false);
    setFeedback('');
    setSubmitting(false);
    setToast(null);
    loadedRequestKeyRef.current = null;

    const fetchData = async () => {
      try {
        if (isDemo && email) {
          try {
            const studentData = await getStudent(email);
            if (!isCurrentRequest()) return;
            setStudent(studentData);
            outletContext.setStudent?.(studentData);
            if (studentData.tasks && studentData.tasks.length > 0) {
              setTask(studentData.tasks[0]);
            } else {
              const newTask = await createTask({
                student_email: email,
                description: '花 10 分钟在 B 站搜索你感兴趣的职业方向，观看一个相关的科普视频，并记录下你的三点感受。'
              });
              if (!isCurrentRequest()) return;
              setTask(newTask.data.task);
            }
          } catch (err) {
            if (!isCurrentRequest()) return;
            // 演示入口在测试数据不可用时使用本地任务，真实任务入口仍正常暴露错误。
            setTask({
              id: 0,
              description: '花 10 分钟在 B 站搜索你感兴趣的职业方向，观看一个相关的科普视频，并记录下你的三点感受。',
              status: '进行中'
            });
            setStudent({ name: '演示用户', email: email });
            outletContext.setStudent?.({ name: '演示用户', email });
          }
        } else if (taskId) {
          const taskData = await getTask(taskId);
          if (!isCurrentRequest()) return;
          setTask(taskData);
        } else {
          if (!isCurrentRequest()) return;
          setError('缺少任务ID或邮箱参数');
        }
      } catch (err) {
        if (!isCurrentRequest()) return;
        setError(err.response?.data?.detail || '加载任务失败');
      } finally {
        if (isCurrentRequest()) {
          loadedRequestKeyRef.current = requestKey;
          setLoading(false);
        }
      }
    };
    fetchData();

    return () => {
      alive = false;
    };
  }, [taskId, email, isDemo, requestKey, outletContext.setStudent]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const requestSequence = requestSequenceRef.current;
    const isCurrentRequest = () => requestSequenceRef.current === requestSequence;

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
      if (!isCurrentRequest()) return;
      if (result.success) {
        setTask(result.data.task);
        setCompleted(true);
        setToast({ message: result.message, type: 'success' });
      }
    } catch (err) {
      if (!isCurrentRequest()) return;
      setToast({ message: err.response?.data?.detail || '打卡失败', type: 'error' });
    } finally {
      if (isCurrentRequest()) setSubmitting(false);
    }
  };

  if (loading || loadedRequestKeyRef.current !== requestKey) {
    return (
      <section className="workspace-state">
        <div className="workspace-state-card">
          <div className="workspace-state-mark">GO</div>
          <h2>正在读取微行动</h2>
          <p>正在同步任务内容和完成状态。</p>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="workspace-state">
        <div className="workspace-state-card">
          <div className="workspace-state-mark">!</div>
          <h2>暂时无法读取这个任务</h2>
          <p>{error}</p>
          <Link to={tasksHref} className="workspace-primary-link">
            返回微行动
          </Link>
        </div>
      </section>
    );
  }

  return (
    <>
      {toast && (
        <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />
      )}
      <section className="workspace-view checkin-view">
        <div className="workspace-view-header">
          <div>
            <span className="workspace-kicker">TODAY&apos;S STEP</span>
            <h2>完成今天的一小步</h2>
            <p>
              {student ? `${student.name}，` : ''}完成后记录一句真实感受，就足够了。
            </p>
          </div>
          <Link to={tasksHref} className="workspace-secondary-button">
            返回微行动
          </Link>
        </div>

        <div className="workspace-panel checkin-panel">
          {task && (
            <>
              <span className={`checkin-status-badge ${completed || task.status === '已完成' ? 'status-completed' : 'status-in-progress'}`}>
                {completed || task.status === '已完成' ? '已完成' : '进行中'}
              </span>

              <div className="checkin-task">
                <div className="checkin-task-label">今日微行动</div>
                <div className="checkin-task-text">{task.description}</div>
              </div>

              {!completed && task.status !== '已完成' ? (
                <form onSubmit={handleSubmit}>
                  <div className="form-group">
                    <label className="form-label" htmlFor="checkin-feedback">
                      打卡感言（可选）
                    </label>
                    <textarea
                      id="checkin-feedback"
                      className="feedback-textarea"
                      placeholder="完成这个任务后，你有什么感受或收获？"
                      value={feedback}
                      onChange={(e) => setFeedback(e.target.value)}
                    />
                  </div>
                  <button type="submit" className="form-submit" disabled={submitting}>
                    {submitting ? '正在提交...' : '完成打卡'}
                  </button>
                </form>
              ) : (
                <div className="checkin-complete">
                  <div className="checkin-complete-mark" aria-hidden="true">✓</div>
                  <h3>今天的一小步已经完成</h3>
                  <p>
                    {task.feedback ? `你的感言：${task.feedback}` : '继续保持，每一步都在向目标靠近！'}
                  </p>
                  <Link to={tasksHref} className="workspace-primary-link">
                    查看全部微行动
                  </Link>
                  <Link to="/app/today" className="workspace-secondary-link">
                    返回今日
                  </Link>
                </div>
              )}
            </>
          )}
        </div>
      </section>
    </>
  );
};

export default CheckIn;
