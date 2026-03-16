import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAuthenticatedUser } from '../services/authService';
import { useAuth } from '../contexts/AuthContext';
import AuthCard from '../components/AuthCard';
import MusicbotLogo from '../components/MusicbotLogo';
import { Loader2 } from 'lucide-react';

const AuthCallback = () => {
  const navigate = useNavigate();
  const { loginWithProfile } = useAuth();
  const [status, setStatus] = useState<'loading' | 'error'>('loading');

  useEffect(() => {
    const handleCallback = async () => {
      const flow = localStorage.getItem('auth_flow') || 'login';
      localStorage.removeItem('auth_flow');

      try {
        const profile = await getAuthenticatedUser();

        if (profile) {
          if (flow === 'register') {
            // Redirect to cadastro with profile loaded in context
            loginWithProfile(profile);
            navigate('/cadastro?step=confirm', { replace: true });
          } else {
            loginWithProfile(profile);
            navigate('/under-construction', { replace: true });
          }
        } else {
          setStatus('error');
          setTimeout(() => {
            navigate('/entrar?error=auth_failed', { replace: true });
          }, 2000);
        }
      } catch {
        setStatus('error');
        setTimeout(() => {
          navigate('/entrar?error=auth_failed', { replace: true });
        }, 2000);
      }
    };

    handleCallback();
  }, [navigate, loginWithProfile]);

  return (
    <AuthCard>
      <div className="flex flex-col items-center gap-6">
        <MusicbotLogo />
        {status === 'loading' ? (
          <>
            <Loader2 size={32} className="animate-spin text-teal" />
            <p className="text-slate text-sm text-center">Autenticando com Spotify...</p>
          </>
        ) : (
          <>
            <p className="text-magenta text-sm text-center">
              Falha na autenticação. Redirecionando...
            </p>
          </>
        )}
      </div>
    </AuthCard>
  );
};

export default AuthCallback;
