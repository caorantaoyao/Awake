import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useOutletContext } from 'react-router-dom';
import { getAuthToken, getCurrentStudent, getStudent } from '../api/client';
import { groupTasksForActionList } from '../utils/growth';

const formatDate = (value) => {
  if (!value) return '未设置截止时间';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '未设置截止时间';
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
};

const Tasks = () => {
  const navigate = useNavigate();
  const outletContext = useOutletContext() || {};
  const [student, setStudent] = useState(outletContext.student || null);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let alive = true;

    const loadTasks = async () => {
      setLoading(true);
      setError('');

      if (!getAuthToken()) {
        if (alive) {
          setStudent(null);
          setTasks([]);
          setLoading(false);
        }
        return;
      }

      try {
        const identity = await getCurrentStudent();
        const data = await getStudent(identity.email);
        if (!alive) return;
        setStudent(data);
        setTasks(Array.isArray(data.tasks) ? data.tasks : []);
        outletContext.setStudent?.(identity);
      } catch (err) {
        if (!alive) return;
        setTasks([]);
        setError(err.response?.data?.detail || '任务列表加载失败，请稍后重试。');
      } finally {
        if (alive) setLoading(false);
      }
    };

    loadTasks();
    return () => {
      alive = false;
    };
  }, [outletContext.setStudent, reloadKey]);

  const taskGroups = useMemo(() => groupTasksForActionList(tasks), [tasks]);

  if (loading) {
    return (
      <section className="workspace-view">
        <div className="workspace-state-card is-inline">
          <div className="workspace-state-mark">TASK</div>
          <h2>正在同步微行动</h2>
          <p>正在读取任务内容、完成状态和建议时长。</p>
        </div>
      </section>
    );
  }

  if (!student && !getAuthToken()) {
    return (
      <section className="workspace-state">
        <div className="workspace-state-card">
          <div className="workspace-state-mark">ID</div>
          <h2>登录后查看微行动</h2>
          <p>微行动属于你的成长记录，登录后会自动恢复。</p>
          <Link to="/login" className="workspace-primary-link">
            登录已有账号
          </Link>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="workspace-state">
        <div className="workspace-state-card">
          <div className="workspace-state-mark">!</div>
          <h2>暂时无法同步微行动</h2>
          <p>{error}</p>
          <button
            type="button"
            className="workspace-primary-link"
            onClick={() => setReloadKey((value) => value + 1)}
          >
            重新同步
          </button>
          <Link to="/app/chat" className="workspace-secondary-link">
            回到小海对话
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="workspace-view tasks-view">
      <div className="workspace-view-header">
        <div>
          <span className="workspace-kicker">MICRO ACTIONS</span>
          <h2>微行动</h2>
          <p>{student?.name ? `${student.name}，` : ''}先推进一件正在进行的事。</p>
        </div>
        <Link to="/app/chat" className="workspace-secondary-button">
          从对话生成任务
        </Link>
      </div>

      {tasks.length === 0 ? (
        <div className="workspace-empty-panel">
          <div className="workspace-state-mark">0</div>
          <h3>还没有微行动</h3>
          <p>先和小海完成三轮探索，再把对话提炼成今天能完成的一小步。</p>
          <Link to="/app/chat" className="workspace-primary-link">
            去和小海聊聊
          </Link>
        </div>
      ) : (
        <div className="action-groups">
          {taskGroups.map((group) => (
            <section
              key={group.key}
              className={`action-group action-group-${group.key}`}
              aria-labelledby={`action-group-${group.key}`}
            >
              <header className="action-group-header">
                <div>
                  <h3 id={`action-group-${group.key}`}>{group.title}</h3>
                  <p>{group.hint}</p>
                </div>
                <span>{group.tasks.length}</span>
              </header>

              {group.tasks.length === 0 ? (
                <p className="action-empty">暂无{group.title}任务</p>
              ) : (
                <div className="action-list">
                  {group.tasks.map((task) => (
                    <article key={task.id} className="action-item">
                      <div className="action-item-main">
                        <div className="action-item-topline">
                          <span>{task.status}</span>
                          <span>{task.estimated_minutes || 15} 分钟</span>
                          {task.growth_points > 0 && <span>成长值 +{task.growth_points}</span>}
                        </div>
                        <h4>{task.description}</h4>
                        <div className="action-item-meta">
                          <span>
                            {group.key === 'completed' && task.completed_at
                              ? `完成于 ${formatDate(task.completed_at)}`
                              : `截止 ${formatDate(task.deadline)}`}
                          </span>
                          {(task.topic_tags || []).slice(0, 2).map((tag) => (
                            <span key={tag}>#{tag}</span>
                          ))}
                        </div>
                      </div>

                      {group.key === 'active' && (
                        <div className="action-item-controls">
                          <button
                            type="button"
                            className="action-primary"
                            onClick={() => navigate(`/app/focus?task_id=${task.id}`)}
                          >
                            开始专注
                          </button>
                          <button
                            type="button"
                            className="action-secondary"
                            onClick={() => navigate(`/app/checkin?task_id=${task.id}`)}
                          >
                            去打卡
                          </button>
                        </div>
                      )}
                    </article>
                  ))}
                </div>
              )}
            </section>
          ))}
        </div>
      )}
    </section>
  );
};

export default Tasks;
