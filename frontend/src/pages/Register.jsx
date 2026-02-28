import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../utils/AuthContext';
import { UserPlus, Loader2, AlertCircle, CheckCircle } from 'lucide-react';

export default function Register() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await register(username, email, password);
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const passwordStrength = password.length >= 12 ? 'strong' : password.length >= 8 ? 'ok' : 'weak';

  return (
    <div className="min-h-[calc(100vh-3.5rem)] flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <h1 className="font-display font-bold text-2xl text-txt-primary">Create account</h1>
          <p className="font-mono text-xs text-txt-muted mt-2">Start reviewing code for free</p>
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
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="input"
                placeholder="devuser"
                required
                autoFocus
              />
            </div>

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
                minLength={8}
              />
              {password.length > 0 && (
                <div className="flex items-center gap-2 mt-2">
                  <div className="flex gap-1 flex-1">
                    <div
                      className={`h-0.5 rounded-full flex-1 transition-colors ${
                        password.length >= 1 ? (passwordStrength === 'weak' ? 'bg-accent-red' : passwordStrength === 'ok' ? 'bg-accent-amber' : 'bg-accent-green') : 'bg-surface-5'
                      }`}
                    />
                    <div
                      className={`h-0.5 rounded-full flex-1 transition-colors ${
                        password.length >= 8 ? (passwordStrength === 'ok' ? 'bg-accent-amber' : 'bg-accent-green') : 'bg-surface-5'
                      }`}
                    />
                    <div
                      className={`h-0.5 rounded-full flex-1 transition-colors ${
                        password.length >= 12 ? 'bg-accent-green' : 'bg-surface-5'
                      }`}
                    />
                  </div>
                  <span className="font-mono text-[10px] text-txt-muted">
                    {passwordStrength === 'weak' ? 'min 8 chars' : passwordStrength === 'ok' ? 'good' : 'strong'}
                  </span>
                </div>
              )}
            </div>

            <button type="submit" disabled={loading || password.length < 8} className="btn-primary w-full mt-2">
              {loading ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  Creating account...
                </>
              ) : (
                <>
                  <UserPlus size={14} />
                  Create Account
                </>
              )}
            </button>
          </form>

          <div className="mt-5 pt-5 border-t border-surface-5 text-center">
            <p className="text-sm text-txt-muted">
              Already have an account?{' '}
              <Link to="/login" className="text-accent-cyan hover:underline">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
