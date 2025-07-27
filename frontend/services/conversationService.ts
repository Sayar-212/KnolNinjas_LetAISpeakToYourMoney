import { config } from "../config";
import { v4 as uuidv4 } from 'uuid';

interface ConversationAPI {
	createConversation(): Promise<string>;
	sendMessage(
		text: string,
		contextId: string
	): Promise<{ message_id: string; context_id: string }>;
	listMessages(conversationId: string): Promise<any[]>;
	getPendingMessages(): Promise<any[]>;
}

class ConversationService implements ConversationAPI {
	private baseUrl: string;

	constructor(baseUrl: string = config.backendUrl) {
		this.baseUrl = baseUrl;
	}

	private async makeRequest(
		endpoint: string,
		method: string = "POST",
		params?: any
	) {
		const requestBody = params && {
			id: Date.now().toString(),
			jsonrpc: "2.0",
			method: endpoint.substring(1),
			params,
		};

		const config: RequestInit = {
			method,
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify(requestBody),
		};

		console.log(config);

		const response = await fetch(`${this.baseUrl}${endpoint}`, config);

		if (!response.ok) {
			throw new Error(`HTTP error! status: ${response.status}`);
		}

		const data = await response.json();
		return data.result;
	}

	async createConversation(): Promise<string> {
		const result = await this.makeRequest("/conversation/create", "POST");
		console.log(result);
		return result.conversation_id;
	}

	async sendMessage(
		text: string,
		contextId: string
	): Promise<{ message_id: string; context_id: string }> {
		const messageParams = {
			configuration: null,
			contextId,
			extensions: null,
			kind: "message",
			messageId: uuidv4(),
			metadata: null,
			parts: [
				{
					kind: "text",
					metadata: null,
					text,
				},
			],
			referenceTaskIds: null,
			role: "user",
			taskId: null,
		};
		return await this.makeRequest("/message/send", "POST", messageParams);
	}

	async listMessages(conversationId: string): Promise<any[]> {
		return await this.makeRequest("/message/list", "POST", conversationId);
	}

	async getPendingMessages(): Promise<any[]> {
		return await this.makeRequest("/message/pending", "POST");
	}
}

export const conversationService = new ConversationService();
