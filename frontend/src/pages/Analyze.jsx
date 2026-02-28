import { useState } from 'react';
import { Scan, BookOpen, GitBranch, Loader2 } from 'lucide-react';
import { codeAnalysis } from '../utils/api';
import CodeEditor from '../components/CodeEditor';
import ReviewResults from '../components/ReviewResults';
import TextResults from '../components/TextResults';

const MODES = [
  { id: 'review', label: 'Review', icon: Scan, desc: 'Bugs, security, performance' },
  { id: 'explain', label: 'Explain', icon: BookOpen, desc: 'Plain English breakdown' },
  { id: 'refactor', label: 'Refactor', icon: GitBranch, desc: 'Before/after improvements' },
];

export default function Analyze() {
  const [mode, setMode] = useState('review');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [resultType, setResultType] = useState(null);
  const [cached, setCached] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (code, language) => {
    setLoading(true);
    setError('');
    setResult(null);

    try {
      let response;
      switch (mode) {
        case 'review':
          response = await codeAnalysis.review(code, language);
          setResult(response.data.review);
          setResultType('review');
          setCached(response.data.cached);
          break;
        case 'explain':
          response = await codeAnalysis.explain(code, language);
          setResult(response.data.explanation);
          setResultType('explain');
          setCached(response.data.cached);
          break;
        case 'refactor':
          response = await codeAnalysis.refactor(code, language);
          setResult(response.data.suggestions);
          setResultType('refactor');
          setCached(response.data.cached);
          break;
      }
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (err.response?.status === 429) {
        setError(detail || 'Rate limit exceeded. Please wait before trying again.');
      } else {
        setError(detail || 'Analysis failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const getModeAccent = () => {
    switch (mode) {
      case 'review': return 'accent-cyan';
      case 'explain': return 'accent-purple';
      case 'refactor': return 'accent-green';
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Page header */}
      <div className="mb-6">
        <h1 className="font-display font-bold text-xl text-txt-primary">Analyze Code</h1>
        <p className="text-sm text-txt-muted mt-1">
          Select a mode, paste your code, and let GPT-4o do the rest.
        </p>
      </div>

      {/* Mode selector */}
      <div className="flex gap-2 mb-6">
        {MODES.map((m) => {
          const isActive = mode === m.id;
          const accent =
            m.id === 'review' ? 'accent-cyan' :
            m.id === 'explain' ? 'accent-purple' :
            'accent-green';

          return (
            <button
              key={m.id}
              onClick={() => { setMode(m.id); setResult(null); setError(''); }}
              className={`
                flex items-center gap-2 px-4 py-2.5 rounded-lg font-mono text-xs tracking-wide
                border transition-all duration-200
                ${isActive
                  ? `bg-${accent}/10 border-${accent}/30 text-${accent}`
                  : 'bg-surface-2 border-surface-5 text-txt-muted hover:text-txt-secondary hover:border-surface-5'}
              `}
            >
              <m.icon size={14} />
              <span>{m.label}</span>
              <span className="hidden sm:inline text-txt-muted/60">— {m.desc}</span>
            </button>
          );
        })}
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 bg-accent-red/5 border border-accent-red/20 text-accent-red text-sm px-4 py-3 rounded-lg mb-5">
          {error}
        </div>
      )}

      {/* Two-column layout */}
      <div className="grid lg:grid-cols-2 gap-5 items-start">
        {/* Left: Editor */}
        <div className="card p-0 overflow-hidden">
          <CodeEditor
            onSubmit={handleSubmit}
            loading={loading}
            actionLabel={
              mode === 'review' ? 'Run Review' :
              mode === 'explain' ? 'Explain Code' :
              'Get Suggestions'
            }
          />
        </div>

        {/* Right: Results */}
        <div className="min-h-[400px]">
          {loading && (
            <div className="card flex flex-col items-center justify-center py-20">
              <Loader2 size={28} className={`text-${getModeAccent()} animate-spin mb-4`} />
              <p className="font-mono text-xs text-txt-muted tracking-wide">
                {mode === 'review' && 'Scanning for issues...'}
                {mode === 'explain' && 'Generating explanation...'}
                {mode === 'refactor' && 'Finding improvements...'}
              </p>
            </div>
          )}

          {!loading && result && resultType === 'review' && (
            <ReviewResults result={result} cached={cached} />
          )}

          {!loading && result && (resultType === 'explain' || resultType === 'refactor') && (
            <TextResults content={result} type={resultType} cached={cached} />
          )}

          {!loading && !result && !error && (
            <div className="card flex flex-col items-center justify-center py-20 text-center">
              <div className="w-12 h-12 rounded-xl bg-surface-3 border border-surface-5 flex items-center justify-center mb-4">
                {mode === 'review' && <Scan size={20} className="text-accent-cyan/40" />}
                {mode === 'explain' && <BookOpen size={20} className="text-accent-purple/40" />}
                {mode === 'refactor' && <GitBranch size={20} className="text-accent-green/40" />}
              </div>
              <p className="text-sm text-txt-muted">
                Results will appear here
              </p>
              <p className="font-mono text-[10px] text-txt-muted/60 mt-1">
                Paste code on the left and hit analyze
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
