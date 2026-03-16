import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { redirectToSpotifyAuth, logout as authLogout } from '@/services/authService';
import MusicbotLogo from '@/components/MusicbotLogo';
import AuthCard from '@/components/AuthCard';
import { Loader2 } from 'lucide-react';

const Cadastro = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user, logout: ctxLogout } = useAuth();
  const [loading, setLoading] = useState(false);

  const step = searchParams.get('step') === 'confirm' && user ? 'confirm' : 'connect';

  const handleSpotifyAuth = () => {
    setLoading(true);
    localStorage.setItem('auth_flow', 'register');
    redirectToSpotifyAuth();
  };

  const handleUseAnotherAccount = async () => {
    await authLogout();
    ctxLogout();
    navigate('/cadastro', { replace: true });
  };

  return (
    <AuthCard>
      <div className="flex flex-col items-center gap-6">
        <MusicbotLogo />
        <h2 className="font-display font-bold text-xl text-off-white">Criar conta</h2>
        <p className="text-slate text-center text-sm">
          Sua conta é vinculada ao Spotify. Nenhuma senha extra necessária.
        </p>

        {step === 'connect' ? (
          <>
            <button
              onClick={handleSpotifyAuth}
              disabled={loading}
              className="w-full py-3 px-4 rounded-xl bg-magenta text-off-white font-body font-semibold text-base hover:brightness-110 transition-all duration-200 hover:scale-[1.02] flex items-center justify-center gap-3 disabled:opacity-70"
            >
              {loading ? (
                <Loader2 size={20} className="animate-spin" />
              ) : (
                <>
                  <div className="w-6 h-6 rounded-full bg-[#1DB954] flex items-center justify-center text-xs font-bold">♪</div>
                  Continuar com Spotify
                </>
              )}
            </button>

            {/* <div className="w-full glass rounded-xl p-4 opacity-60">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 rounded-full bg-[hsla(0,0%,100%,0.1)]" />
                <div>
                  <p className="text-off-white text-sm">João Silva</p>
                  <p className="text-slate text-xs">joao@email.com</p>
                </div>
              </div>
              <p className="text-slate text-xs font-mono-label">Dados importados do Spotify</p>
            </div> */}
          </>
        ) : (
          <>
            <div className="w-full glass rounded-xl p-4">
              <div className="flex items-center gap-3 mb-3">
                {user?.avatar ? (
                  <img src={user.avatar} alt="Avatar" className="w-12 h-12 rounded-full object-cover border border-teal" />
                ) : (
                  <div className="w-12 h-12 rounded-full bg-[hsla(0,0%,100%,0.1)]" />
                )}
                <div>
                  <p className="text-off-white text-sm font-semibold">{user?.name}</p>
                  <p className="text-slate text-xs">{user?.email}</p>
                </div>
              </div>
              {user?.plan && (
                <p className="text-slate text-xs font-mono-label">
                  Plano Spotify: <span className="text-teal">{user.plan}</span>
                </p>
              )}
            </div>

            <button
              onClick={() => navigate('/under-construction', { replace: true })}
              className="w-full py-3 px-4 rounded-xl bg-magenta text-off-white font-body font-semibold text-base hover:brightness-110 transition-all duration-200 hover:scale-[1.02]"
            >
              Entrar
            </button>

            <button
              onClick={handleUseAnotherAccount}
              className="text-slate text-sm hover:text-teal transition-colors duration-200"
            >
              Não é você? Usar outra conta
            </button>
          </>
        )}

        <button
          onClick={() => navigate('/login')}
          className="text-slate text-sm hover:text-teal transition-colors duration-200"
        >
          ← Voltar
        </button>
      </div>
    </AuthCard>
  );
};

export default Cadastro;
