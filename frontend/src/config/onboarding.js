export const ONBOARDING_STEPS = [
  {
    id: 'interest',
    question: (name) => `你好，${name}！很高兴认识你 👋\n\n在我们正式开始之前，想先了解一下——你目前对哪些方向比较好奇？`,
    options: [
      { label: 'AI / 计算机', emoji: '🤖', value: 'AI/计算机' },
      { label: '医学 / 生命科学', emoji: '🏥', value: '医学' },
      { label: '设计 / 艺术', emoji: '🎨', value: '设计/艺术' },
      { label: '商业 / 金融', emoji: '💼', value: '商业/金融' },
      { label: '工程 / 科研', emoji: '🔬', value: '工程/科研' },
      { label: '人文 / 社科', emoji: '📝', value: '人文/社科' },
    ],
    uncertain: { label: '还不太确定', emoji: '🤔', value: '待探索' },
    multiSelect: false,
  },
  {
    id: 'confusion',
    question: (name, answers) => {
      const interest = answers.interest?.[0] || '这些方向';
      return `${interest}很有意思！\n\n那你现在最想搞清楚的是什么？`;
    },
    getOptions: (answers) => {
      const interest = answers.interest?.[0];
      if (interest === '待探索') {
        return [
          { label: '不知道自己喜欢什么', emoji: '🌫️', value: '方向迷茫' },
          { label: '想多了解各个领域', emoji: '🔍', value: '需要探索' },
          { label: '不知道怎么开始', emoji: '🚀', value: '不知如何开始' },
          { label: '学业压力大，没时间想', emoji: '📚', value: '学业繁忙' },
        ];
      }
      return [
        { label: '这个方向要学什么', emoji: '📚', value: '学什么' },
        { label: '大学选什么专业', emoji: '🎓', value: '选专业' },
        { label: '未来能做什么工作', emoji: '💼', value: '职业方向' },
        { label: '怎么开始入门', emoji: '🚀', value: '如何入门' },
      ];
    },
    uncertain: { label: '说不清，都有点懵', emoji: '😅', value: '整体困惑' },
    multiSelect: false,
  },
  {
    id: 'style',
    question: () => '明白了！最后一个问题——\n\n课余时间你更喜欢怎么学习新东西？',
    options: [
      { label: '看视频 / 教程', emoji: '👀', value: '视觉学习' },
      { label: '看书 / 文章', emoji: '📖', value: '阅读学习' },
      { label: '动手做项目', emoji: '🔨', value: '实践学习' },
      { label: '和人聊 / 讨论', emoji: '💬', value: '交流学习' },
    ],
    multiSelect: false,
  },
];
