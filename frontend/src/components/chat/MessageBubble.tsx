import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Message, Source } from '@/types';
import MiniPlayer from './MiniPlayer';

const MessageBubble = ({
  message,
  onSourceClick,
}: {
  message: Message;
  onSourceClick: (source: Source) => void;
}) => (
  <article className={`w-full flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
    <div className={`max-w-[90%] sm:max-w-[78%] rounded-2xl px-4 sm:px-5 py-3 sm:py-4 ${message.role === 'user' ? 'bg-[#1DB954] text-off-white rounded-br-md' : 'bg-[#282828] text-off-white rounded-bl-md'}`}>
      <div className={`text-sm sm:text-base leading-relaxed prose prose-invert max-w-none prose-p:my-1 prose-pre:bg-[#0D0D0D] prose-code:text-[#1DB954] ${message.role === 'user' ? 'text-off-white' : 'text-off-white'}`}>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {message.content}
        </ReactMarkdown>
        {message.streaming && <span className="inline-block w-2 h-4 ml-1 bg-[#1DB954] animate-pulse rounded-sm" />}
      </div>
      {message.role === 'bot' && message.midia?.preview_url && <MiniPlayer midia={message.midia} />}
      <div className="mt-2 text-xs text-slate flex items-center gap-2">
        <span>{message.timestamp}</span>
        {message.sources && message.sources.length > 0 && (
          <button type="button" onClick={() => onSourceClick(message.sources![0])} className="text-[#1DB954] hover:underline">Fonte</button>
        )}
      </div>
    </div>
  </article>
);

export default MessageBubble;