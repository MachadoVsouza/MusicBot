import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import MusicbotLogo from '@/components/MusicbotLogo';
import AuthCard from '@/components/AuthCard';
import { CheckCircle } from 'lucide-react';

const RecuperarSenha = () => {
  const navigate = useNavigate();
  const [sent, setSent] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSent(true);
  };

  return (
    <AuthCard>
      <div className="flex flex-col items-center gap-5">
        <MusicbotLogo />
        <h2 className="font-display font-bold text-xl text-off-white">Recuperar senha</h2>

        {sent ? (
          <div className="flex flex-col items-center gap-3 py-4">
            <CheckCircle size={48} className="text-teal" />
            <p className="text-teal text-center font-body">
              E-mail enviado! Verifique sua caixa de entrada.
            </p>
          </div>
        ) : (
          <>
            <p className="text-slate text-center text-sm">
              Informe seu e-mail para receber as instruções.
            </p>
            <form onSubmit={handleSubmit} className="w-full flex flex-col gap-4">
              <input
                type="email"
                placeholder="E-mail"
                className="w-full px-4 py-3 rounded-xl glass text-off-white placeholder:text-slate text-sm font-body focus:outline-none focus:border-teal transition-colors"
              />
              <button
                type="submit"
                className="w-full py-3 px-4 rounded-xl bg-magenta text-off-white font-body font-semibold text-base hover:brightness-110 transition-all duration-200 hover:scale-[1.02]"
              >
                Enviar instruções
              </button>
            </form>
          </>
        )}

        <button
          onClick={() => navigate('/entrar')}
          className="text-slate text-sm hover:text-teal transition-colors duration-200"
        >
          ← Voltar para o login
        </button>
      </div>
    </AuthCard>
  );
};

export default RecuperarSenha;
