import { Link } from 'react-router-dom';
import { useAuth } from '../utils/AuthContext';
import {
  Terminal,
  Shield,
  Zap,
  BookOpen,
  GitBranch,
  Scan,
  ArrowRight,
  ChevronRight,
} from 'lucide-react';

const FEATURES = [
  {
    icon: Scan,
    title: 'Code Review',
    desc: 'Structured analysis of bugs, security vulnerabilities, performance issues, and style — with line-specific feedback and severity ratings.',
    accent: 'accent-cyan',
  },
  {
    icon: BookOpen,
    title: 'Code Explanation',
    desc: 'Plain English breakdowns of what your code does. Ideal for learning, onboarding, or understanding unfamiliar codebases.',
    accent: 'accent-purple',
  },
  {
    icon: GitBranch,
    title: 'Refactor Suggestions',
    desc: 'Improvement recommendations with before/after examples. Focused on readability, performance, and modern best practices.',
    accent: 'accent-green',
  },
];

const LANGUAGES = ['Python', 'JavaScript', 'TypeScript', 'Java', 'Go', 'C++', 'Rust', 'C', 'C#'];

const STATS = [
  { value: '9', label: 'Languages' },
  { value: '3', label: 'AI Modes' },
  { value: '<5s', label: 'Avg Response' },
  { value: '40%', label: 'Cost Saved via Cache' },
];

export default function Home() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="relative">
      {/* ── Hero ── */}
      <section className="relative overflow-hidden">
        {/* Grid background */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `
              linear-gradient(rgba(0,229,255,0.3) 1px, transparent 1px),
              linear-gradient(90deg, rgba(0,229,255,0.3) 1px, transparent 1px)
            `,
            backgroundSize: '60px 60px',
          }}
        />
        {/* Gradient orb */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-accent-cyan/[0.04] rounded-full blur-[120px]" />

        <div className="relative max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-20 text-center">
          {/* Terminal prompt intro */}
          <div className="inline-flex items-center gap-2 bg-surface-2 border border-surface-5 rounded-full px-4 py-1.5 mb-8">
            <span className="w-1.5 h-1.5 rounded-full bg-accent-green animate-pulse" />
            <span className="font-mono text-xs text-txt-muted tracking-wide">
              AI-powered code analysis
            </span>
          </div>

          <h1 className="font-display font-bold text-4xl sm:text-5xl lg:text-6xl text-txt-primary leading-[1.1] mb-6">
            Ship better code,
            <br />
            <span className="text-accent-cyan">faster.</span>
          </h1>

          <p className="text-lg text-txt-secondary max-w-2xl mx-auto mb-10 leading-relaxed">
            CodeLens uses GPT-4o to review your code for bugs, security flaws, and performance issues.
            Get structured feedback with line-specific suggestions in seconds.
          </p>

          {/* CTA */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            {isAuthenticated ? (
              <Link to="/analyze" className="btn-primary text-sm py-3 px-8">
                <Terminal size={16} />
                Start Analyzing
                <ArrowRight size={14} />
              </Link>
            ) : (
              <>
                <Link to="/register" className="btn-primary text-sm py-3 px-8">
                  Get Started
                  <ArrowRight size={14} />
                </Link>
                <Link to="/login" className="btn-secondary text-sm py-3 px-8">
                  Login
                </Link>
              </>
            )}
          </div>

          {/* Terminal preview */}
          <div className="mt-16 max-w-2xl mx-auto">
            <div className="card p-0 overflow-hidden text-left">
              <div className="flex items-center gap-1.5 px-4 py-2.5 border-b border-surface-5 bg-surface-1/50">
                <div className="w-2.5 h-2.5 rounded-full bg-accent-red/50" />
                <div className="w-2.5 h-2.5 rounded-full bg-accent-amber/50" />
                <div className="w-2.5 h-2.5 rounded-full bg-accent-green/50" />
                <span className="ml-3 font-mono text-[10px] text-txt-muted">codelens — analysis</span>
              </div>
              <div className="p-4 font-mono text-xs leading-relaxed">
                <div className="text-txt-muted">$ codelens review app.py</div>
                <div className="mt-2 text-txt-secondary">
                  <span className="text-accent-cyan">→</span> Analyzing 47 lines of Python...
                </div>
                <div className="mt-1 text-txt-secondary">
                  <span className="text-accent-green">✓</span> Score: <span className="text-accent-green font-semibold">8/10</span>
                </div>
                <div className="mt-1 text-txt-secondary">
                  <span className="text-accent-amber">⚠</span> <span className="text-accent-amber">1 warning</span> — unused import on L3
                </div>
                <div className="mt-1 text-txt-secondary">
                  <span className="text-accent-red">✕</span> <span className="text-accent-red">1 critical</span> — SQL injection risk on L22
                </div>
                <div className="mt-2 text-txt-muted">
                  <span className="animate-scan">█</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Stats bar ── */}
      <section className="border-y border-surface-5 bg-surface-1/30">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
            {STATS.map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="font-display font-bold text-2xl text-accent-cyan">{stat.value}</div>
                <div className="font-mono text-[10px] text-txt-muted tracking-widest uppercase mt-1">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center mb-12">
          <h2 className="font-display font-bold text-2xl text-txt-primary mb-3">
            Three modes of analysis
          </h2>
          <p className="text-sm text-txt-secondary max-w-lg mx-auto">
            Each powered by GPT-4o with structured output parsing and Redis-cached responses.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-5">
          {FEATURES.map((f) => (
            <div key={f.title} className="card-glow group">
              <div
                className={`inline-flex items-center justify-center w-10 h-10 rounded-lg
                  bg-${f.accent}/10 border border-${f.accent}/20 mb-4`}
              >
                <f.icon size={18} className={`text-${f.accent}`} />
              </div>
              <h3 className="font-display font-semibold text-sm text-txt-primary mb-2">{f.title}</h3>
              <p className="text-sm text-txt-secondary leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Languages ── */}
      <section className="border-t border-surface-5 bg-surface-1/20">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center">
          <h3 className="font-mono text-[10px] text-txt-muted tracking-[0.2em] uppercase mb-6">
            Supported Languages
          </h3>
          <div className="flex flex-wrap justify-center gap-2">
            {LANGUAGES.map((lang) => (
              <span
                key={lang}
                className="font-mono text-xs text-txt-secondary bg-surface-3 border border-surface-5
                  px-3.5 py-1.5 rounded-md hover:border-accent-cyan/30 hover:text-accent-cyan transition-colors"
              >
                {lang}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      {!isAuthenticated && (
        <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
          <h2 className="font-display font-bold text-2xl text-txt-primary mb-3">
            Ready to level up your code?
          </h2>
          <p className="text-sm text-txt-secondary mb-8">
            Free to use. No credit card required.
          </p>
          <Link to="/register" className="btn-primary py-3 px-8">
            Create Account
            <ChevronRight size={14} />
          </Link>
        </section>
      )}

      {/* ── Footer ── */}
      <footer className="border-t border-surface-5">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex items-center justify-between">
          <span className="font-mono text-[10px] text-txt-muted">
            codelens v1.0 — built with FastAPI + React + GPT-4o
          </span>
          <div className="flex items-center gap-1">
            <Shield size={12} className="text-txt-muted" />
            <span className="font-mono text-[10px] text-txt-muted">JWT + bcrypt auth</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
