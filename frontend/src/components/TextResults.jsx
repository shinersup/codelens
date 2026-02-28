import { BookOpen, GitBranch, Zap } from 'lucide-react';

export default function TextResults({ content, type, cached }) {
  if (!content) return null;

  const getIcon = () => {
    switch (type) {
      case 'explain':
        return <BookOpen size={14} className="text-accent-purple" />;
      case 'refactor':
        return <GitBranch size={14} className="text-accent-green" />;
      default:
        return <Zap size={14} className="text-accent-cyan" />;
    }
  };

  const getTitle = () => {
    switch (type) {
      case 'explain': return 'Explanation';
      case 'refactor': return 'Refactor Suggestions';
      default: return 'Result';
    }
  };

  const getAccent = () => {
    switch (type) {
      case 'explain': return 'border-accent-purple/20';
      case 'refactor': return 'border-accent-green/20';
      default: return 'border-accent-cyan/20';
    }
  };

  // Simple markdown-ish rendering for LLM responses
  const renderContent = (text) => {
    const lines = text.split('\n');
    const elements = [];
    let inCodeBlock = false;
    let codeLines = [];
    let codeLang = '';

    lines.forEach((line, i) => {
      // Code block start/end
      if (line.startsWith('```')) {
        if (inCodeBlock) {
          elements.push(
            <pre
              key={`code-${i}`}
              className="bg-surface-0 border border-surface-5 rounded-lg p-4 my-3 overflow-x-auto"
            >
              <code className="font-mono text-xs text-accent-cyan/90 leading-relaxed">
                {codeLines.join('\n')}
              </code>
            </pre>
          );
          codeLines = [];
          inCodeBlock = false;
        } else {
          codeLang = line.replace('```', '').trim();
          inCodeBlock = true;
        }
        return;
      }

      if (inCodeBlock) {
        codeLines.push(line);
        return;
      }

      // Headings
      if (line.startsWith('### ')) {
        elements.push(
          <h4 key={i} className="font-display text-sm font-semibold text-txt-primary mt-4 mb-1.5">
            {line.replace('### ', '')}
          </h4>
        );
        return;
      }
      if (line.startsWith('## ')) {
        elements.push(
          <h3 key={i} className="font-display text-sm font-bold text-txt-primary mt-5 mb-2">
            {line.replace('## ', '')}
          </h3>
        );
        return;
      }
      if (line.startsWith('# ')) {
        elements.push(
          <h2 key={i} className="font-display text-base font-bold text-txt-primary mt-5 mb-2">
            {line.replace('# ', '')}
          </h2>
        );
        return;
      }

      // List items
      if (line.match(/^[\-\*]\s/)) {
        elements.push(
          <div key={i} className="flex items-start gap-2 my-0.5">
            <span className="text-accent-cyan mt-1.5 text-xs">›</span>
            <span className="text-sm text-txt-secondary leading-relaxed">
              {renderInlineFormatting(line.replace(/^[\-\*]\s/, ''))}
            </span>
          </div>
        );
        return;
      }

      // Numbered list
      if (line.match(/^\d+\.\s/)) {
        const num = line.match(/^(\d+)\./)[1];
        elements.push(
          <div key={i} className="flex items-start gap-2.5 my-0.5">
            <span className="font-mono text-[10px] text-accent-cyan/60 mt-1.5 min-w-[1rem] text-right">
              {num}.
            </span>
            <span className="text-sm text-txt-secondary leading-relaxed">
              {renderInlineFormatting(line.replace(/^\d+\.\s/, ''))}
            </span>
          </div>
        );
        return;
      }

      // Empty line
      if (!line.trim()) {
        elements.push(<div key={i} className="h-2" />);
        return;
      }

      // Normal paragraph
      elements.push(
        <p key={i} className="text-sm text-txt-secondary leading-relaxed my-1">
          {renderInlineFormatting(line)}
        </p>
      );
    });

    return elements;
  };

  // Handle inline code and bold
  const renderInlineFormatting = (text) => {
    // Split by inline code backticks
    const parts = text.split(/(`[^`]+`)/g);
    return parts.map((part, i) => {
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code
            key={i}
            className="bg-surface-4 text-accent-cyan/90 font-mono text-xs px-1.5 py-0.5 rounded"
          >
            {part.slice(1, -1)}
          </code>
        );
      }
      // Handle bold
      const boldParts = part.split(/(\*\*[^*]+\*\*)/g);
      return boldParts.map((bp, j) => {
        if (bp.startsWith('**') && bp.endsWith('**')) {
          return (
            <strong key={`${i}-${j}`} className="text-txt-primary font-semibold">
              {bp.slice(2, -2)}
            </strong>
          );
        }
        return bp;
      });
    });
  };

  return (
    <div className="animate-fade-in">
      <div className={`card border-l-2 ${getAccent()}`}>
        <div className="flex items-center gap-2 mb-4">
          {getIcon()}
          <h3 className="font-display text-xs tracking-widest uppercase text-txt-muted">
            {getTitle()}
          </h3>
          {cached && (
            <span className="badge bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/20 ml-auto">
              cached
            </span>
          )}
        </div>
        <div className="prose-dark">{renderContent(content)}</div>
      </div>
    </div>
  );
}
