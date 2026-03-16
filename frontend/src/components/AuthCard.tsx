import { ReactNode } from 'react';
import { motion } from 'framer-motion';

const AuthCard = ({ children }: { children: ReactNode }) => (
  <div className="min-h-screen flex items-center justify-center bg-midnight p-4">
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="glass w-full max-w-[420px] rounded-card p-8 shadow-[0_8px_32px_rgba(0,0,0,0.4)]"
    >
      {children}
    </motion.div>
  </div>
);

export default AuthCard;
