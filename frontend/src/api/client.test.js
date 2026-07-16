import assert from 'node:assert/strict';
import test from 'node:test';

test('成长 API 客户端使用后端真实路径和查询参数', async () => {
  globalThis.localStorage = {
    getItem: () => null
  };
  const client = await import('./client.js');
  const requests = [];
  client.default.defaults.adapter = async (config) => {
    requests.push(config);
    return {
      data: { ok: true },
      status: 200,
      statusText: 'OK',
      headers: {},
      config
    };
  };

  await client.getProfile();
  await client.updateProfile({ summary: '喜欢机器人' });
  await client.getChatHistory(20);
  await client.getTodayTasks();
  await client.getResources('实践');
  await client.getGrowthEvents(10);
  await client.getGrowthSummary();

  assert.deepEqual(
    requests.map(({ method, url, params }) => ({ method, url, params })),
    [
      { method: 'get', url: '/profile', params: undefined },
      { method: 'put', url: '/profile', params: undefined },
      { method: 'get', url: '/chat/history', params: { limit: 20 } },
      { method: 'get', url: '/tasks/today', params: undefined },
      { method: 'get', url: '/resources', params: { resource_type: '实践' } },
      { method: 'get', url: '/growth/events', params: { limit: 10 } },
      { method: 'get', url: '/growth/summary', params: undefined }
    ]
  );
  assert.equal(requests[1].data, JSON.stringify({ summary: '喜欢机器人' }));
});
