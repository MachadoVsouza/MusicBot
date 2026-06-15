import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import MusicbotLogo from '@/components/MusicbotLogo';
import AuthCard from '@/components/AuthCard';
import { Loader2, AlertCircle, CheckCircle } from 'lucide-react';

const ResetSenha = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!password) {
      setError('Senha é obrigatória');
      return;
    }
    if (password.length < 6) {
      setError('Senha deve ter no mínimo 6 caracteres');
      return;
    }
    if (password !== confirmPassword) {
      setError('Senhas não conferem');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const res = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, password }),
      });

      const data = await res.json();

      if (res.ok && data.success) {
        setSuccess(true);
      } else {
        setError(data.message || data.error || 'Erro ao redefinir senha.');
      }
    } catch {
      setError('Erro de conexão com o servidor');
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <AuthCard>
        <div className="flex flex-col items-center gap-5">
          <MusicbotLogo />
          <AlertCircle size={48} className="text-[#E91429]" />
          <h2 className="font-display font-bold text-xl text-off-white">Link inválido</h2>
          <p className="text-gray-light text-center text-sm">
            O link de redefinição de senha é inválido. Solicite um novo link.
          </p>
          <button
            onClick={() => navigate('/recuperar-senha')}
            className="w-full py-3 px-4 rounded-xl bg-green text-off-white font-body font-semibold text-base hover:brightness-110 transition-all duration-200 hover:scale-[1.02]"
          >
            Solicitar novo link
          </button>
        </div>
      </AuthCard>
    );
  }

  return (
    <AuthCard>
      <div className="flex flex-col items-center gap-5">
        <MusicbotLogo />
        <h2 className="font-display font-bold text-xl text-off-white">Redefinir senha</h2>

        {success ? (
          <div className="flex flex-col items-center gap-4 py-2">
            <CheckCircle size={48} className="text-green-bright" />
            <p className="text-off-white text-center text-sm max-w-xs">
              Senha redefinida com sucesso!
            </p>
            <button
              onClick={() => navigate('/entrar')}
              className="w-full py-3 px-4 rounded-xl bg-green text-off-white font-body font-semibold text-base hover:brightness-110 transition-all duration-200 hover:scale-[1.02]"
            >
              Fazer login
            </button>
          </div>
        ) : (
          <>
            <p className="text-gray-light text-center text-sm">
              Digite sua nova senha.
            </p>

            {error && (
              <div className="w-full px-4 py-3 rounded-lg bg-[#E9142920] border border-[#E9142940] flex items-start gap-3">
                <AlertCircle size={18} className="text-red-400 flex-shrink-0 mt-0.5" />
                <p className="text-[#E91429] text-sm">{error}</p>
              </div>
            )}

            <form onSubmit={handleSubmit} className="w-full flex flex-col gap-4">
              <div className="space-y-2">
                <label htmlFor="password" className="block text-sm font-medium text-slate">Nova senha</label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); setError(''); }}
                  placeholder="Mínimo 6 caracteres"
                  className="w-full px-4 py-3 rounded-lg bg-[#282828] border border-[#3E3E3E] text-off-white placeholder:text-slate/50 focus:outline-none focus:border-[#1DB954] focus:ring-1 focus:ring-[#1DB954] transition-all"
                  disabled={loading}
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-slate">Confirmar senha</label>
                <input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => { setConfirmPassword(e.target.value); setError(''); }}
                  placeholder="Confirme sua nova senha"
                  className="w-full px-4 py-3 rounded-lg bg-[#282828] border border-[#3E3E3E] text-off-white placeholder:text-slate/50 focus:outline-none focus:border-[#1DB954] focus:ring-1 focus:ring-[#1DB954] transition-all"
                  disabled={loading}
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 px-4 rounded-xl bg-green text-off-white font-body font-semibold text-base hover:brightness-110 transition-all duration-200 hover:scale-[1.02] disabled:opacity-70 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 size={20} className="animate-spin" />
                    Redefinindo...
                  </>
                ) : (
                  'Redefinir senha'
                )}
              </button>
            </form>
          </>
        )}

        <button
          onClick={() => navigate('/entrar')}
          className="text-gray-light text-sm hover:text-green-bright transition-colors duration-200"
        >
          ← Voltar para o login
        </button>
      </div>
    </AuthCard>
  );
};

export default ResetSenha;