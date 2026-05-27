import { useNavigate } from 'react-router-dom';
import MusicbotLogo from '@/components/MusicbotLogo';
import AuthCard from '@/components/AuthCard';

const Login = () => {
  const navigate = useNavigate();

  return (
    <AuthCard>
      <div className="flex flex-col items-center gap-6">
        <MusicbotLogo size="lg" />
        <p className="text-slate text-center text-sm">
          Descubra, explore e aprofunde seu universo musical.
        </p>
        <div className="w-full h-px bg-[hsla(0,0%,100%,0.1)]" />
        <button
          onClick={() => navigate('/cadastro')}
          className="w-full py-3 px-4 rounded-xl bg-green text-off-white font-body font-semibold tracking-wide text-base hover:brightness-110 transition-all duration-200 hover:scale-[1.02]"
        >
          Criar nova conta
        </button>
        <button
          onClick={() => navigate('/entrar')}
          className="w-full py-3 px-4 rounded-xl border border-green-bright text-off-white font-body font-semibold text-base hover:bg-[#1DB95420] transition-all duration-200 hover:scale-[1.02]"
        >
          Fazer login
        </button>
      </div>
    </AuthCard>
  );
};

export default Login;
