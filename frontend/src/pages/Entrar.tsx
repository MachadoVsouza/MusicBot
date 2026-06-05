import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { loginWithPassword, redirectToSpotifyAuth } from '@/services/authService';
import { useAuth } from '@/contexts/AuthContext';
import MusicbotLogo from '@/components/MusicbotLogo';
import AuthCard from '@/components/AuthCard';
import { Eye, EyeOff, Loader2, AlertCircle } from 'lucide-react';

const Entrar = () => {
  const navigate = useNavigate();
  const { loginWithProfile } = useAuth();
  const [searchParams] = useSearchParams();
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  useEffect(() => {
    const errorParam = searchParams.get('error');
    if (errorParam) {
      const errorMessages: Record<string, string> = {
        auth_failed: 'Falha na autenticação. Tente novamente.',
        profile_failed: 'Não foi possível obter seus dados do Spotify.',
        token_failed: 'Falha ao autenticar com Spotify.',
        state_invalido: 'Estado da sessão inválido. Tente novamente.',
      };
      setError(errorMessages[errorParam] || 'Erro na autenticação.');
    }
  }, [searchParams]);

  const handleLoginWithPassword = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email.trim() || !password.trim()) {
      setError('Email e senha são obrigatórios');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await loginWithPassword({ email, password });

      if (result.success && result.token) {
        localStorage.setItem('musicbot_jwt', result.token);

        const profileRes = await fetch('/api/spotify/profile', {
          credentials: 'include',
          headers: { Authorization: `Bearer ${result.token}` },
        });

        if (profileRes.ok) {
          const profileData = await profileRes.json();
          const profile = profileData.data;
          loginWithProfile({
            name: profile.display_name ?? profile.name ?? 'Usuário',
            email: profile.email ?? email,
            avatar: 'https://api.dicebear.com/7.x/initials/svg?seed=user',
            plan: profile.product ?? 'free',
            followers: profile.followers?.total ?? 0,
          }, result.token);
        }
        navigate('/chat', { replace: true });
      } else {
        setError(result.error || 'Erro ao fazer login');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro desconhecido';
      console.error('Login error:', errorMessage);
      setError('Erro de conexão com o servidor');
    } finally {
      setLoading(false);
    }
  };

  const handleSpotifyLogin = () => {
    setLoading(true);
    setError(null);
    localStorage.setItem('auth_flow', 'login');
    redirectToSpotifyAuth();
  };

  return (
    <AuthCard>
      <div className="flex flex-col items-center gap-5">
        <MusicbotLogo />
        <h2 className="font-display font-bold text-xl text-off-white">Entrar no Musicbot</h2>

        {error && (
          <div className="w-full px-4 py-3 rounded-lg bg-[#E9142920] border border-[#E9142940] flex items-start gap-3">
            <AlertCircle size={18} className="text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-[#E91429] text-sm">{error}</p>
          </div>
        )}

        <form onSubmit={handleLoginWithPassword} className="w-full flex flex-col gap-4">
          <div className="space-y-2">
            <label htmlFor="email" className="block text-sm font-medium text-slate">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => { setEmail(e.target.value); setError(null); }}
              placeholder="seu@email.com"
              className="w-full px-4 py-3 rounded-lg bg-[#282828] border border-[#3E3E3E] text-off-white placeholder:text-slate/50 focus:outline-none focus:border-[#1DB954] focus:ring-1 focus:ring-[#1DB954] transition-all"
              disabled={loading}
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="password" className="block text-sm font-medium text-slate">Senha</label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => { setPassword(e.target.value); setError(null); }}
                placeholder="Sua senha"
                className="w-full px-4 py-3 rounded-lg bg-[#282828] border border-[#3E3E3E] text-off-white placeholder:text-slate/50 focus:outline-none focus:border-[#1DB954] focus:ring-1 focus:ring-[#1DB954] transition-all pr-12"
                disabled={loading}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate hover:text-off-white transition-colors"
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 rounded-xl bg-green text-off-white font-body font-semibold text-base hover:brightness-110 transition-all duration-200 hover:scale-[1.02] flex items-center justify-center gap-2 disabled:opacity-70"
          >
            {loading ? (
              <>
                <Loader2 size={20} className="animate-spin" />
                Entrando...
              </>
            ) : (
              'Entrar com Email'
            )}
          </button>
        </form>

        <button
          onClick={() => navigate('/recuperar-senha')}
          className="text-slate text-sm hover:text-green-bright transition-colors duration-200"
        >
          Recuperar senha
        </button>

        <p className="text-slate text-sm">
          Não tem uma conta?{' '}
          <button onClick={() => navigate('/cadastro')} className="text-green-bright hover:underline">
            Criar conta
          </button>
        </p>
      </div>
    </AuthCard>
  );
};

export default Entrar;
