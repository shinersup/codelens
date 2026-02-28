import { useState, useEffect } from 'react';
import { history as historyApi } from '../utils/api';
import ReviewResults from '../components/ReviewResults';
import TextResults from '../components/TextResults';
import {
  Clock,
  Scan,
  BookOpen,
  GitBranch,
  Loader2,
  AlertCircle,
  Inbox,
  ChevronRight,
  ArrowLeft,
  Code2,
  Trash2,
} from 'lucide-react';

function getTypeIcon(type) {
  switch (type) {
    case 'review': return <Scan size={14} className="text-accent-cyan" />;
    case 'explain': return <BookOpen size={14} className="text-accent-purple" />;
    case 'refactor': return <GitBranch size={14} className="text-accent-green" />;
    default: return <Scan size={14} className="text-txt-muted" />;
  }
}

function getTypeLabel(type) {
  switch (type) {
    case 'review': return 'Review';
    case 'explain': return 'Explanation';
    case 'refactor': return 'Refactor';
    default: return type;
  }
}

function getTypeBadgeClass(type) {
  switch (type) {
    case 'review': return 'bg-accent-cyan/10 text-accent-cyan border-accent-cyan/20';
    case 'explain': return 'bg-accent-purple/10 text-accent-purple border-accent-purple/20';
    case 'refactor': return 'bg-accent-green/10 text-accent-green border-accent-green/20';
    default: return 'bg-surface-4 text-txt-muted border-surface-5';
  }
}

function getScoreColor(score) {
  if (score >= 8) return 'text-accent-green';
  if (score >= 5) return 'text-accent-amber';
  return 'text-accent-red';
}

function formatDate(isoString) {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now - date;
  const diffMin = Math.floor(diffMs / 60000);
  const diffHr = Math.floor(diffMs / 3600000);
  const diffDay = Math.floor(diffMs / 86400000);

  if (diffMin < 1) return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHr < 24) return `${diffHr}h ago`;
  if (diffDay < 7) return `${diffDay}d ago`;

  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

// ── Detail View ──
function HistoryDetailView({ detail, onBack, onDelete }) {
  const [confirmDelete, setConfirmDelete] = useState(false);

  const handleDelete = () => {
    if (confirmDelete) {
      onDelete(detail.id);
    } else {
      setConfirmDelete(true);
      setTimeout(() => setConfirmDelete(false), 3000);
    }
  };

  return (
    <div className="animate-fade-in">
      {/* Back button + header */}
      <div className="flex items-center justify-between mb-4">
        <button onClick={onBack} className="btn-ghost -ml-2">
          <ArrowLeft size={14} />
          Back to history
        </button>
        <button
          onClick={handleDelete}
          className={`btn-ghost text-xs ${
            confirmDelete
              ? 'text-accent-red bg-accent-red/5 border border-accent-red/20'
              : 'text-txt-muted hover:text-accent-red'
          }`}
        >
          <Trash2 size={13} />
          {confirmDelete ? 'Click again to confirm' : 'Delete'}
        </button>
      </div>

      <div className="flex items-center gap-3 mb-5">
        {getTypeIcon(detail.review_type)}
        <div>
          <div className="flex items-center gap-2">
            <span className={`badge border text-[10px] ${getTypeBadgeClass(detail.review_type)}`}>
              {getTypeLabel(detail.review_type)}
            </span>
            <span className="font-mono text-xs text-txt-secondary">{detail.language}</span>
            <span className="font-mono text-[10px] text-txt-muted">
              {formatDate(detail.created_at)}
            </span>
          </div>
        </div>
      </div>

      {/* Original code */}
      <div className="card p-0 overflow-hidden mb-5">
        <div className="flex items-center gap-2 px-4 py-2.5 border-b border-surface-5 bg-surface-1/50">
          <Code2 size={13} className="text-txt-muted" />
          <span className="font-mono text-[10px] text-txt-muted tracking-wide">
            Submitted code · {detail.language}
          </span>
        </div>
        <pre className="p-4 overflow-x-auto">
          <code className="font-mono text-xs text-txt-secondary leading-relaxed">
            {detail.code}
          </code>
        </pre>
      </div>

      {/* Results */}
      {detail.review_type === 'review' && detail.result && (
        <ReviewResults result={detail.result} cached={false} />
      )}

      {detail.review_type === 'explain' && detail.result?.explanation && (
        <TextResults content={detail.result.explanation} type="explain" cached={false} />
      )}

      {detail.review_type === 'refactor' && detail.result?.suggestions && (
        <TextResults content={detail.result.suggestions} type="refactor" cached={false} />
      )}
    </div>
  );
}

