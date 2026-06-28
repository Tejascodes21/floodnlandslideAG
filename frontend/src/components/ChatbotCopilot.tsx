import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, X, Bot, Sparkles, CheckCircle } from 'lucide-react';
import { apiClient } from '../config';

interface ChatbotCopilotProps {
  lang: 'en' | 'hi' | 'mr';
}

const chatTranslations = {
  en: {
    greeting: "Hello! I am GeoShield AI Copilot. Ask me about safe camps, landslide guidelines, or how to register distress signals.",
    placeholder: "Type message to Copilot...",
    send_btn: "Send",
    copilot_label: "Disaster AI Copilot",
    action_notif: "GIS Action Triggered: Highlight closest shelter on map!"
  },
  hi: {
    greeting: "नमस्ते! मैं जियोशील्ड एआई कोपायलट हूं। मुझसे सुरक्षित शिविरों, भूस्खलन दिशानिर्देशों, या संकट संकेतों को दर्ज करने के बारे में पूछें।",
    placeholder: "कोपायलट को संदेश लिखें...",
    send_btn: "भेजें",
    copilot_label: "आपदा एआई कोपायलट",
    action_notif: "GIS एक्शन ट्रिगर: मानचित्र पर निकटतम निवारा शिविर हाइलाइट करें!"
  },
  mr: {
    greeting: "नमस्कार! मी जिओशील्ड एआय कोपायलट आहे. मला निवारा केंद्रांबद्दल, दरड कोसळण्यासंबंधित घ्यावयाच्या काळजीबद्दल किंवा मदतीबद्दल विचारा.",
    placeholder: "संदेश टाईप करा...",
    send_btn: "पाठवा",
    copilot_label: "आपत्ती एआय कोपायलट",
    action_notif: "GIS ॲक्शन ट्रिगर: नकाशावर जवळील निवारा केंद्र दर्शवा!"
  }
};

interface ChatMessage {
  sender: 'user' | 'bot';
  text: string;
  action?: any;
}

export default function ChatbotCopilot({ lang }: ChatbotCopilotProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMsg, setInputMsg] = useState("");
  const [loading, setLoading] = useState(false);
  const [notif, setNotif] = useState(false);
  
  const endRef = useRef<HTMLDivElement>(null);
  const t = chatTranslations[lang];

  // Load welcome greeting on mount or language switch
  useEffect(() => {
    setMessages([
      { sender: 'bot', text: t.greeting }
    ]);
  }, [lang]);

  // Auto scroll
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isOpen]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMsg.trim()) return;

    const userText = inputMsg;
    setMessages(prev => [...prev, { sender: 'user', text: userText }]);
    setInputMsg("");
    setLoading(true);

    try {
      const data = await apiClient.post('/api/chatbot', {
        message: userText,
        lat: 19.076,
        lon: 72.877,
        lang: lang
      });
      
      setMessages(prev => [
        ...prev, 
        { sender: 'bot', text: data.reply, action: data.action_command }
      ]);
      
      // Trigger GIS map animation alert if a routing/shelter action is returned
      if (data.action_command) {
        setNotif(true);
        setTimeout(() => setNotif(false), 4500);
      }
    } catch (err) {
      console.error(err);
      // Fallback answers if offline
      let replyText = "I am processing your geospatial query. In high risk monsoon sectors, please proceed immediately to government relief camps.";
      if (userText.toLowerCase().includes("shelter")) replyText = t.action_notif;
      
      setMessages(prev => [
        ...prev,
        { sender: 'bot', text: replyText }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* 1. Floating trigger Bubble icon */}
      {!isOpen && (
        <button 
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 p-4 bg-gradient-to-br from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-600 rounded-full text-white shadow-neon-blue border border-blue-400/20 glow-button flex items-center justify-center cursor-pointer"
          title="Disaster AI Copilot"
        >
          <Bot className="w-6 h-6 animate-pulse" />
          <span className="absolute -top-1 -right-1 w-3.5 h-3.5 bg-red-500 border border-bgDark rounded-full animate-ping"></span>
          <span className="absolute -top-1 -right-1 w-3.5 h-3.5 bg-red-500 border border-bgDark rounded-full"></span>
        </button>
      )}

      {/* 2. Collapsible Drawer Container */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 z-50 w-[350px] h-[480px] glass-panel-glow border border-blue-500/25 rounded-2xl flex flex-col overflow-hidden shadow-glass animate-in fade-in slide-in-from-bottom-6 duration-300">
          
          {/* Header */}
          <div className="bg-[#0b1224] border-b border-slate-900 px-4 py-3 flex justify-between items-center shrink-0">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-blue-400 animate-spin [animation-duration:6s]" />
              <span className="text-xs font-bold text-gray-200 tracking-wide">{t.copilot_label}</span>
            </div>
            <button 
              onClick={() => setIsOpen(false)}
              className="text-slate-400 hover:text-gray-200 p-1 hover:bg-slate-900/60 rounded transition-all"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Action notification banner */}
          {notif && (
            <div className="bg-emerald-950/80 border-b border-emerald-900 text-emerald-400 px-4 py-1.5 text-[10px] font-bold flex items-center gap-1.5 animate-pulse shrink-0">
              <CheckCircle className="w-3.5 h-3.5" />
              <span>{t.action_notif}</span>
            </div>
          )}

          {/* Messages lists container */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-black/20">
            {messages.map((m, i) => (
              <div 
                key={i} 
                className={`flex ${m.sender === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in duration-200`}
              >
                <div 
                  className={`max-w-[85%] rounded-xl px-3 py-2 text-xs leading-relaxed ${m.sender === 'user' ? 'bg-blue-600/90 text-white font-medium' : 'bg-slate-900/90 border border-slate-800 text-gray-200 font-medium'}`}
                >
                  {m.text}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-400 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></span>
                  <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0.2s]"></span>
                  <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0.4s]"></span>
                </div>
              </div>
            )}
            <div ref={endRef}></div>
          </div>

          {/* Footer input form */}
          <form onSubmit={handleSend} className="p-3 bg-[#0a0f1d] border-t border-slate-900 flex gap-2 shrink-0">
            <input 
              type="text" 
              value={inputMsg}
              onChange={(e) => setInputMsg(e.target.value)}
              placeholder={t.placeholder}
              className="flex-1 bg-slate-950/80 border border-slate-900 px-3.5 py-1.5 rounded-lg text-xs text-gray-200 focus:outline-none focus:border-blue-500"
            />
            <button 
              type="submit"
              className="p-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-all glow-button shrink-0 flex items-center justify-center cursor-pointer"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>

        </div>
      )}
    </>
  );
}
