/**
 * LoginPage component
 * Login form matching seed credentials
 */
import { useState, FormEvent } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { TextInput, PasswordInput, Button, InlineNotification } from '@carbon/react';
import { useAuth } from '../../lib/auth-context';
import { ApiError } from '../../lib/api-client';

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await login({ email, password });
      const from = (location.state as { from?: string })?.from || '/dashboard';
      navigate(from, { replace: true });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Login failed. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ 
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: 'var(--cds-background)',
    }}>
      <div style={{ 
        width: '100%',
        maxWidth: '400px',
        padding: 'var(--cds-spacing-07)',
      }}>
        <h1 style={{ 
          marginBottom: 'var(--cds-spacing-06)',
          fontSize: '28px',
          fontWeight: 400,
        }}>
          AML Transaction Monitoring
        </h1>
        <p style={{ 
          marginBottom: 'var(--cds-spacing-07)',
          color: 'var(--cds-text-secondary)',
        }}>
          Sign in to your account
        </p>

        {error && (
          <InlineNotification
            kind="error"
            title="Login failed"
            subtitle={error}
            lowContrast
            hideCloseButton
            style={{ marginBottom: 'var(--cds-spacing-05)' }}
          />
        )}

        <form onSubmit={handleSubmit}>
          <TextInput
            id="email"
            labelText="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
            style={{ marginBottom: 'var(--cds-spacing-05)' }}
          />
          
          <PasswordInput
            id="password"
            labelText="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
            style={{ marginBottom: 'var(--cds-spacing-06)' }}
          />

          <Button
            type="submit"
            disabled={isLoading || !email || !password}
            style={{ width: '100%' }}
          >
            {isLoading ? 'Signing in...' : 'Sign in'}
          </Button>
        </form>

        <p style={{ 
          marginTop: 'var(--cds-spacing-06)',
          fontSize: '12px',
          color: 'var(--cds-text-secondary)',
        }}>
          Demo credentials: officer@example.com / Officer-pass-1
        </p>
      </div>
    </div>
  );
}
