import { memo, ReactNode } from 'react';
import { motion } from 'framer-motion';

const AuthCard = memo(({ children }: { children: ReactNode }) => (
  <div className="min-h-screen flex items-center justify-center bg-black p-4">
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="bg-[#181818] w-full max-w-[420px] rounded-card p-8 shadow-[0_4px_24px_rgba(0,0,0,0.6)] border border-[#282828]"
    >
      {children}
    </motion.div>
  </div>
));

AuthCard.displayName = 'AuthCard';
export default AuthCard;
