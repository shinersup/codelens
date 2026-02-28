import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../utils/AuthContext';
import { LogIn, Loader2, AlertCircle } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
      navigate('/analyze');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-3.5rem)] flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <h1 className="font-display font-bold text-2xl text-txt-primary">Welcome back</h1>
          <p className="font-mono text-xs text-txt-muted mt-2">Sign in to continue</p>
        </div>

        <div className="card">
          {error && (
            <div className="flex items-center gap-2 bg-accent-red/5 border border-accent-red/20 text-accent-red text-sm px-4 py-3 rounded-lg mb-5">
              <AlertCircle size={14} className="shrink-0" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block font-mono text-[10px] tracking-widest uppercase text-txt-muted mb-2">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input"
                placeholder="you@example.com"
                required
                autoFocus
                autoComplete="email"
              />
            </div>

            <div>
              <label className="block font-mono text-[10px] tracking-widest uppercase text-txt-muted mb-2">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input"
                placeholder="••••••••"
                required
                autoComplete="current-password"
              />
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full mt-2">
              {loading ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  Signing in...
                </>
              ) : (
                <>
                  <LogIn size={14} />
                  Sign In
                </>
              )}
            </button>
          </form>

          <div className="mt-5 pt-5 border-t border-surface-5 text-center">
            <p className="text-sm text-txt-muted">
              No account?{' '}
              <Link to="/register" className="text-accent-cyan hover:underline">
                Create one
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
