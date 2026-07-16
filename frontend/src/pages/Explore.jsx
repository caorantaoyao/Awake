import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getResources } from '../api/client';
import { buildExploreViewModel } from '../utils/growth';

const RESOURCE_TYPES = ['', '课程', '活动', '竞赛', '实践'];
const EMPTY_VIEW = buildExploreViewModel(null);

const ExploreSkeleton = () => (
  <section className="workspace-view explore-view" aria-busy="true" aria-label="正在读取探索资源">
    <div className="explore-skeleton explore-skeleton-heading" />
    <div className="explore-skeleton explore-skeleton-filters" />
    <div className="explore-skeleton-grid">
      <div className="explore-skeleton explore-skeleton-card" />
      <div className="explore-skeleton explore-skeleton-card" />
    </div>
  </section>
);

const Explore = () => {
  const [resourceType, setResourceType] = useState('');
  const [view, setView] = useState(EMPTY_VIEW);
  const [status, setStatus] = useState('loading');
  const [reloadKey, setReloadKey] = useState(0);

  const loadResources = useCallback(async (activeType, isCurrent) => {
    setStatus('loading');
    try {
      const response = await getResources(activeType || undefined);
      if (!isCurrent()) return;
      setView(buildExploreViewModel(response));
      setStatus('success');
    } catch {
      if (isCurrent()) setStatus('error');
    }
  }, []);

  useEffect(() => {
    let active = true;
    loadResources(resourceType, () => active);
    return () => {
      active = false;
    };
  }, [loadResources, reloadKey, resourceType]);

  if (status === 'loading') return <ExploreSkeleton />;

  if (status === 'error') {
    return (
      <section className="workspace-state explore-state">
        <div className="workspace-state-card explore-state-card">
          <div className="workspace-state-mark">!</div>
          <h2>探索资源暂时没有同步</h2>
          <p>资源服务没有返回结果。重新同步不会影响已经形成的画像和成长记录。</p>
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
    <section className="workspace-view explore-view">
      <header className="explore-intro">
        <div>
          <h2>把兴趣带到真实世界</h2>
          <p>
            {view.personalized
              ? '这些资源依据你的兴趣、能力和探索阶段排序。'
              : '画像还在形成，先从适合当前年级和探索阶段的通用资源开始。'}
          </p>
        </div>
        <Link to="/app/chat" className="explore-profile-link">
          {view.personalized ? '继续补充画像' : '和小海聊聊方向'}
        </Link>
      </header>

      <div className="explore-filter-wrap">
        <span id="explore-filter-label">资源类型</span>
        <div className="explore-filters" role="group" aria-labelledby="explore-filter-label">
          {RESOURCE_TYPES.map((type) => (
            <button
              key={type || 'all'}
              type="button"
              className={`explore-filter${resourceType === type ? ' is-active' : ''}`}
              aria-pressed={resourceType === type}
              onClick={() => setResourceType(type)}
            >
              {type || '全部'}
            </button>
          ))}
        </div>
      </div>

      {view.isEmpty ? (
        <div className="explore-empty">
          <h3>这个类型暂时没有可用资源</h3>
          <p>资源目录会持续维护。你可以切换其他类型，或通过对话明确下一步想探索的方向。</p>
          <button
            type="button"
            onClick={() => (
              resourceType
                ? setResourceType('')
                : setReloadKey((value) => value + 1)
            )}
          >
            {resourceType ? '查看全部资源' : '重新同步'}
          </button>
        </div>
      ) : (
        <div className="explore-resource-grid" aria-live="polite">
          {view.resources.map((resource) => (
            <article className="explore-resource" key={resource.id}>
              <div className="explore-resource-type">{resource.resource_type}</div>
              <div className="explore-resource-copy">
                <h3>{resource.title}</h3>
                <p>{resource.description}</p>
              </div>
              <div className="explore-reason">
                <span>推荐理由</span>
                <p>{resource.reason}</p>
              </div>
              {resource.url ? (
                <a
                  className="explore-resource-action"
                  href={resource.url}
                  target="_blank"
                  rel="noreferrer"
                >
                  查看资源
                </a>
              ) : (
                <span className="explore-resource-unavailable">线下即可开始</span>
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  );
};

export default Explore;