// ── Main History Page ──
export default function History() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [confirmClear, setConfirmClear] = useState(false);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const response = await historyApi.getAll();
      setItems(response.data);
    } catch (err) {
      setError('Failed to load history.');
    } finally {
      setLoading(false);
    }
  };

  const loadDetail = async (id) => {
    setDetailLoading(true);
    setError('');
    try {
      const response = await historyApi.getById(id);
      setDetail(response.data);
    } catch (err) {
      setError('Failed to load review details.');
    } finally {
      setDetailLoading(false);
    }
  };

  const handleDeleteOne = async (id) => {
    try {
      await historyApi.delete(id);
      setItems(items.filter((item) => item.id !== id));
      setDetail(null);
    } catch (err) {
      setError('Failed to delete review.');
    }
  };

  const handleClearAll = async () => {
    if (confirmClear) {
      try {
        await historyApi.clearAll();
        setItems([]);
        setConfirmClear(false);
      } catch (err) {
        setError('Failed to clear history.');
      }
    } else {
      setConfirmClear(true);
      setTimeout(() => setConfirmClear(false), 3000);
    }
  };

  const handleBack = () => {
    setDetail(null);
  };

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Show detail view if selected */}
      {detail && !detailLoading && (
        <HistoryDetailView
          detail={detail}
          onBack={handleBack}
          onDelete={handleDeleteOne}
        />
      )}

      {detailLoading && (
        <div className="card flex items-center justify-center py-20">
          <Loader2 size={24} className="text-accent-cyan animate-spin" />
        </div>
      )}

      {/* Show list if no detail selected */}
      {!detail && !detailLoading && (
        <>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="font-display font-bold text-xl text-txt-primary">Review History</h1>
              <p className="text-sm text-txt-muted mt-1">
                Your last 50 code analyses, most recent first.
              </p>
            </div>
            {items.length > 0 && (
              <button
                onClick={handleClearAll}
                className={`btn-ghost text-xs ${
                  confirmClear
                    ? 'text-accent-red bg-accent-red/5 border border-accent-red/20'
                    : 'text-txt-muted hover:text-accent-red'
                }`}
              >
                <Trash2 size={13} />
                {confirmClear ? 'Click again to confirm' : 'Clear All'}
              </button>
            )}
          </div>

          {loading && (
            <div className="card flex items-center justify-center py-20">
              <Loader2 size={24} className="text-accent-cyan animate-spin" />
            </div>
          )}

          {error && (
            <div className="flex items-center gap-2 bg-accent-red/5 border border-accent-red/20 text-accent-red text-sm px-4 py-3 rounded-lg mb-4">
              <AlertCircle size={14} />
              {error}
            </div>
          )}

          {!loading && !error && items.length === 0 && (
            <div className="card flex flex-col items-center justify-center py-20 text-center">
              <Inbox size={28} className="text-txt-muted/30 mb-3" />
              <p className="text-sm text-txt-muted">No reviews yet</p>
              <p className="font-mono text-[10px] text-txt-muted/60 mt-1">
                Your analysis history will appear here
              </p>
            </div>
          )}

          {!loading && items.length > 0 && (
            <div className="card p-0 overflow-hidden">
              <div className="divide-y divide-surface-5">
                {items.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => loadDetail(item.id)}
                    className="w-full flex items-center gap-4 px-5 py-3.5 hover:bg-surface-3/30 transition-colors text-left"
                  >
                    {/* Type icon */}
                    <div className="shrink-0">{getTypeIcon(item.review_type)}</div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={`badge border text-[10px] ${getTypeBadgeClass(item.review_type)}`}>
                          {getTypeLabel(item.review_type)}
                        </span>
                        <span className="font-mono text-xs text-txt-secondary">
                          {item.language}
                        </span>
                      </div>
                    </div>

                    {/* Score (review only) */}
                    <div className="shrink-0 w-12 text-right">
                      {item.score != null ? (
                        <span className={`font-display font-bold text-sm ${getScoreColor(item.score)}`}>
                          {item.score}/10
                        </span>
                      ) : (
                        <span className="text-txt-muted/30">—</span>
                      )}
                    </div>

                    {/* Time */}
                    <div className="shrink-0 flex items-center gap-1.5 text-txt-muted">
                      <Clock size={11} />
                      <span className="font-mono text-[10px]">{formatDate(item.created_at)}</span>
                    </div>

                    {/* Arrow */}
                    <ChevronRight size={14} className="shrink-0 text-txt-muted/30" />
                  </button>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}