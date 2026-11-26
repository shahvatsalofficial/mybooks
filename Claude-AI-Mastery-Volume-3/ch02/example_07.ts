/**
 * Recipe 02.3: TypeScript DynamoDB Agent Session Store Manager.
 * Author: Vatsal Shah (Lead Enterprise AI Architect)
 * Architecture: Claude AI Mastery Series — Volume 3
 */

import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { 
  DynamoDBDocumentClient, 
  PutCommand, 
  QueryCommand, 
  QueryCommandInput 
} from "@aws-sdk/lib-dynamodb";

export interface ConversationTurn {
  sessionId: string;
  turnNumber: number;
  userPrompt: string;
  agentThought?: string;
  toolsInvoked?: string[];
  agentResponse: string;
  ttlSeconds?: number;
}

export class DynamoDBAgentSessionManager {
  private docClient: DynamoDBDocumentClient;
  private tableName: string;

  constructor(tableName: string, region: string = "us-east-1") {
    const rawClient = new DynamoDBClient({ region });
    this.docClient = DynamoDBDocumentClient.from(rawClient, {
      marshallOptions: { removeUndefinedValues: true },
    });
    this.tableName = tableName;
  }

  /**
   * Persists a completed conversation turn with a 24-hour automatic TTL expiration.
   */
  async recordTurn(turn: ConversationTurn): Promise<void> {
    const turnFormatted = String(turn.turnNumber).padStart(4, "0");
    const currentEpoch = Math.floor(Date.now() / 1000);
    const ttl = currentEpoch + (turn.ttlSeconds || 86400); // 24-hour default retention

    const item = {
      PK: `SESSION#${turn.sessionId}`,
      SK: `TURN#${turnFormatted}`,
      sessionId: turn.sessionId,
      turnNumber: turn.turnNumber,
      userPrompt: turn.userPrompt,
      agentThought: turn.agentThought || "",
      toolsInvoked: turn.toolsInvoked || [],
      agentResponse: turn.agentResponse,
      createdAt: new Date().toISOString(),
      ttl: ttl,
    };

    await this.docClient.send(
      new PutCommand({
        TableName: this.tableName,
        Item: item,
      })
    );
  }

  /**
   * Retrieves the sliding working memory window (last N turns) for an active session.
   */
  async getRecentTurns(sessionId: string, limit: number = 10): Promise<ConversationTurn[]> {
    const params: QueryCommandInput = {
      TableName: this.tableName,
      KeyConditionExpression: "PK = :pk AND begins_with(SK, :skPrefix)",
      ExpressionAttributeValues: {
        ":pk": `SESSION#${sessionId}`,
        ":skPrefix": "TURN#",
      },
      ScanIndexForward: false, // Sort descending to fetch most recent turns first
      Limit: limit,
      ConsistentRead: true,   // Guarantee zero read replication lag
    };

    const result = await this.docClient.send(new QueryCommand(params));
    const items = result.Items || [];

    // Reverse back to chronological order for prompt injection
    return items.reverse().map((item) => ({
      sessionId: item.sessionId,
      turnNumber: item.turnNumber,
      userPrompt: item.userPrompt,
      agentThought: item.agentThought,
      toolsInvoked: item.toolsInvoked,
      agentResponse: item.agentResponse,
    }));
  }
}
