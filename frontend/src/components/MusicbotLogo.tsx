import { Music } from 'lucide-react';

const MusicbotLogo = ({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) => {
  const sizes = { sm: 'text-xl', md: 'text-3xl', lg: 'text-5xl' };
  const iconSizes = { sm: 20, md: 28, lg: 40 };

  return (
    <div className="flex items-center gap-2 justify-center">
      <div className="bg-magenta p-2 rounded-xl">
        <Music size={iconSizes[size]} className="text-off-white" />
      </div>
      <span className={`font-display font-bold text-off-white ${sizes[size]}`}>
        Musicbot
      </span>
    </div>
  );
};

export default MusicbotLogo;
