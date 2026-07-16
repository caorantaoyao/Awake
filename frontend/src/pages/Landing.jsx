import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';

const journeySteps = [
  {
    number: '01',
    title: '说说最近的困惑',
    description: '不用准备标准答案，从一件让你好奇、犹豫或有成就感的小事开始。'
  },
  {
    number: '02',
    title: '和小海一起追问',
    description: '小海不会急着替你做决定，而是帮你看见兴趣、能力与选择背后的线索。'
  },
  {
    number: '03',
    title: '带走今天的一小步',
    description: '把方向变成当天能完成的微行动，用真实体验继续校准自己的判断。'
  }
];

const Landing = () => {
  return (
    <>
      <Navbar />
      <main className="landing-page">
        <section className="hero" aria-labelledby="landing-title">
          <div className="hero-copy">
            <p className="hero-eyebrow">从一次真诚对话，找到下一步</p>
            <h1 className="hero-title" id="landing-title">方向不用猜，先去真实体验</h1>
            <p className="hero-desc">
              和 AI 成长伙伴「小海」聊聊你的兴趣与困惑，把模糊想法变成今天就能完成的微行动。
            </p>
            <div className="hero-cta">
              <Link to="/register" className="btn-hero-primary">开始和小海对话</Link>
              <a href="#how-it-works" className="btn-hero-explore">
                看看如何开始
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="m9 18 6-6-6-6"/>
                </svg>
              </a>
            </div>
          </div>

          <div className="hero-visual">
            <div className="hero-image-wrap">
              <img src="/hero-students-blue.jpg" alt="两位高中生一起讨论未来方向" />
            </div>

            <div className="float-card card-badge" aria-label="微行动示例">
              <div className="badge-progress">
                <svg viewBox="0 0 56 56" aria-hidden="true">
                  <circle className="progress-track" cx="28" cy="28" r="22"/>
                  <circle className="progress-bar-circle" cx="28" cy="28" r="22"/>
                </svg>
                <span className="progress-dot">完成</span>
              </div>
              <div className="badge-content">
                <span className="badge-label">今天的一小步</span>
                <span className="badge-title">已打卡</span>
              </div>
            </div>

            <div className="float-card card-actions" aria-label="今日微行动示例">
              <span className="actions-header">今日微行动</span>
              <div className="actions-item">
                <div className="actions-check">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </div>
                <span className="actions-text">找一位学长，问三个关于真实专业生活的问题</span>
              </div>
            </div>
          </div>
        </section>

        <section className="landing-section journey-section" id="how-it-works" aria-labelledby="journey-title">
          <div className="landing-section-heading">
            <p className="landing-kicker">从想法到行动</p>
            <h2 id="journey-title">不替你做决定，陪你把答案走出来</h2>
            <p>生涯方向不是一次测评的结论，而是在持续探索中越来越清楚的判断。</p>
          </div>
          <div className="journey-grid">
            {journeySteps.map((step) => (
              <article className="journey-step" key={step.number}>
                <span className="journey-number" aria-hidden="true">{step.number}</span>
                <h3>{step.title}</h3>
                <p>{step.description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="landing-section xiaohai-section" id="meet-xiaohai" aria-labelledby="xiaohai-title">
          <div className="xiaohai-copy">
            <p className="landing-kicker">认识小海</p>
            <h2 id="xiaohai-title">先听懂你，再和你一起往前走</h2>
            <p>
              小海会记住你提到的线索，用具体问题帮你辨认真正重视的事。没有标签，没有标准答案，也不会催你立刻选定一生。
            </p>
            <ul className="xiaohai-principles">
              <li>用追问代替武断建议</li>
              <li>把抽象方向落到真实场景</li>
              <li>每次只推进一个可完成的小行动</li>
            </ul>
          </div>
          <div className="conversation-preview" aria-label="小海对话示例">
            <div className="conversation-line conversation-line-user">
              我喜欢生物，但不知道自己是真的喜欢研究，还是只是成绩还不错。
            </div>
            <div className="conversation-line conversation-line-xiaohai">
              如果暂时不看成绩，最近哪一次接触生物时，你会忍不住继续查下去？
            </div>
            <div className="conversation-caption">小海会从真实经历继续追问，而不是直接推荐专业。</div>
          </div>
        </section>

        <section className="landing-section action-section" id="micro-actions" aria-labelledby="action-title">
          <div className="landing-section-heading">
            <p className="landing-kicker">今天就能开始</p>
            <h2 id="action-title">好方向，要经得起一次真实行动</h2>
            <p>每个任务都足够小、足够具体，也会告诉你做完后该观察什么。</p>
          </div>
          <article className="action-example">
            <div className="action-example-meta">
              <span>预计 15 分钟</span>
              <span>职业访谈</span>
            </div>
            <h3>向一位相关专业的学长提三个问题</h3>
            <p>了解他一天如何学习、最意外的困难是什么，以及他会给高中时期的自己什么建议。</p>
            <div className="action-reflection">完成后记录：哪一个回答最改变你的想象？</div>
          </article>
        </section>

        <section className="landing-section trust-section" id="trust" aria-labelledby="trust-title">
          <div className="trust-copy">
            <p className="landing-kicker">安心探索</p>
            <h2 id="trust-title">你的选择，始终由你决定</h2>
          </div>
          <div className="trust-points">
            <article>
              <h3>不贴标签</h3>
              <p>对话用于发现线索，不把一次回答变成固定结论。</p>
            </article>
            <article>
              <h3>不替代专业咨询</h3>
              <p>遇到心理、医疗或重大升学决策时，应继续寻求老师与专业人士支持。</p>
            </article>
            <article>
              <h3>少一点个人信息</h3>
              <p>探索时无需提供身份证、住址等敏感信息，分享与你的问题有关的内容即可。</p>
            </article>
          </div>
        </section>

        <section className="landing-final-cta" aria-labelledby="final-cta-title">
          <p>不必先想清楚未来十年</p>
          <h2 id="final-cta-title">先找到今天愿意迈出的那一步</h2>
          <Link to="/register" className="btn-hero-primary">开始和小海对话</Link>
          <span>已有账号？<Link to="/login">继续上次的探索</Link></span>
        </section>
      </main>
    </>
  );
};

export default Landing;
