import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Database, AlertCircle } from 'lucide-react';
import './Chatbot.css';

interface Message {
  id: string;
  sender: 'user' | 'agent';
  text: string;
}

const Chatbot: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', sender: 'agent', text: 'Z.AI Kernel Online. How can I assist with your operations today?' }
  ]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = input;
    setInput('');
    setMessages(prev => [...prev, { id: Date.now().toString(), sender: 'user', text: userMsg }]);

    setTimeout(() => {
      setMessages(prev => [...prev, { 
        id: Date.now().toString(), 
        sender: 'agent', 
        text: `Analyzing query: "${userMsg}". Context parsed from Business Context Snapshot. Generating operational response...` 
      }]);
    }, 1000);
  };

  return (
    <div className="chatbot-container">
      <header className="page-header">
        <div>
          <h1 className="page-title">Instruction Channel</h1>
          <p className="page-subtitle">Direct communication with Z.AI GLM</p>
        </div>
      </header>

      <div className="chatbot-layout">
        {/* Chat Interface */}
        <div className="chat-interface card">
          <div className="chat-history">
            {messages.map(msg => (
              <div key={msg.id} className={`chat-message ${msg.sender}`}>
                <div className="message-avatar">
                  {msg.sender === 'agent' ? <Bot size={20} /> : <User size={20} />}
                </div>
                <div className="message-bubble">
                  {msg.text}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
          
          <form className="chat-input-area" onSubmit={handleSend}>
            <input 
              type="text" 
              className="chat-input" 
              placeholder="Ask for an operational summary or give direct instructions..." 
              value={input}
              onChange={e => setInput(e.target.value)}
            />
            <button type="submit" className="btn btn-primary send-btn">
              <Send size={18} />
            </button>
          </form>
        </div>

        {/* Business Context Sidebar */}
        <div className="context-sidebar card">
          <div className="card-header">
            <h3 className="card-title"><Database className="inline-icon" size={18} /> Context Snapshot</h3>
          </div>
          <div className="context-body">
            <p className="text-muted text-sm mb-4">Injected into GLM context window</p>
            
            <div className="context-section">
              <h4>Active Alerts</h4>
              <ul className="context-list text-accent-red">
                <li><AlertCircle size={14} className="inline-icon" /> Salmon Price Spike (18%)</li>
                <li><AlertCircle size={14} className="inline-icon" /> Premium Rice Low (0.8d)</li>
              </ul>
            </div>
            
            <div className="context-section mt-4">
              <h4>Top Inventory</h4>
              <ul className="context-list">
                <li>Wagyu Beef A4: 42 kg</li>
                <li>Chicken: 105 kg</li>
                <li>Nori: 500 sheets</li>
              </ul>
            </div>
            
            <div className="context-section mt-4">
              <h4>Current Orders</h4>
              <ul className="context-list">
                <li>Active: 12</li>
                <li>VIP Tables: Table 4</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;
