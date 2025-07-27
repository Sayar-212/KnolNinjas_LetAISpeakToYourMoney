
import { GoogleGenAI, Chat } from "@google/genai";

const API_KEY = process.env.API_KEY;

if (!API_KEY) {
  throw new Error("API_KEY environment variable is not set.");
}

const ai = new GoogleGenAI({ apiKey: API_KEY });

const model = "gemini-2.5-flash";

const systemInstruction = `You are Project Arthasashtri, an expert financial co-pilot. Your goal is to provide clear, actionable financial advice and insights. You are friendly, encouraging, and helpful. You must never give any specific investment advice, such as 'buy stock X' or 'invest in this fund'. Instead, you should provide general financial education and principles. Format your answers with markdown where appropriate (e.g., using lists, bolding key terms).`;

export function startChatSession(): Chat {
  try {
    const chat = ai.chats.create({
      model: model,
      config: {
        systemInstruction: systemInstruction,
        temperature: 0.7,
        topP: 0.9,
        topK: 40,
      },
    });
    return chat;
  } catch (error) {
    console.error("Gemini SDK Initialization Error:", error);
    throw new Error("Failed to initialize chat session with Gemini API.");
  }
}

export async function getOneTimeInsight(prompt: string): Promise<string> {
    try {
        const response = await ai.models.generateContent({
            model: model,
            contents: prompt,
            config: {
                systemInstruction: "You are a financial analyst who provides a single, concise insight. The insight should be a short paragraph.",
                temperature: 0.8,
            }
        });
        return response.text;
    } catch(error) {
        console.error("Gemini API Error (Insight):", error);
        return "Could not fetch an insight at this time. Please try again.";
    }
}
