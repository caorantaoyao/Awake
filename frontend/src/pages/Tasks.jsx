import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useOutletContext, useSearchParams } from 'react-router-dom';
import { getAuthToken, getCurrentStudent, getStoredStudent, getStudent } from '../api/client';

const TASK_GROUPS = [
  { key: 'active', title: '进行中', hint: '今天就能推进的小行动' },
  { key: 'completed', title: '已完成', hint: '已经打卡沉淀的行动' },
  { key: 'expired', title: '已过期', hint: '需要重新选择节奏的任务' }
];

const formatDate = (value) => {
  if (!value) return '未设置';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '未设置';
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
};

const getTaskGroup = (task) => {
  if (task.status === '已完成') return 'completed';
  if (task.status === '已过期') return 'expired';

  if (task.deadline) {
    const deadline = new Date(task.deadline);
    if (!Number.isNaN(deadline.getTime()) && deadline.getTime() < Date.now()) {
      return 'expired';
    }
  }

  return 'active';
};

const getInitialStudent = () => {
  if (!getAuthToken()) return null;
  return getStoredStudent();
};

const Tasks = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const outletContext = useOutletContext() || {};
  const queryEmail = searchParams.get('email');
  const workspaceStudent = outletContext.student;
  const workspaceStudentEmail = workspaceStudent?.email;
  const setWorkspaceStudent = outletContext.setStudent;
  const [email, setEmail] = useState(
    queryEmail || workspaceStudentEmail || getInitialStudent()?.email || ''
  );
  const [student, setStudent] = useState(workspaceStudent || getInitialStudent());
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let alive = true;

    const loadTasks = async () => {
      setLoading(true);
      setError('');

      const storedStudent = getInitialStudent();
      let nextEmail = queryEmail || storedStudent?.email || workspaceStudentEmail || '';
      let identity = storedStudent || workspaceStudent || null;

      if (!nextEmail && getAuthToken()) {
        try {
          identity = await getCurrentStudent();
          nextEmail = identity.email;
          setWorkspaceStudent?.(identity);
        } catch {
          nextEmail = '';
          identity = null;
        }
      }

      if (!nextEmail) {
        if (alive) {
          setEmail('');
          setStudent(null);
          setTasks([]);
          setLoading(false);
        }
        return;
      }

      try {
        const data = await getStudent(nextEmail);
        if (alive) {
          setEmail(nextEmail);
          setStudent(data);
          setTasks(Array.isArray(data.tasks) ? data.tasks : []);
          setWorkspaceStudent?.(data);
        }
      } catch (err) {
        if (alive) {
          setEmail(nextEmail);
          setStudent(identity || { email: nextEmail });
          setTasks([]);
          setError(err.response?.data?.detail || '任务列表加载失败，请稍后重试。');
        }
      } finally {
        if (alive) setLoading(false);
      }
    };

    loadTasks();
    return () => {
      alive = false;
    };
  }, [queryEmail, setWorkspaceStudent, workspaceStudentEmail]);

  const groupedTasks = useMemo(() => {
    const groups = TASK_GROUPS.reduce((nextGroups, group) => {
      nextGroups[group.key] = [];
      return nextGroups;
    }, {});

    tasks.forEach((task) => {
      groups[getTaskGroup(task)].push(task);
    });

    return groups;
  }, [tasks]);

  const totalCount = tasks.length;
  const chatHref = email ? `/app/chat?email=${encodeURIComponent(email)}` : '/app/chat';

  if (loading) {
    return (
      <section className="workspace-view">
        <div className="workspace-state-card is-inline">
          <div className="workspace-state-mark">TASK</div>
          <h2>正在同步任务列表</h2>
          <p>正在读取你的微行动任务、打卡状态和截止时间。</p>
        </div>
      </section>
    );
  }

  if (!email) {
    return (
      <section className="workspace-state">
        <div className="workspace-state-card">
          <div className="workspace-state-mark">ID</div>
          <h2>需要先确认学生身份</h2>
          <p>任务管理依赖学生邮箱。登录后会自动拉取你的微行动任务。</p>
          <Link to="/login" className="workspace-primary-link">
            登录已有账号 →
          </Link>
          <Link to="/register" className="workspace-secondary-link">
            还没有账号？先注册
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
          <h2>任务管理</h2>
          <p>
            {student?.name ? `${student.name}，` : ''}这里汇总你和小海沉淀下来的行动任务。
          </p>
        </div>
        <Link to={chatHref} className="workspace-secondary-button">
          回到对话生成任务
        </Link>
      </div>

      {error && (
        <div className="workspace-alert is-error">
          <span>任务同步失败</span>
          <p>{error}</p>
        </div>
      )}

      {totalCount === 0 ? (
        <div className="workspace-empty-panel">
          <div className="workspace-state-mark">0</div>
          <h3>还没有微行动任务</h3>
          <p>先和小海聊 3 轮探索，解锁后即可把对话提炼成今天能完成的一小步。</p>
          <Link to={chatHref} className="workspace-primary-link">
            去对话区开始探索 →
          </Link>
        </div>
      ) : (
        <div className="task-columns">
          {TASK_GROUPS.map((group) => (
            <section key={group.key} className="task-column" aria-label={group.title}>
              <div className="task-column-head">
                <div>
                  <h3>{group.title}</h3>
                  <p>{group.hint}</p>
                </div>
                <span>{groupedTasks[group.key].length}</span>
              </div>

              <div className="task-card-list">
                {groupedTasks[group.key].length === 0 ? (
                  <div className="task-mini-empty">暂无{group.title}任务</div>
                ) : (
                  groupedTasks[group.key].map((task) => (
                    <article key={task.id} className={`task-card task-card-${group.key}`}>
                      <div className="task-card-topline">
                        <span>{task.status}</span>
                        <span>#{task.id}</span>
                      </div>
                      <p className="task-card-desc">{task.description}</p>
                      <div className="task-card-meta">
                        <span>截止：{formatDate(task.deadline)}</span>
                        {task.completed_at && <span>完成：{formatDate(task.completed_at)}</span>}
                      </div>
                      {group.key === 'active' && (
                        <button
                          type="button"
                          className="task-card-action"
                          onClick={() => navigate(`/checkin?task_id=${task.id}`)}
                        >
                          去打卡
                        </button>
                      )}
                    </article>
                  ))
                )}
              </div>
            </section>
          ))}
        </div>
      )}
    </section>
  );
};

export default Tasks;
