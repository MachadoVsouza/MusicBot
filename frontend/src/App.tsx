import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import Login from "./pages/Login";
import Cadastro from "./pages/Cadastro";
import Entrar from "./pages/Entrar";
import RecuperarSenha from "./pages/RecuperarSenha";
import Chat from "./pages/Chat";
import BaseConhecimento from "./pages/BaseConhecimento";
import Dashboard from "./pages/Dashboard";
import AuthCallback from "./pages/AuthCallback";
import UnderConstruction from "./pages/UnderConstruction";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="/login" element={<Login />} />
            <Route path="/cadastro" element={<Cadastro />} />
            <Route path="/entrar" element={<Entrar />} />
            <Route path="/recuperar-senha" element={<RecuperarSenha />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/moderacao/base-conhecimento" element={<BaseConhecimento />} />
            <Route path="/moderacao/dashboard" element={<Dashboard />} />
            <Route path="/auth/callback" element={<AuthCallback />} />
            <Route path="/under-construction" element={<UnderConstruction />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
