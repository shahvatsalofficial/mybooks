import jsforce from "jsforce";
import { Client as NotionClient } from "@notionhq/client";

export class CrmNotionTransformer {
  private sfConn: jsforce.Connection;
  private notion: NotionClient;

  constructor() {
    this.sfConn = new jsforce.Connection({
      loginUrl: process.env.SALESFORCE_LOGIN_URL || "https://login.salesforce.com"
    });
    this.notion = new NotionClient({
      auth: process.env.NOTION_API_KEY
    });
  }

  // Authenticate Salesforce via OAuth2 Username-Password Flow
  async connectSalesforce() {
    await this.sfConn.login(
      process.env.SALESFORCE_USER!,
      process.env.SALESFORCE_PASSWORD! + process.env.SALESFORCE_SECURITY_TOKEN!
    );
  }

  // Query high-value opportunities using SOQL
  async queryTopOpportunities(minAmount: number = 50000): Promise<any[]> {
    const query = `
      SELECT Id, Name, Amount, StageName, CloseDate, Account.Name
      FROM Opportunity
      WHERE Amount >= ${minAmount} AND IsClosed = false
      ORDER BY Amount DESC
      LIMIT 25
    `;
    const res = await this.sfConn.query(query);
    return res.records;
  }

  // Transform Salesforce Opportunity to Notion Database Page
  async syncOpportunityToNotion(notionDatabaseId: string, opp: any) {
    await this.notion.pages.create({
      parent: { database_id: notionDatabaseId },
      properties: {
        Name: {
          title: [{ text: { content: opp.Name } }]
        },
        Account: {
          rich_text: [{ text: { content: opp.Account?.Name || "N/A" } }]
        },
        Amount: {
          number: Number(opp.Amount) || 0
        },
        Stage: {
          select: { name: opp.StageName }
        },
        CloseDate: {
          date: { start: opp.CloseDate }
        }
      }
    });
  }
}
