import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { getTask } from '../api/client';
import {
  createFocusTimer,
  finishFocusTimer,
  pauseFocusTimer,
  restoreFocusTimer,
  resumeFocusTimer
} from '../utils/growth';

const storageKey = (taskId) => `awaken_focus_${taskId}`;

const readSnapshot = (taskId) => {
  try {
    const raw = localStorage.getItem(storageKey(taskId));
    if (!raw) return null;
    const snapshot = JSON.parse(raw);
    if (Number(snapshot.taskId) !== Number(taskId)) return null;
    return restoreFocusTimer(snapshot);
  } catch {
    localStorage.removeItem(storageKey(taskId));
    return null;
  }
};

const formatTime = (seconds) => {
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return `${String(minutes).padStart(2, '0')}:${String(rest).padStart(2, '0')}`;
};

const Focus = () => {
  const [searchParams] = useSearchParams();
  const taskId = searchParams.get('task_id');
  const [task, setTask] = useState(null);
  const [timer, setTimer] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let alive = true;

    const loadTask = async () => {
      setLoading(true);
      setError('');
      setTask(null);
      setTimer(null);

      if (!taskId) {
        setError('缺少任务 ID');
        setLoading(false);
        return;
      }

      try {
        const nextTask = await getTask(taskId);
        if (!alive) return;
        setTask(nextTask);
        setTimer(readSnapshot(taskId));
      } catch (err) {
        if (alive) {
          setError(err.response?.data?.detail || '专注任务加载失败，请稍后重试。');
        }
      } finally {
        if (alive) setLoading(false);
      }
    };

    loadTask();
    return () => {
      alive = false;
    };
  }, [taskId]);

  useEffect(() => {
    if (!timer || !taskId) return;
    localStorage.setItem(storageKey(taskId), JSON.stringify(timer));
  }, [taskId, timer]);

  useEffect(() => {
    if (timer?.status !== 'running') return undefined;
    const interval = window.setInterval(() => {
      setTimer((current) => (
        current?.status === 'running' ? restoreFocusTimer(current) : current
      ));
    }, 1000);
    return () => window.clearInterval(interval);
  }, [timer?.status]);

  const isTaskCompleted = task?.status === '已完成';
  const totalSeconds = Math.max(1, (task?.estimated_minutes || 15) * 60);
  const remainingSeconds = isTaskCompleted ? 0 : timer?.remainingSeconds ?? totalSeconds;
  const progress = useMemo(
    () => Math.min(100, Math.max(0, ((totalSeconds - remainingSeconds) / totalSeconds) * 100)),
    [remainingSeconds, totalSeconds]
  );

  const start = () => setTimer(createFocusTimer(task));
  const pause = () => setTimer((current) => pauseFocusTimer(current));
  const resume = () => setTimer((current) => resumeFocusTimer(current));
  const finish = () => setTimer((current) => finishFocusTimer(current));

  if (loading) {
    return (
      <section className="workspace-state">
        <div className="workspace-state-card">
          <div className="workspace-state-mark">FOCUS</div>
          <h2>正在准备专注空间</h2>
          <p>读取任务内容和上次保存的计时状态。</p>
        </div>
      </section>
    );
  }

  if (error || !task) {
    return (
      <section className="workspace-state">
        <div className="workspace-state-card">
          <div className="workspace-state-mark">!</div>
          <h2>暂时无法开始专注</h2>
          <p>{error || '任务不存在。'}</p>
          <Link to="/app/tasks" className="workspace-primary-link">
            返回微行动
          </Link>
        </div>
      </section>
    );
  }

  const timerStatus = isTaskCompleted ? 'completed' : timer?.status || 'idle';

  return (
    <section className="workspace-view focus-view">
      <header className="focus-header">
        <div>
          <span className="workspace-kicker">AI FOCUS</span>
          <h2>只做眼前这一小步</h2>
          <p>计时保存在当前设备，刷新页面也能继续。</p>
        </div>
        <Link to="/app/tasks" className="workspace-secondary-button">
          返回微行动
        </Link>
      </header>

      <div className="focus-stage">
        <div className="focus-task">
          <span>{task.estimated_minutes || 15} 分钟</span>
          <h3>{task.description}</h3>
          <p>暂时放下结果，只把注意力放在当前动作上。</p>
        </div>

        <div
          className={`focus-timer focus-timer-${timerStatus}`}
          aria-live="polite"
          aria-label={`剩余时间 ${formatTime(remainingSeconds)}`}
        >
          <div className="focus-time">{formatTime(remainingSeconds)}</div>
          <div className="focus-progress" aria-hidden="true">
            <span style={{ width: `${progress}%` }} />
          </div>
          <p>
            {timerStatus === 'idle' && '准备好后开始'}
            {timerStatus === 'running' && '专注进行中'}
            {timerStatus === 'paused' && '已暂停，按自己的节奏继续'}
            {timerStatus === 'completed' && '本次专注已结束'}
          </p>
        </div>

        <div className="focus-controls">
          {timerStatus === 'idle' && (
            <button type="button" className="focus-primary" onClick={start}>
              开始专注
            </button>
          )}
          {timerStatus === 'running' && (
            <>
              <button type="button" className="focus-primary" onClick={pause}>
                暂停
              </button>
              <button type="button" className="focus-secondary" onClick={finish}>
                结束本次专注
              </button>
            </>
          )}
          {timerStatus === 'paused' && (
            <>
              <button type="button" className="focus-primary" onClick={resume}>
                继续
              </button>
              <button type="button" className="focus-secondary" onClick={finish}>
                结束本次专注
              </button>
            </>
          )}
          {timerStatus === 'completed' && (
            <Link
              to={isTaskCompleted ? '/app/tasks' : `/app/checkin?task_id=${task.id}`}
              className="focus-primary"
            >
              {isTaskCompleted ? '查看微行动' : '完成后去打卡'}
            </Link>
          )}
        </div>
      </div>
    </section>
  );
};

export default Focus;
