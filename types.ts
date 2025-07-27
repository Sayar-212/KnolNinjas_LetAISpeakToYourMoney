
export interface Bill {
  id: string;
  name: string;
  amount: number;
  dueDate: string; // Format: "DD Mon", e.g., "25 Jun"
  icon: React.ComponentType<{ className?: string }>;
}

export interface AnalyticsData {
  name: string;
  income: number;
  expense: number;
}

export interface ChatMessage {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp: number;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
}

export interface Agent {
    id: string;
    name: string;
    role: string;
    avatar: React.ComponentType<{ className?: string }>;
    status: 'Active' | 'Inactive';
}

export type View = 'Chat' | 'Dashboard' | 'Profile' | 'ChatHistory';
