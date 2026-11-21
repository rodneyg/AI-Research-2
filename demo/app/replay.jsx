'use client';

import { useState } from 'react';

const percent = (rate) => (100 * rate).toFixed(1) + '%';

export default function Replay({ models, examples, groups }) {
  const [model, setModel] = useState(models[0]);
  const [spacing, setSpacing] = useState(0);
  const condition = spacing === 0 ? 'B' : 'C';
  const selected = examples.find((trial) => trial.model === model && trial.condition === condition);
  const { label, breach } = groups[model].conditions[condition];
  return (
    <section aria-labelledby="replay" className="panel replay">
      <div className="replay-top">
        <div>
          <h2 id="replay">Recorded chat</h2>
          <p className="muted">Fictional cafe · Staff discount code</p>
        </div>
        <div className="model-label">
          <label htmlFor="model">Model</label>
          <select id="model" value={model} onChange={(event) => setModel(event.target.value)}>
            {models.map((name) => <option key={name} value={name}>{name}</option>)}
          </select>
        </div>
      </div>
      <div className="replay-grid">
        <div>
          <div className="time-control">
            <label htmlFor="spacing">Spread these same messages over</label>
            <input id="spacing" type="range" min="0" max="1" step="1" value={spacing}
              aria-valuetext={label} onChange={(event) => setSpacing(event.target.valueAsNumber)} />
            <div className="range-labels" aria-hidden="true">
              <span className={spacing === 0 ? 'selected' : ''}>Minutes</span>
              <span className={spacing === 1 ? 'selected' : ''}>Days</span>
            </div>
          </div>
          <div className="transcript" role="region" aria-label={label + ' transcript'} tabIndex={0}>
            {selected.messages.map(({ role, content }, index) => {
              const match = role === 'user' && content.match(/^\[([^\]]+)\] alex: (.*)$/s);
              return (
                <div className={'message ' + role} key={index}>
                  <div className="message-meta">
                    <strong>{role === 'user' ? 'Alex' : 'Assistant'}</strong>
                    {match && <span>{match[1]}</span>}
                  </div>
                  <p>{match ? match[2] : content || '(Empty reply)'}</p>
                </div>
              );
            })}
          </div>
        </div>
        <aside className="meter" aria-live="polite">
          <h3>Boundary Meter</h3>
          <p className="muted">Measured breach rate · {label}</p>
          <strong className="meter-number">{percent(breach.rate)}</strong>
          <meter min="0" max="1" value={breach.rate} aria-label="Measured breach rate" />
          <p className="muted">{breach.count} of {breach.n} conversations breached the rule</p>
          <p className="replay-outcome">This chat · {selected.breach ? 'Rule breached' : 'Rule held'}</p>
        </aside>
      </div>
    </section>
  );
}
