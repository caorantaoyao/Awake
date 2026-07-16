import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useOutletContext } from 'react-router-dom';
import {
  getGrowthEvents,
  getGrowthSummary,
  getProfile,
  getResources,
  getTodayTasks
} from '../api/client';
import { buildTodaySnapshot } from '../utils/workspace';

const EMPTY_SNAPSHOT = buildTodaySnapshot([]);

const formatToday = () =>
  new Intl.DateTimeFormat('zh-CN', {
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  }).format(new Date());

const formatEventTime = (value) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '最近';
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'numeric',
    day: 'numeric'
  }).format(date);
};

const TodaySkeleton = () => (
  <section className="workspace-view today-view" aria-busy="true" aria-label="正在准备今日首页">
    <div className="today-loading-head">
      <span className="today-skeleton is-short" />
      <span className="today-skeleton is-title" />
    </div>
    <div className="today-layout">
      <div className="today-skeleton today-skeleton-sheet" />
      <div className="today-skeleton today-skeleton-side" />
      <div className="today-skeleton today-skeleton-wide" />
      <div className="today-skeleton today-skeleton-side" />
    </div>
  </section>
);

const Today = () => {
  const outletContext = useOutletContext() || {};
  const { student, deerflowStatus } = outletContext;
  const [snapshot, setSnapshot] = useState(EMPTY_SNAPSHOT);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  const loadToday = useCallback(async (silent = false) => {
    if (silent) setRefreshing(true);
    else setLoading(true);

    const results = await Promise.allSettled([
      getTodayTasks(),
      getProfile(),
      getResources(),
      getGrowthSummary(),
      getGrowthEvents(4)
    ]);
    setSnapshot(buildTodaySnapshot(results));
    setLoading(false);
    setRefreshing(false);
  }, []);

  useEffect(() => {
    loadToday();
  }, [loadToday, reloadKey]);

  const profileTags = useMemo(
    () => [...(snapshot.profile?.interest_tags || []), ...(snapshot.profile?.ability_tags || [])],
    [snapshot.profile]
  );
  const isDegraded = ['degraded', 'unreachable'].includes(deerflowStatus?.availability);
  const firstName = student?.name || '同学';
  const primaryTask = snapshot.primaryTask;
  const focusHref = primaryTask
    ? `/app/focus?task_id=${encodeURIComponent(primaryTask.id)}`
    : '/app/tasks';

  if (loading) return <TodaySkeleton />;

  if (snapshot.isUnavailable) {
    return (
      <section className="workspace-state">
        <div className="workspace-state-card today-error-state">
          <div className="workspace-state-mark">!</div>
          <h2>今日内容暂时没有同步</h2>
          <p>成长记录服务没有返回数据。你可以重新同步，已保存的内容不会丢失。</p>
          <button
            type="button"
            className="workspace-primary-link"
            onClick={() => setReloadKey((value) => value + 1)}
          >
            重新同步
          </button>
          <Link to="/app/chat" className="workspace-secondary-link">
            先去对话
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="workspace-view today-view">
      <header className="today-intro">
        <div>
          <p className="today-date">{formatToday()}</p>
          <h2>{firstName}，从一件具体的小事开始。</h2>
          <p>这里汇总今天最值得推进的行动，以及最近形成的成长线索。</p>
        </div>
        <button
          type="button"
          className="today-refresh"
          onClick={() => loadToday(true)}
          disabled={refreshing}
        >
          {refreshing ? '同步中' : '同步今日'}
        </button>
      </header>

      {isDegraded && (
        <div className="today-degraded-note" role="status">
          <strong>小海当前使用基础陪伴模式</strong>
          <span>今日任务和成长记录仍可查看，增强对话能力恢复后会自动可用。</span>
        </div>
      )}

      {snapshot.isPartial && (
        <div className="today-partial-note" role="status">
          部分内容暂未同步，页面已保留本次成功读取的真实记录。
        </div>
      )}

      <div className="today-layout">
        <article className="today-mission">
          <div className="today-section-heading">
            <span>当前微行动</span>
            {primaryTask && <em>{primaryTask.estimated_minutes} 分钟</em>}
          </div>
          {primaryTask ? (
            <>
              <h3>{primaryTask.description}</h3>
              <div className="today-mission-meta">
                <span>成长值 +{primaryTask.growth_points}</span>
                {(primaryTask.topic_tags || []).slice(0, 2).map((tag) => (
                  <span key={tag}>{tag}</span>
                ))}
              </div>
              <p>先完成这一小步。需要调整节奏时，可以去微行动页查看其他任务。</p>
              <div className="today-mission-actions">
                <Link to={focusHref} className="today-primary-action">
                  开始专注
                </Link>
                <Link to="/app/tasks" className="today-text-link">
                  查看全部微行动
                </Link>
              </div>
            </>
          ) : (
            <div className="today-section-empty">
              <h3>今天还没有微行动</h3>
              <p>和小海聊聊最近在意的事情，探索清楚后再决定今天做哪一步。</p>
              <Link to="/app/chat" className="today-primary-action">
                开始对话
              </Link>
            </div>
          )}
        </article>

        <aside className="today-profile" aria-labelledby="today-profile-title">
          <div className="today-section-heading">
            <span id="today-profile-title">我的画像</span>
            <em>{snapshot.profile?.exploration_stage || '探索中'}</em>
          </div>
          {snapshot.profile?.is_empty !== false ? (
            <div className="today-section-empty">
              <h3>画像正在形成</h3>
              <p>{snapshot.profile?.guidance || '从一次真实对话开始，逐步积累兴趣和能力线索。'}</p>
            </div>
          ) : (
            <>
              <p className="today-profile-summary">{snapshot.profile?.summary}</p>
              {profileTags.length > 0 && (
                <div className="today-tag-list" aria-label="画像标签">
                  {profileTags.slice(0, 5).map((tag) => (
                    <span key={tag}>{tag}</span>
                  ))}
                </div>
              )}
            </>
          )}
          <Link to="/app/growth" className="today-text-link">
            查看成长画像
          </Link>
        </aside>

        <section className="today-resources" aria-labelledby="today-resources-title">
          <div className="today-section-heading">
            <div>
              <span id="today-resources-title">值得探索</span>
              <small>
                {snapshot.resourcesPersonalized ? '根据你的画像排序' : '适合当前阶段的通用建议'}
              </small>
            </div>
            <Link to="/app/explore" className="today-text-link">
              查看更多
            </Link>
          </div>
          {snapshot.resources.length === 0 ? (
            <div className="today-section-empty is-compact">
              <h3>推荐资源暂未准备好</h3>
              <p>可以稍后同步，或先通过对话补充你想探索的方向。</p>
            </div>
          ) : (
            <div className="today-resource-list">
              {snapshot.resources.slice(0, 2).map((resource) => (
                <article key={resource.id}>
                  <span>{resource.resource_type}</span>
                  <div>
                    <h3>{resource.title}</h3>
                    <p>{resource.reason}</p>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="today-growth" aria-labelledby="today-growth-title">
          <div className="today-section-heading">
            <span id="today-growth-title">最近成长</span>
            <Link to="/app/growth" className="today-text-link">
              完整记录
            </Link>
          </div>
          <dl className="today-growth-ledger">
            <div>
              <dt>完成行动</dt>
              <dd>{snapshot.summary?.completed_count ?? 0}</dd>
            </div>
            <div>
              <dt>成长值</dt>
              <dd>{snapshot.summary?.growth_points ?? 0}</dd>
            </div>
          </dl>
          {snapshot.events.length > 0 ? (
            <div className="today-latest-event">
              <span>{formatEventTime(snapshot.events[0].created_at)}</span>
              <p>{snapshot.events[0].title}</p>
            </div>
          ) : (
            <p className="today-growth-empty">完成一次微行动后，第一条成长记录会出现在这里。</p>
          )}
        </section>
      </div>
    </section>
  );
};

export default Today;
