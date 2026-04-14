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

      if (result.success) {
        const profileRes = await fetch('/api/spotify/profile', {
          credentials: 'include',
        });

        if (profileRes.ok) {
          const profileData = await profileRes.json();
          const profile = profileData.data;
          loginWithProfile({
            name: profile.display_name ?? profile.name ?? 'Usuário',
            email: profile.email ?? email,
            avatar: profile.images?.[0]?.url ?? '',
            plan: profile.product ?? 'free',
            followers: profile.followers?.total ?? 0,
          });
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
          <div className="w-full px-4 py-3 rounded-lg bg-red-500/20 border border-red-500/50 flex items-start gap-3">
            <AlertCircle size={18} className="text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-red-300 text-sm">{error}</p>
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
              className="w-full px-4 py-3 rounded-lg bg-slate/10 border border-slate/30 text-off-white placeholder:text-slate/50 focus:outline-none focus:border-teal focus:ring-1 focus:ring-teal transition-all"
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
                className="w-full px-4 py-3 rounded-lg bg-slate/10 border border-slate/30 text-off-white placeholder:text-slate/50 focus:outline-none focus:border-teal focus:ring-1 focus:ring-teal transition-all pr-12"
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
            className="w-full py-3 px-4 rounded-xl bg-magenta text-off-white font-body font-semibold text-base hover:brightness-110 transition-all duration-200 hover:scale-[1.02] flex items-center justify-center gap-2 disabled:opacity-70"
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

        <div className="w-full h-px bg-slate/20" />

        <button
          onClick={handleSpotifyLogin}
          disabled={loading}
          className="w-full py-3 px-4 rounded-xl bg-teal text-off-white font-body font-semibold text-base hover:brightness-110 transition-all duration-200 hover:scale-[1.02] flex items-center justify-center gap-3 disabled:opacity-70"
        >
          {loading ? (
            <Loader2 size={20} className="animate-spin" />
          ) : (
            <>
              <div className="w-5 h-5 rounded-full bg-[#1DB954] flex items-center justify-center text-xs font-bold text-black">♪</div>
              Continuar com Spotify
            </>
          )}
        </button>

        <button
          onClick={() => navigate('/recuperar-senha')}
          className="text-slate text-sm hover:text-teal transition-colors duration-200"
        >
          Recuperar senha
        </button>

        <p className="text-slate text-sm">
          Não tem uma conta?{' '}
          <button onClick={() => navigate('/cadastro')} className="text-teal hover:underline">
            Criar conta
          </button>
        </p>

        {/* <div className="w-full h-px bg-[hsla(0,0%,100%,0.1)]" /> */}
        {/* <div className="w-full">
          <p className="text-slate text-xs mb-2 text-center font-mono-label">Demo: Entrar como</p>
          <div className="flex gap-2">
            <button
              onClick={() => setSelectedRole('user')}
              className={`flex-1 py-2 rounded-tag text-sm font-body transition-all duration-200 ${
                selectedRole === 'user'
                  ? 'bg-teal text-off-white'
                  : 'glass text-slate hover:text-off-white'
              }`}
            >
              Usuário Comum
            </button>
            <button
              onClick={() => setSelectedRole('moderator')}
              className={`flex-1 py-2 rounded-tag text-sm font-body transition-all duration-200 ${
                selectedRole === 'moderator'
                  ? 'bg-gold text-midnight'
                  : 'glass text-slate hover:text-off-white'
              }`}
            >
              Moderador
            </button>
          </div>
        </div> */}
      </div>
    </AuthCard>
  );
};

export default Entrar;
