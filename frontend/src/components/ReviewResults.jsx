import { useState } from 'react';
import { AlertTriangle, AlertCircle, Info, CheckCircle, CheckCircle2 } from 'lucide-react';

function ScoreRing({ score }) {
  const circumference = 2 * Math.PI * 42;
  const offset = circumference - (score / 10) * circumference;

  const getColor = (s) => {
    if (s >= 8) return { stroke: '#39ff85', text: 'text-accent-green', glow: 'drop-shadow-[0_0_12px_rgba(57,255,133,0.4)]' };
    if (s >= 5) return { stroke: '#ffb300', text: 'text-accent-amber', glow: 'drop-shadow-[0_0_12px_rgba(255,179,0,0.4)]' };
    return { stroke: '#ff4d6a', text: 'text-accent-red', glow: 'drop-shadow-[0_0_12px_rgba(255,77,106,0.4)]' };
  };

  const color = getColor(score);

  return (
    <div className={`score-ring ${color.glow}`}>
      <svg width="100" height="100" viewBox="0 0 100 100">
        {/* Background ring */}
        <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="4" />
        {/* Score ring */}
        <circle
          cx="50" cy="50" r="42"
          fill="none"
          stroke={color.stroke}
          strokeWidth="4"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 1s ease-out' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`font-display font-bold text-2xl ${color.text}`}>{score}</span>
        <span className="font-mono text-[9px] text-txt-muted tracking-widest">/10</span>
      </div>
    </div>
  );
}

function SeverityIcon({ severity }) {
  switch (severity) {
    case 'critical':
      return <AlertTriangle size={14} className="text-accent-red" />;
    case 'warning':
      return <AlertCircle size={14} className="text-accent-amber" />;
    case 'info':
      return <Info size={14} className="text-accent-blue" />;
    default:
      return <Info size={14} className="text-txt-muted" />;
  }
}

function getSeverityBadge(severity) {
  switch (severity) {
    case 'critical': return 'badge-critical';
    case 'warning': return 'badge-warning';
    case 'info': return 'badge-info';
    default: return 'badge bg-surface-4 text-txt-muted';
  }
}

function getCategoryColor(category) {
  switch (category) {
    case 'bug': return 'text-accent-red';
    case 'security': return 'text-accent-amber';
    case 'performance': return 'text-accent-purple';
    case 'style': return 'text-accent-blue';
    default: return 'text-txt-secondary';
  }
}

/**
 * ReviewResults
 *
 * Props:
 *   result      — ReviewResult object from the API
 *   cached      — bool, shows "cached" badge when true
 *   reviewId    — int | null — if provided, shows "Mark as applied" buttons per issue
 *   feedbackMap — { [issueIndex]: boolean } — initial applied state (e.g. loaded from history)
 *   onFeedback  — (issueIndex, applied, category) => void — called when user toggles an issue
 */
export default function ReviewResults({ result, cached, reviewId = null, feedbackMap = {}, onFeedback }) {
  // Local optimistic state — initialized from feedbackMap prop
  const [applied, setApplied] = useState(() => {
    const m = {};
    Object.entries(feedbackMap).forEach(([k, v]) => { m[parseInt(k)] = v; });
    return m;
  });

  if (!result) return null;

  const criticalCount = result.issues?.filter((i) => i.severity === 'critical').length || 0;
  const warningCount = result.issues?.filter((i) => i.severity === 'warning').length || 0;
  const infoCount = result.issues?.filter((i) => i.severity === 'info').length || 0;
  const appliedCount = Object.values(applied).filter(Boolean).length;

  const handleToggle = (index, category) => {
    const next = !applied[index];
    setApplied((prev) => ({ ...prev, [index]: next }));
    onFeedback?.(index, next, category);
  };

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Score + Summary */}
      <div className="card">
        <div className="flex items-start gap-6">
          <ScoreRing score={result.score} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="font-display font-semibold text-sm text-txt-primary">Analysis Complete</h3>
              {cached && (
                <span className="badge bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/20">
                  cached
                </span>
              )}
            </div>
            <p className="text-sm text-txt-secondary leading-relaxed">{result.summary}</p>

            {/* Issue count pills */}
            <div className="flex gap-2 mt-3 flex-wrap">
              {criticalCount > 0 && (
                <span className="badge-critical">
                  <AlertTriangle size={10} />
                  {criticalCount} critical
                </span>
              )}
              {warningCount > 0 && (
                <span className="badge-warning">
                  <AlertCircle size={10} />
                  {warningCount} warning
                </span>
              )}
              {infoCount > 0 && (
                <span className="badge-info">
                  <Info size={10} />
                  {infoCount} info
                </span>
              )}
              {result.issues?.length === 0 && (
                <span className="badge-success">
                  <CheckCircle size={10} />
                  No issues found
                </span>
              )}
              {/* Feedback summary — only when review_id is present and at least one applied */}
              {reviewId && appliedCount > 0 && (
                <span className="badge bg-accent-green/10 text-accent-green border border-accent-green/20">
                  <CheckCircle2 size={10} />
                  {appliedCount} applied
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Issues list */}
      {result.issues && result.issues.length > 0 && (
        <div className="card p-0 overflow-hidden">
          <div className="px-5 py-3 border-b border-surface-5 flex items-center justify-between">
            <h3 className="font-display text-xs tracking-widest uppercase text-txt-muted">
              Issues ({result.issues.length})
            </h3>
            {reviewId && (
              <span className="font-mono text-[10px] text-txt-muted/50">
                Mark suggestions you applied →
              </span>
            )}
          </div>

          <div className="divide-y divide-surface-5">
            {result.issues.map((issue, index) => {
              const isApplied = !!applied[index];
              return (
                <div
                  key={index}
                  className={`px-5 py-4 transition-colors ${
                    isApplied ? 'bg-accent-green/5' : 'hover:bg-surface-3/30'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <SeverityIcon severity={issue.severity} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className={getSeverityBadge(issue.severity)}>
                          {issue.severity}
                        </span>
                        <span className={`font-mono text-[10px] tracking-wider uppercase ${getCategoryColor(issue.category)}`}>
                          {issue.category}
                        </span>
                        {issue.line && (
                          <span className="font-mono text-[10px] text-txt-muted">
                            L{issue.line}
                          </span>
                        )}
                        {issue.verified === false && (
                          <span className="font-mono text-[10px] text-accent-amber/70">
                            unverified line
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-txt-primary leading-relaxed">{issue.description}</p>
                      <p className="text-sm text-accent-green/80 mt-1.5 leading-relaxed">
                        → {issue.suggestion}
                      </p>
                    </div>

                    {/* Applied toggle — only shown when a reviewId is available */}
                    {reviewId && (
                      <button
                        onClick={() => handleToggle(index, issue.category)}
                        title={isApplied ? 'Mark as not applied' : 'Mark as applied'}
                        className={`shrink-0 p-1.5 rounded-md transition-all ${
                          isApplied
                            ? 'text-accent-green bg-accent-green/10'
                            : 'text-txt-muted/30 hover:text-accent-green/60 hover:bg-surface-3'
                        }`}
                      >
                        <CheckCircle2 size={16} />
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
