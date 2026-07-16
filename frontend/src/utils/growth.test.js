import assert from 'node:assert/strict';
import test from 'node:test';

test('buildExploreViewModel 保留后端个性化标记和真实资源', async () => {
  const { buildExploreViewModel } = await import('./growth.js');
  const resources = [
    { id: 'robot', resource_type: '实践', reason: '与你关注的机器人方向相关' }
  ];

  assert.deepEqual(
    buildExploreViewModel({ personalized: true, resources }),
    {
      personalized: true,
      resources,
      isEmpty: false
    }
  );
  assert.deepEqual(
    buildExploreViewModel({ personalized: false, resources: [] }),
    {
      personalized: false,
      resources: [],
      isEmpty: true
    }
  );
});

test('buildGrowthViewModel 只根据真实画像、摘要和事件生成页面状态', async () => {
  const { buildGrowthViewModel } = await import('./growth.js');
  const profile = {
    is_empty: false,
    summary: '喜欢通过项目理解机器人。',
    interest_tags: ['机器人'],
    ability_tags: ['动手实践']
  };
  const summary = {
    days: 7,
    created_count: 2,
    completed_count: 1,
    growth_points: 8,
    top_interest: '机器人'
  };
  const events = [{ id: 2, created_at: '2026-07-16T11:00:00', title: '完成微行动' }];

  assert.deepEqual(
    buildGrowthViewModel(profile, summary, { events }),
    {
      profile,
      summary,
      eventGroups: [{ date: '2026-07-16', events }],
      hasGrowthData: true
    }
  );

  const emptyProfile = {
    is_empty: true,
    summary: '',
    interest_tags: [],
    ability_tags: []
  };
  assert.equal(
    buildGrowthViewModel(
      emptyProfile,
      { days: 7, created_count: 0, completed_count: 0, growth_points: 0, top_interest: null },
      { events: [] }
    ).hasGrowthData,
    false
  );
});

test('groupGrowthEventsByDate 按日期倒序分组且事件保持倒序', async () => {
  const { groupGrowthEventsByDate } = await import('./growth.js');
  const events = [
    { id: 1, created_at: '2026-07-15T09:00:00' },
    { id: 3, created_at: '2026-07-16T11:00:00' },
    { id: 2, created_at: '2026-07-16T08:00:00' }
  ];

  assert.deepEqual(groupGrowthEventsByDate(events), [
    { date: '2026-07-16', events: [events[1], events[2]] },
    { date: '2026-07-15', events: [events[0]] }
  ]);
});

test('restoreFocusTimer 刷新后扣除运行时间并保留暂停时间', async () => {
  const { restoreFocusTimer } = await import('./growth.js');
  const now = Date.parse('2026-07-16T10:00:30Z');

  assert.deepEqual(
    restoreFocusTimer(
      {
        status: 'running',
        remainingSeconds: 600,
        savedAt: '2026-07-16T10:00:00Z'
      },
      now
    ),
    { status: 'running', remainingSeconds: 570, savedAt: now }
  );
  assert.deepEqual(
    restoreFocusTimer(
      {
        status: 'paused',
        remainingSeconds: 420,
        savedAt: '2026-07-16T09:00:00Z'
      },
      now
    ),
    { status: 'paused', remainingSeconds: 420, savedAt: now }
  );
});

test('对话历史仅保留用户和助手消息并按用户轮次恢复任务解锁状态', async () => {
  const { restoreConversation } = await import('./growth.js');
  const history = {
    messages: [
      { id: 1, role: 'system', content: '内部规则' },
      { id: 2, role: 'assistant', content: '你最近在关注什么？' },
      { id: 3, role: 'user', content: '机器人' },
      { id: 4, role: 'user', content: '我喜欢动手' },
      { id: 5, role: 'assistant', content: '还有吗？' },
      { id: 6, role: 'user', content: '也喜欢写代码' }
    ]
  };

  assert.deepEqual(restoreConversation(history), {
    messages: [
      { role: 'assistant', content: '你最近在关注什么？' },
      { role: 'user', content: '机器人' },
      { role: 'user', content: '我喜欢动手' },
      { role: 'assistant', content: '还有吗？' },
      { role: 'user', content: '也喜欢写代码' }
    ],
    canExtractTask: true
  });
});

test('微行动分组始终以进行中为首并按截止时间排序', async () => {
  const { groupTasksForActionList } = await import('./growth.js');
  const tasks = [
    { id: 1, status: '已完成', completed_at: '2026-07-16T08:00:00Z' },
    { id: 2, status: '进行中', deadline: '2026-07-18T08:00:00Z' },
    { id: 3, status: '已过期', deadline: '2026-07-15T08:00:00Z' },
    { id: 4, status: '进行中', deadline: '2026-07-17T08:00:00Z' }
  ];

  const groups = groupTasksForActionList(tasks, Date.parse('2026-07-16T09:00:00Z'));

  assert.deepEqual(groups.map(({ key, tasks: items }) => ({
    key,
    ids: items.map((task) => task.id)
  })), [
    { key: 'active', ids: [4, 2] },
    { key: 'completed', ids: [1] },
    { key: 'expired', ids: [3] }
  ]);
});

test('AI Focus 支持开始暂停继续结束并持久化可恢复快照', async () => {
  const {
    createFocusTimer,
    pauseFocusTimer,
    resumeFocusTimer,
    finishFocusTimer
  } = await import('./growth.js');
  const startedAt = Date.parse('2026-07-16T10:00:00Z');
  const started = createFocusTimer({ id: 7, estimated_minutes: 10 }, startedAt);
  const paused = pauseFocusTimer(started, startedAt + 30_000);
  const resumed = resumeFocusTimer(paused, startedAt + 60_000);
  const finished = finishFocusTimer(resumed, startedAt + 90_000);

  assert.deepEqual(started, {
    taskId: 7,
    status: 'running',
    remainingSeconds: 600,
    savedAt: startedAt
  });
  assert.equal(paused.status, 'paused');
  assert.equal(paused.remainingSeconds, 570);
  assert.equal(resumed.status, 'running');
  assert.equal(resumed.remainingSeconds, 570);
  assert.equal(finished.status, 'completed');
  assert.equal(finished.remainingSeconds, 0);
  assert.equal(pauseFocusTimer(started, startedAt + 600_000).status, 'completed');
});
