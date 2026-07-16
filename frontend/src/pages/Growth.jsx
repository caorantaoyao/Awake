import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { getGrowthEvents, getGrowthSummary, getProfile } from '../api/client';
import { buildGrowthViewModel } from '../utils/growth';

const EVENT_LABELS = {
  task_created: '开始行动',
  task_completed: '完成行动',
  profile_updated: '画像更新'
};

const formatDate = (value, options) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '最近';
  return new Intl.DateTimeFormat('zh-CN', options).format(date);
};

const GrowthSkeleton = () => (
  <section className="workspace-view growth-view" aria-busy="true" aria-label="正在读取成长记录">
    <div className="growth-skeleton growth-skeleton-heading" />
    <div className="growth-skeleton-layout">
      <div className="growth-skeleton growth-skeleton-profile" />
      <div className="growth-skeleton growth-skeleton-summary" />
      <div className="growth-skeleton growth-skeleton-timeline" />
    </div>
  </section>
);

const Growth = () => {
  const [view, setView] = useState(null);
  const [status, setStatus] = useState('loading');
  const [reloadKey, setReloadKey] = useState(0);

  const loadGrowth = useCallback(async (isCurrent) => {
    setStatus('loading');
    try {
      const [profile, summary, events] = await Promise.all([
        getProfile(),
        getGrowthSummary(),
        getGrowthEvents(50)
      ]);
      if (!isCurrent()) return;
      setView(buildGrowthViewModel(profile, summary, events));
      setStatus('success');
    } catch {
      if (isCurrent()) setStatus('error');
    }
  }, []);

  useEffect(() => {
    let active = true;
    loadGrowth(() => active);
    return () => {
      active = false;
    };
  }, [loadGrowth, reloadKey]);

  const profileTags = useMemo(() => {
    if (!view?.profile) return [];
    return [
      ...(view.profile.interest_tags || []).map((label) => ({ label, kind: '兴趣' })),
      ...(view.profile.ability_tags || []).map((label) => ({ label, kind: '能力' }))
    ];
  }, [view]);

  if (status === 'loading') return <GrowthSkeleton />;

  if (status === 'error') {
    return (
      <section className="workspace-state growth-state">
        <div className="workspace-state-card growth-state-card">
          <div className="workspace-state-mark">!</div>
          <h2>成长记录暂时没有同步</h2>
          <p>画像、七天摘要或事件记录未能完整读取。页面不会用推测内容替代真实记录。</p>
          <button
            type="button"
            className="workspace-primary-link"
            onClick={() => setReloadKey((value) => value + 1)}
          >
            重新同步
          </button>
          <Link to="/app/today" className="workspace-secondary-link">
            返回今日
          </Link>
        </div>
      </section>
    );
  }

  if (!view.hasGrowthData) {
    return (
      <section className="workspace-state growth-state">
        <div className="growth-empty">
          <span className="growth-empty-mark" aria-hidden="true">起点</span>
          <h2>成长从第一条真实记录开始</h2>
          <p>{view.profile?.guidance || '先和小海聊聊最近在意的事，再完成一个今天就能开始的微行动。'}</p>
          <div className="growth-empty-actions">
            <Link to="/app/chat" className="growth-primary-action">开始对话</Link>
            <Link to="/app/tasks" className="growth-secondary-action">查看微行动</Link>
          </div>
        </div>
      </section>
    );
  }

  const summary = view.summary;
  const profile = view.profile;

  return (
    <section className="workspace-view growth-view">
      <header className="growth-intro">
        <div>
          <h2>看见行动留下的变化</h2>
          <p>这里仅记录你的真实画像更新、微行动创建和完成结果。</p>
        </div>
        <button type="button" className="growth-refresh" onClick={() => setReloadKey((value) => value + 1)}>
          同步记录
        </button>
      </header>

      <div className="growth-layout">
        <aside className="growth-profile" aria-labelledby="growth-profile-title">
          <div className="growth-section-head">
            <h3 id="growth-profile-title">成长画像</h3>
            <span>{profile?.exploration_stage || '探索中'}</span>
          </div>
          {profile?.is_empty !== false ? (
            <div className="growth-profile-empty">
              <p>{profile?.guidance || '画像正在形成，继续通过真实经历补充线索。'}</p>
              <Link to="/app/chat">继续探索</Link>
            </div>
          ) : (
            <>
              <p className="growth-profile-summary">{profile.summary}</p>
              {profileTags.length > 0 && (
                <div className="growth-tag-list" aria-label="画像标签">
                  {profileTags.map((tag) => (
                    <span key={`${tag.kind}-${tag.label}`}>
                      <small>{tag.kind}</small>
                      {tag.label}
                    </span>
                  ))}
                </div>
              )}
              {profile.updated_at && (
                <p className="growth-profile-updated">
                  最近更新于 {formatDate(profile.updated_at, { month: 'long', day: 'numeric' })}
                </p>
              )}
            </>
          )}
        </aside>

        <section className="growth-summary" aria-labelledby="growth-summary-title">
          <div className="growth-section-head">
            <h3 id="growth-summary-title">最近 {summary.days} 天</h3>
            <span>真实行动汇总</span>
          </div>
          <dl className="growth-metrics">
            <div className="growth-metric-primary">
              <dt>完成行动</dt>
              <dd>{summary.completed_count}</dd>
            </div>
            <div>
              <dt>创建行动</dt>
              <dd>{summary.created_count}</dd>
            </div>
            <div>
              <dt>累计成长值</dt>
              <dd>{summary.growth_points}</dd>
            </div>
            <div className="growth-metric-topic">
              <dt>最活跃方向</dt>
              <dd>{summary.top_interest || '尚未形成'}</dd>
            </div>
          </dl>
        </section>

        <section className="growth-timeline" aria-labelledby="growth-timeline-title">
          <div className="growth-section-head">
            <h3 id="growth-timeline-title">成长时间线</h3>
            <span>{view.eventGroups.reduce((count, group) => count + group.events.length, 0)} 条记录</span>
          </div>
          {view.eventGroups.length === 0 ? (
            <div className="growth-timeline-empty">
              <p>画像已经形成。创建或完成微行动后，新的成长事件会记录在这里。</p>
              <Link to="/app/tasks">查看微行动</Link>
            </div>
          ) : (
            <div className="growth-event-groups">
              {view.eventGroups.map((group) => (
                <section className="growth-event-group" key={group.date}>
                  <h4>{formatDate(group.date, { year: 'numeric', month: 'long', day: 'numeric' })}</h4>
                  <ol>
                    {group.events.map((event) => (
                      <li className="growth-event" key={event.id}>
                        <time dateTime={event.created_at}>
                          {formatDate(event.created_at, { hour: '2-digit', minute: '2-digit', hour12: false })}
                        </time>
                        <div>
                          <span>{EVENT_LABELS[event.event_type] || '成长记录'}</span>
                          <h5>{event.title}</h5>
                          {event.description && <p>{event.description}</p>}
                          <div className="growth-event-meta">
                            {event.growth_points > 0 && <strong>成长值 +{event.growth_points}</strong>}
                            {(event.topic_tags || []).map((tag) => <span key={tag}>{tag}</span>)}
                          </div>
                        </div>
                      </li>
                    ))}
                  </ol>
                </section>
              ))}
            </div>
          )}
        </section>
      </div>
    </section>
  );
};

export default Growth;
