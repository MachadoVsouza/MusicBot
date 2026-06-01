import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { registerUser } from '@/services/authService';
import { useAuth, authFetch } from '@/contexts/AuthContext';
import AuthCard from '@/components/AuthCard';
import MusicbotLogo from '@/components/MusicbotLogo';
import { Loader2, AlertCircle } from 'lucide-react';

const RegistrationForm = () => {
  const navigate = useNavigate();
  const { loginWithProfile, loginWithToken } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
    setError('');
  };

  const validateForm = (): boolean => {
    if (!formData.email.trim()) {
      setError('Email é obrigatório');
      return false;
    }
    if (!formData.email.includes('@')) {
      setError('Email inválido');
      return false;
    }
    if (!formData.password) {
      setError('Senha é obrigatória');
      return false;
    }
    if (formData.password.length < 6) {
      setError('Senha deve ter no mínimo 6 caracteres');
      return false;
    }
    if (formData.password !== formData.confirmPassword) {
      setError('Senhas não conferem');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    setLoading(true);
    try {
      const result = await registerUser({
        email: formData.email,
        password: formData.password,
      });

      if (result.success) {
        if (result.token) {
          await loginWithToken(result.token);
        }
        try {
          const profileRes = await authFetch('/api/spotify/profile');

          if (profileRes.ok) {
            const profileData = await profileRes.json();
            const profile = profileData.data;
            loginWithProfile({
              name: profile.display_name ?? profile.name ?? 'Usuário',
              email: profile.email ?? formData.email,
              avatar: profile.images?.[0]?.url ?? '',
              plan: profile.product ?? 'free',
              followers: profile.followers?.total ?? 0,
            }, result.token!);
          }
        } catch (profileError) {
          console.error('Erro ao buscar perfil:', profileError);
          // Continua mesmo se falhar ao buscar o perfil
          loginWithProfile({
            name: 'Usuário',
            email: formData.email,
            avatar: '',
            plan: 'free',
            followers: 0,
          }, result.token!);
        }
        navigate('/chat', { replace: true });
      } else {
        setError(result.error || 'Erro ao criar conta');
      }
    } catch (err) {
      console.error('Erro ao registrar:', err);
      setError('Erro de conexão com o servidor');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthCard>
      <div className="flex flex-col items-center gap-6">
        <MusicbotLogo size="lg" />
        <h2 className="font-display font-bold text-xl text-off-white">Complete seu cadastro</h2>
        <p className="text-gray-light text-center text-sm">
          Sua conta está conectada ao Spotify. Agora preencha seus dados para criar sua senha.
        </p>

        <form onSubmit={handleSubmit} className="w-full space-y-4">
          {/* Erro Alert */}
          {error && (
            <div className="p-3 rounded-lg bg-[#E9142920] border border-[#E9142940] flex items-start gap-3">
              <AlertCircle size={20} className="text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-[#FF4444] text-sm">{error}</p>
            </div>
          )}

          {/* Email */}
          <div className="space-y-2">
            <label htmlFor="email" className="block text-sm font-medium text-gray-light">Email</label>
            <input
              id="email"
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="seu@email.com"
              className="w-full px-4 py-2 rounded-lg bg-[#282828] border border-[#3E3E3E] text-off-white placeholder:text-gray-light/50 focus:outline-none focus:border-[#1DB954] focus:ring-1 focus:ring-[#1DB954] transition-all"
              disabled={loading}
            />
          </div>

          {/* Senha */}
          <div className="space-y-2">
            <label htmlFor="password" className="block text-sm font-medium text-gray-light">Senha</label>
            <input
              id="password"
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Mínimo 6 caracteres"
              className="w-full px-4 py-2 rounded-lg bg-[#282828] border border-[#3E3E3E] text-off-white placeholder:text-gray-light/50 focus:outline-none focus:border-[#1DB954] focus:ring-1 focus:ring-[#1DB954] transition-all"
              disabled={loading}
            />
          </div>

          {/* Confirmar Senha */}
          <div className="space-y-2">
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-light">Confirmar senha</label>
            <input
              id="confirmPassword"
              type="password"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              placeholder="Confirme sua senha"
              className="w-full px-4 py-2 rounded-lg bg-[#282828] border border-[#3E3E3E] text-off-white placeholder:text-gray-light/50 focus:outline-none focus:border-[#1DB954] focus:ring-1 focus:ring-[#1DB954] transition-all"
              disabled={loading}
            />
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 rounded-xl bg-greentext-off-white font-body font-semibold text-base hover:brightness-110 transition-all duration-200 hover:scale-[1.02] disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 size={20} className="animate-spin" />
                Criando conta...
              </>
            ) : (
              'Criar conta'
            )}
          </button>

          {/* Voltar */}
          <button
            type="button"
            onClick={() => navigate('/login', { replace: true })}
            disabled={loading}
            className="w-full text-gray-light text-sm hover:text-green-bright transition-colors"
          >
            Voltar para login
          </button>
        </form>
      </div>
    </AuthCard>
  );
};

export default RegistrationForm;