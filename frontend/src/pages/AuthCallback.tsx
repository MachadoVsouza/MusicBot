import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import AuthCard from '../components/AuthCard';
import MusicbotLogo from '../components/MusicbotLogo';
import { Loader2 } from 'lucide-react';

const AuthCallback = () => {
  const navigate = useNavigate();
  const { loginWithToken } = useAuth();
  const [status, setStatus] = useState<'loading' | 'error'>('loading');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const params = new URLSearchParams(window.location.search);
        const tokenFromUrl = params.get('token');
        const refreshFromUrl = params.get('refresh_token');

        if (tokenFromUrl) {
          window.history.replaceState({}, '', '/chat');
          const ok = await loginWithToken(tokenFromUrl, refreshFromUrl || undefined);
          if (ok) {
            navigate('/chat', { replace: true });
          } else {
            setStatus('error');
            setTimeout(() => navigate('/entrar?error=auth_failed', { replace: true }), 2000);
          }
          return;
        }

        // Sem token na URL — fluxo inválido
        setStatus('error');
        setTimeout(() => navigate('/entrar?error=auth_failed', { replace: true }), 2000);
      } catch {
        setStatus('error');
        setTimeout(() => navigate('/entrar?error=auth_failed', { replace: true }), 2000);
      }
    };

    handleCallback();
  }, [navigate, loginWithToken]);

  return (
    <AuthCard>
      <div className="flex flex-col items-center gap-6">
        <MusicbotLogo />
        {status === 'loading' ? (
          <>
            <Loader2 size={32} className="animate-spin text-green-bright" />
            <p className="text-slate text-sm text-center">Autenticando com Spotify...</p>
          </>
        ) : (
          <p className="text-[#E91429] text-sm text-center">
            Falha na autenticação. Redirecionando...
          </p>
        )}
      </div>
    </AuthCard>
  );
};

export default AuthCallback;
