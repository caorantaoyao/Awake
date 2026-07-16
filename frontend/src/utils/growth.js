export const buildExploreViewModel = (response) => {
  const resources = response?.resources ?? [];
  return {
    personalized: response?.personalized === true,
    resources,
    isEmpty: resources.length === 0
  };
};

export const groupGrowthEventsByDate = (events) => {
  const groups = new Map();
  const sortedEvents = [...events].sort((left, right) =>
    right.created_at.localeCompare(left.created_at)
  );

  sortedEvents.forEach((event) => {
    const date = event.created_at.slice(0, 10);
    const group = groups.get(date) ?? [];
    group.push(event);
    groups.set(date, group);
  });

  return Array.from(groups, ([date, groupedEvents]) => ({
    date,
    events: groupedEvents
  }));
};

export const buildGrowthViewModel = (profile, summary, eventsResponse) => {
  const events = eventsResponse?.events ?? [];
  return {
    profile,
    summary,
    eventGroups: groupGrowthEventsByDate(events),
    hasGrowthData:
      profile?.is_empty === false
      || (summary?.created_count ?? 0) > 0
      || (summary?.completed_count ?? 0) > 0
      || (summary?.growth_points ?? 0) > 0
      || events.length > 0
  };
};

export const restoreConversation = (history) => {
  const messages = (history?.messages ?? [])
    .filter((message) => ['user', 'assistant'].includes(message.role))
    .map(({ role, content }) => ({ role, content }));

  return {
    messages,
    canExtractTask: messages.filter((message) => message.role === 'user').length >= 3
  };
};

const taskGroup = (task, now) => {
  if (task.status === '已完成') return 'completed';
  if (task.status === '已过期') return 'expired';
  if (task.deadline) {
    const deadline = new Date(task.deadline).getTime();
    if (Number.isFinite(deadline) && deadline < now) return 'expired';
  }
  return 'active';
};

const taskTime = (task, key, fallback) => {
  const value = new Date(task[key]).getTime();
  return Number.isFinite(value) ? value : fallback;
};

export const groupTasksForActionList = (tasks, now = Date.now()) => {
  const groups = [
    { key: 'active', title: '进行中', hint: '今天就能推进的小行动', tasks: [] },
    { key: 'completed', title: '已完成', hint: '已经沉淀下来的行动', tasks: [] },
    { key: 'expired', title: '已过期', hint: '可以重新选择节奏', tasks: [] }
  ];
  const byKey = new Map(groups.map((group) => [group.key, group]));

  tasks.forEach((task) => {
    byKey.get(taskGroup(task, now)).tasks.push(task);
  });
  byKey.get('active').tasks.sort(
    (left, right) =>
      taskTime(left, 'deadline', Number.POSITIVE_INFINITY)
      - taskTime(right, 'deadline', Number.POSITIVE_INFINITY)
      || taskTime(left, 'created_at', 0) - taskTime(right, 'created_at', 0)
  );
  byKey.get('completed').tasks.sort(
    (left, right) =>
      taskTime(right, 'completed_at', 0) - taskTime(left, 'completed_at', 0)
  );

  return groups;
};

export const restoreFocusTimer = (snapshot, now = Date.now()) => {
  const remainingSeconds = Math.max(0, snapshot.remainingSeconds);
  if (snapshot.status !== 'running') {
    return { ...snapshot, remainingSeconds, savedAt: now };
  }

  const savedAt = new Date(snapshot.savedAt).getTime();
  const elapsedSeconds = Math.max(0, Math.floor((now - savedAt) / 1000));
  const restoredSeconds = Math.max(0, remainingSeconds - elapsedSeconds);

  return {
    ...snapshot,
    status: restoredSeconds === 0 ? 'completed' : 'running',
    remainingSeconds: restoredSeconds,
    savedAt: now
  };
};

export const createFocusTimer = (task, now = Date.now()) => ({
  taskId: task.id,
  status: 'running',
  remainingSeconds: Math.max(1, task.estimated_minutes || 15) * 60,
  savedAt: now
});

export const pauseFocusTimer = (snapshot, now = Date.now()) => {
  const restored = restoreFocusTimer(snapshot, now);
  return {
    ...restored,
    status: restored.status === 'completed' ? 'completed' : 'paused',
    savedAt: now
  };
};

export const resumeFocusTimer = (snapshot, now = Date.now()) => ({
  ...snapshot,
  status: 'running',
  savedAt: now
});

export const finishFocusTimer = (snapshot, now = Date.now()) => ({
  ...snapshot,
  status: 'completed',
  remainingSeconds: 0,
  savedAt: now
});
