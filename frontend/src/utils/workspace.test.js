import assert from 'node:assert/strict';
import test from 'node:test';

test('学生工作台一级导航固定为五个成长入口，账号设置独立下沉', async () => {
  const { PRIMARY_NAV_ITEMS, ACCOUNT_NAV_ITEM } = await import('./workspace.js');

  assert.deepEqual(
    PRIMARY_NAV_ITEMS.map(({ key, label, to }) => ({ key, label, to })),
    [
      { key: 'today', label: '今日', to: '/app/today' },
      { key: 'chat', label: '对话', to: '/app/chat' },
      { key: 'tasks', label: '微行动', to: '/app/tasks' },
      { key: 'explore', label: '探索', to: '/app/explore' },
      { key: 'growth', label: '成长', to: '/app/growth' }
    ]
  );
  assert.equal(ACCOUNT_NAV_ITEM.to, '/app/settings');
});

test('今日聚合保留成功数据并明确标记局部降级', async () => {
  const { buildTodaySnapshot } = await import('./workspace.js');
  const task = { id: 7, description: '整理一次机器人观察记录' };
  const snapshot = buildTodaySnapshot([
    { status: 'fulfilled', value: { primary_task: task, tasks: [task] } },
    { status: 'fulfilled', value: { summary: '喜欢通过动手项目理解问题。' } },
    { status: 'rejected', reason: new Error('资源服务暂不可用') },
    {
      status: 'fulfilled',
      value: { days: 7, created_count: 2, completed_count: 1, growth_points: 8 }
    },
    { status: 'fulfilled', value: { events: [] } }
  ]);

  assert.equal(snapshot.primaryTask, task);
  assert.equal(snapshot.profile.summary, '喜欢通过动手项目理解问题。');
  assert.deepEqual(snapshot.resources, []);
  assert.equal(snapshot.isPartial, true);
  assert.equal(snapshot.isUnavailable, false);
  assert.deepEqual(snapshot.failedSections, ['resources']);
});

test('今日聚合在所有真实数据接口失败时进入可重试错误态', async () => {
  const { buildTodaySnapshot } = await import('./workspace.js');
  const failure = { status: 'rejected', reason: new Error('unauthorized') };
  const snapshot = buildTodaySnapshot([failure, failure, failure, failure, failure]);

  assert.equal(snapshot.isUnavailable, true);
  assert.equal(snapshot.isPartial, false);
  assert.equal(snapshot.primaryTask, null);
});
