import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { logout, getAuthenticatedUser } from '../services/authService';
import { useAuth } from '../contexts/AuthContext';
import AuthCard from '../components/AuthCard';
import MusicbotLogo from '../components/MusicbotLogo';
import { Construction, Loader2 } from 'lucide-react';

const UnderConstruction = () => {
  const navigate = useNavigate();
  const { logout: ctxLogout } = useAuth();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const check = async () => {
      const user = await getAuthenticatedUser();
      if (!user) {
        navigate('/', { replace: true });
      } else {
        setChecking(false);
      }
    };
    check();
  }, [navigate]);

  const handleLogout = async () => {
    await logout();
    ctxLogout();
    navigate('/', { replace: true });
  };

  if (checking) {
    return (
      <AuthCard>
        <div className="flex flex-col items-center gap-4">
          <Loader2 size={32} className="animate-spin text-teal" />
        </div>
      </AuthCard>
    );
  }

  return (
    <AuthCard>
      <div className="flex flex-col items-center gap-6">
        <MusicbotLogo />
        <Construction size={48} className="text-gold" />
        <h2 className="font-display font-bold text-2xl text-off-white">Em Construção</h2>
        <p className="text-slate text-center text-sm">
          Estamos trabalhando no chat. Em breve estará disponível!
        </p>
        <button
          onClick={handleLogout}
          className="w-full py-3 px-4 rounded-xl border border-teal text-off-white font-body font-semibold text-base hover:bg-[hsla(170,71%,41%,0.1)] transition-all duration-200 hover:scale-[1.02]"
        >
          Sair
        </button>
      </div>
    </AuthCard>
  );
};

export default UnderConstruction;
