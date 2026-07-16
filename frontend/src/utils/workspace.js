export const PRIMARY_NAV_ITEMS = [
  { key: 'today', label: '今日', description: '今天的起点', to: '/app/today' },
  { key: 'chat', label: '对话', description: '和小海探索', to: '/app/chat' },
  { key: 'tasks', label: '微行动', description: '任务与打卡', to: '/app/tasks' },
  { key: 'explore', label: '探索', description: '资源与方向', to: '/app/explore' },
  { key: 'growth', label: '成长', description: '记录与变化', to: '/app/growth' }
];

export const ACCOUNT_NAV_ITEM = {
  key: 'settings',
  label: '账号设置',
  description: '账号与偏好',
  to: '/app/settings'
};

const SNAPSHOT_KEYS = ['todayTasks', 'profile', 'resources', 'summary', 'events'];

const valueOr = (result, fallback) =>
  result?.status === 'fulfilled' ? result.value : fallback;

export const buildTodaySnapshot = (results) => {
  const failedSections = SNAPSHOT_KEYS.filter(
    (_, index) => results[index]?.status !== 'fulfilled'
  );
  const todayTasks = valueOr(results[0], { primary_task: null, tasks: [] });
  const resourcesResponse = valueOr(results[2], { personalized: false, resources: [] });
  const eventsResponse = valueOr(results[4], { events: [] });

  return {
    primaryTask: todayTasks.primary_task ?? null,
    tasks: todayTasks.tasks ?? [],
    profile: valueOr(results[1], null),
    resources: resourcesResponse.resources ?? [],
    resourcesPersonalized: resourcesResponse.personalized === true,
    summary: valueOr(results[3], null),
    events: eventsResponse.events ?? [],
    failedSections,
    isPartial: failedSections.length > 0 && failedSections.length < SNAPSHOT_KEYS.length,
    isUnavailable: failedSections.length === SNAPSHOT_KEYS.length
  };
};
