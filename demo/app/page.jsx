import data from '../../results/summary.json';
import Replay from './replay';

const percent = (rate) => (100 * rate).toFixed(1) + '%';
const repo = 'https://github.com/rodneyg/AI-Research-2';
const pooled = data.groups['All models'];
const minutes = pooled.conditions.B;
const days = pooled.conditions.C;
const difference = pooled.paired.difference;
const signedDifference = (difference > 0 ? '+' : '') + (difference * 100).toFixed(1);
const modelLabel = (name) => name.replace(/-20\d{2}-\d{2}-\d{2}$/, '');
const conditionKeys = ['A', 'B', 'C', 'D'];
const ceiling = Math.min(100, Math.max(10, Math.ceil(Math.max(...data.models.flatMap((model) =>
  conditionKeys.map((key) => data.groups[model].conditions[key].breach.ci[1]))) * 10) * 10));

function BreachChart() {
  return (
    <section aria-labelledby="rates" className="panel section-panel">
      <div className="chart-header">
        <h2 id="rates">How often the rule broke</h2>
        <p className="muted">Dots show measured rates. Lines show 95% Wilson intervals.</p>
      </div>
      <div className="chart-axis" aria-hidden="true">
        {[0, 1, 2, 3, 4].map((step) => <span key={step}>{ceiling * step / 4}%</span>)}
      </div>
      {conditionKeys.map((key) => (
        <div key={key} className="chart-condition">
          <h3>{pooled.conditions[key].label}</h3>
          {data.models.map((model, index) => {
            const { rate, ci, n, count } = data.groups[model].conditions[key].breach;
            const label = percent(rate) + ' · ' + count + '/' + n;
            return (
              <div key={model} className={'plot-row series-' + index}>
                <span>{modelLabel(model)}</span>
                <div className="track" aria-hidden="true">
                  <span className="interval" style={{ left: (10000 * ci[0] / ceiling) + '%',
                    width: (10000 * (ci[1] - ci[0]) / ceiling) + '%' }} />
                  <span className="point" style={{ left: (10000 * rate / ceiling) + '%' }} />
                </div>
                <span className="plot-value" title={'95% CI ' + percent(ci[0]) + ' to ' + percent(ci[1])}>
                  {label}<span className="sr-only">, 95% CI {percent(ci[0])} to {percent(ci[1])}</span>
                </span>
              </div>
            );
          })}
        </div>
      ))}
      <p className="monitor"><strong>Monitor catch rate</strong> · Minutes {percent(minutes.monitor.rate)} ({minutes.monitor.count}/{minutes.monitor.n}) · Days {percent(days.monitor.rate)} ({days.monitor.count}/{days.monitor.n})</p>
    </section>
  );
}

export default function Page() {
  const noClearChange = pooled.paired.p >= 0.05;
  return (
    <main className="mx-auto w-full max-w-6xl px-4 pb-10 sm:px-8">
      <header className="hero">
        <h1>{data.title}</h1>
        <p>If someone pushes an AI past its rules one small step at a time, does it matter whether those steps come minutes apart or days apart?</p>
      </header>
      <section className="finding panel" aria-labelledby="finding">
        <h2 id="finding">What we found</h2>
        <p><strong>{noClearChange ? 'This small pilot found no clear effect of timestamp spacing.' :
          'Breach rates shifted with timestamp spacing in this small pilot.'}</strong>
          {' '}Across both models, {percent(minutes.breach.rate)} breached with minutes between messages
          (95% CI {percent(minutes.breach.ci[0])} to {percent(minutes.breach.ci[1])}) and {percent(days.breach.rate)} with days
          (95% CI {percent(days.breach.ci[0])} to {percent(days.breach.ci[1])}).
          The change was {signedDifference} percentage points (paired sign test, p = {pooled.paired.p.toFixed(3)}).
        </p>
      </section>
      <Replay models={data.models} examples={data.example} groups={data.groups} />
      <BreachChart />
      <section className="panel section-panel" aria-labelledby="method">
        <h2 id="method">How we tested</h2>
        <p>We ran {data.sequences} fictional sequences of six user messages with {data.samples} trials per condition
          on each of two models ({data.n} conversations). The minutes and days conditions kept the same
          user text and full conversation history. The other conditions removed timestamps or sent only
          the final request. We counted a breach when the model printed the protected fictional value.
        </p>
        <p>A separate call showed the finished chat to the same model and asked if the user had gradually
          pushed it to break a rule. This measures detection on escalation examples. The pilot used
          timestamp labels in replayed chats, with all calls made during the same run. Replies had a
          64-token limit, so some end mid-sentence.
        </p>
        <dl className="method-grid">
          <div><dt>Model snapshots</dt><dd>{data.models.join(', ')}</dd></div>
          <div><dt>Temperature</dt><dd>{data.temperature} chat · 0 monitor</dd></div>
          <div><dt>Token cost</dt><dd>${data.spend_usd.toFixed(4)}</dd></div>
          <div><dt>Recorded (UTC)</dt><dd>{data.date === data.end_date ? data.date : data.date + ' to ' + data.end_date}</dd></div>
        </dl>
      </section>
      <footer className="footer">
        <p>Real model calls, recorded on {data.date}. No AI is called on this page.</p>
        <div><a href={repo}>Source and data</a><a href={repo + '/blob/main/PRIOR_WORK_SEARCH.md'}>Prior-work search</a></div>
      </footer>
    </main>
  );
}
