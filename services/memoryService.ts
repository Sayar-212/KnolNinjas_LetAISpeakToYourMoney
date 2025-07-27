import { ChatMessage, ChatSession } from '../types';

interface MemoryEntry {
  id: string;
  content: string;
  timestamp: number;
  sessionId: string;
  embedding?: number[];
}

class MemoryService {
  private memories: MemoryEntry[] = [];

  constructor() {
    this.loadMemories();
  }

  private loadMemories() {
    const saved = localStorage.getItem('chatMemories');
    if (saved) {
      this.memories = JSON.parse(saved);
    }
  }

  private saveMemories() {
    localStorage.setItem('chatMemories', JSON.stringify(this.memories));
  }

  addMemory(message: ChatMessage, sessionId: string) {
    if (message.sender === 'user' && message.text.trim()) {
      const memory: MemoryEntry = {
        id: `${sessionId}-${message.id}`,
        content: message.text,
        timestamp: message.timestamp,
        sessionId
      };
      this.memories.push(memory);
      this.saveMemories();
    }
  }

  getRelevantMemories(query: string, limit: number = 5): string[] {
    const queryLower = query.toLowerCase();
    const relevant = this.memories
      .filter(memory => 
        memory.content.toLowerCase().includes(queryLower) ||
        this.calculateSimilarity(memory.content.toLowerCase(), queryLower) > 0.3
      )
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, limit)
      .map(memory => memory.content);
    
    return relevant;
  }

  private calculateSimilarity(text1: string, text2: string): number {
    const words1 = text1.split(' ');
    const words2 = text2.split(' ');
    const intersection = words1.filter(word => words2.includes(word));
    return intersection.length / Math.max(words1.length, words2.length);
  }

  getContextForSession(sessionId: string): string {
    const sessionMemories = this.memories
      .filter(memory => memory.sessionId !== sessionId)
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, 10);
    
    if (sessionMemories.length === 0) return '';
    
    return `Previous context: ${sessionMemories.map(m => m.content).join('; ')}`;
  }

  getConversationSummaries(limit: number = 3): string[] {
    const allSessions = JSON.parse(localStorage.getItem('chatSessions') || '[]');
    return allSessions.slice(0, limit).map((session: any) => {
      const userMessages = session.messages.filter((m: any) => m.sender === 'user');
      const summary = `"${session.title}" - ${userMessages.length} messages, topics: ${userMessages.slice(0, 3).map((m: any) => m.text.slice(0, 50)).join(', ')}`;
      return summary;
    });
  }
}

export const memoryService = new MemoryService();

// Helper function to get conversation summaries for AI
export const getConversationSummariesForAI = (): string => {
  const allSessions = JSON.parse(localStorage.getItem('chatSessions') || '[]');
  if (allSessions.length === 0) return 'No previous conversations found.';
  
  const summaries = allSessions.slice(0, 5).map((session: any, index: number) => {
    const userMessages = session.messages.filter((m: any) => m.sender === 'user');
    const aiMessages = session.messages.filter((m: any) => m.sender === 'ai');
    const date = new Date(session.createdAt).toLocaleDateString();
    
    return `${index + 1}. Conversation "${session.title}" (${date}):\n   - User topics: ${userMessages.slice(0, 2).map((m: any) => m.text.slice(0, 80)).join('; ')}\n   - AI discussed: ${aiMessages.slice(0, 2).map((m: any) => m.text.slice(0, 80)).join('; ')}`;
  });
  
  return `Here are your last ${Math.min(5, allSessions.length)} conversations:\n\n${summaries.join('\n\n')}`;
};