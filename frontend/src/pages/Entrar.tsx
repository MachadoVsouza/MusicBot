import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { redirectToSpotifyAuth } from '@/services/authService';
import MusicbotLogo from '@/components/MusicbotLogo';
import AuthCard from '@/components/AuthCard';
import { Eye, EyeOff, Loader2 } from 'lucide-react';

const Entrar = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const errorParam = searchParams.get('error');
    if (errorParam === 'auth_failed') {
      setError('Não foi possível autenticar. Verifique seu usuário e senha do Spotify.');
    }
  }, [searchParams]);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
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
          <div className="w-full px-4 py-3 rounded-xl bg-[hsla(340,80%,55%,0.15)] border border-magenta/30 text-magenta text-sm text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="w-full flex flex-col gap-4">
          <input
            type="text"
            placeholder="Seu nome do Spotify"
            className="w-full px-4 py-3 rounded-xl glass text-off-white placeholder:text-slate text-sm font-body focus:outline-none focus:border-teal transition-colors"
          />
          <div className="relative">
            <input
              type={showPassword ? 'text' : 'password'}
              placeholder="Senha"
              className="w-full px-4 py-3 rounded-xl glass text-off-white placeholder:text-slate text-sm font-body focus:outline-none focus:border-teal transition-colors pr-12"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate hover:text-off-white transition-colors"
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 rounded-xl bg-magenta text-off-white font-body font-semibold text-base hover:brightness-110 transition-all duration-200 hover:scale-[1.02] flex items-center justify-center gap-2 disabled:opacity-70"
          >
            {loading ? <Loader2 size={20} className="animate-spin" /> : 'Entrar'}
          </button>
        </form>

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
