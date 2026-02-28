import { useState } from 'react';
import { Play, Loader2 } from 'lucide-react';

// Must match backend regex: ^(python|javascript|typescript|java|go|cpp|rust|c|csharp)$
const LANGUAGES = [
  { value: 'python', label: 'Python' },
  { value: 'javascript', label: 'JavaScript' },
  { value: 'typescript', label: 'TypeScript' },
  { value: 'java', label: 'Java' },
  { value: 'go', label: 'Go' },
  { value: 'cpp', label: 'C++' },
  { value: 'rust', label: 'Rust' },
  { value: 'c', label: 'C' },
  { value: 'csharp', label: 'C#' },
];

export default function CodeEditor({ onSubmit, loading, actionLabel = 'Analyze' }) {
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (code.trim() && !loading) {
      onSubmit(code, language);
    }
  };

  const lineCount = code.split('\n').length;
  const charCount = code.length;

  return (
    <form onSubmit={handleSubmit} className="flex flex-col h-full">
      {/* Header bar */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-surface-5 bg-surface-1/50">
        <div className="flex items-center gap-3">
          {/* Fake traffic lights */}
          <div className="flex gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-accent-red/60" />
            <div className="w-2.5 h-2.5 rounded-full bg-accent-amber/60" />
            <div className="w-2.5 h-2.5 rounded-full bg-accent-green/60" />
          </div>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="bg-surface-3 border border-surface-5 text-txt-secondary font-mono text-xs
              px-2.5 py-1 rounded-md focus:outline-none focus:border-accent-cyan/40
              cursor-pointer appearance-none"
          >
            {LANGUAGES.map((lang) => (
              <option key={lang.value} value={lang.value}>
                {lang.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-4">
          <span className="font-mono text-[10px] text-txt-muted tracking-wide">
            {lineCount} lines · {charCount.toLocaleString()} / 10,000
          </span>
        </div>
      </div>

      {/* Editor area */}
      <div className="flex-1 relative">
        <textarea
          value={code}
          onChange={(e) => {
            if (e.target.value.length <= 10000) {
              setCode(e.target.value);
            }
          }}
          placeholder="// Paste your code here..."
          spellCheck={false}
          className="w-full h-full min-h-[320px] resize-none bg-transparent
            font-mono text-sm text-txt-primary leading-relaxed
            p-4 pl-6
            placeholder:text-txt-muted/30
            focus:outline-none"
        />

        {/* Char limit warning */}
        {charCount > 9000 && (
          <div className="absolute bottom-2 right-3 font-mono text-[10px] text-accent-amber animate-pulse">
            {(10000 - charCount).toLocaleString()} chars remaining
          </div>
        )}
      </div>

      {/* Footer / submit */}
      <div className="px-4 py-3 border-t border-surface-5 bg-surface-1/30">
        <button
          type="submit"
          disabled={loading || !code.trim()}
          className="btn-primary w-full"
        >
          {loading ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              Processing...
            </>
          ) : (
            <>
              <Play size={14} />
              {actionLabel}
            </>
          )}
        </button>
      </div>
    </form>
  );
}
