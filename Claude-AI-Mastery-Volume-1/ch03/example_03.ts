/**
 * Enterprise Headless Claude Project Manager
 * Author: Vatsal Shah, Lead Enterprise AI Architect
 * Publisher: Vatsal Shah (c) 2026
 */

import axios, { AxiosInstance } from 'axios';

export interface ProjectMetadata {
  name: string;
  description: string;
  customInstructions: string;
  departmentTag: string;
}

export interface IngestedDocument {
  title: string;
  content: string;
}

export class HeadlessProjectManager {
  private client: AxiosInstance;

  constructor(private apiKey: string, private organizationId: string) {
    this.client = axios.create({
      baseURL: 'https://api.anthropic.com/v1',
      headers: {
        'x-api-key': this.apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-beta': 'projects-2024-10-01',
        'content-type': 'application/json'
      }
    });
  }

  /**
   * Provisions a sovereign enterprise project workspace programmatically.
   */
  public async createEnterpriseProject(meta: ProjectMetadata): Promise<string> {
    console.log(`[ProjectManager] Provisioning workspace: ${meta.name}...`);
    
    try {
      const response = await this.client.post('/projects', {
        name: meta.name,
        description: meta.description,
        custom_instructions: meta.customInstructions,
        metadata: {
          cost_center: meta.departmentTag,
          provisioned_by: 'enterprise-ci-cd'
        }
      });

      const projectId = response.data.id;
      console.log(`✅ Successfully provisioned Project ID: ${projectId}`);
      return projectId;
    } catch (error: any) {
      console.error('[ProjectManager] Failed to provision project:', error.response?.data || error.message);
      throw error;
    }
  }

  /**
   * Uploads and indexes a batch of reference documents into project memory.
   */
  public async uploadKnowledgeFiles(projectId: string, docs: IngestedDocument[]): Promise<void> {
    console.log(`[ProjectManager] Uploading ${docs.length} documents to Project ${projectId}...`);

    for (const doc of docs) {
      try {
        await this.client.post(`/projects/${projectId}/docs`, {
          title: doc.title,
          content: doc.content
        });
        console.log(`  -> Indexed: ${doc.title} (${doc.content.length} chars)`);
      } catch (err: any) {
        console.error(`  ⚠️ Failed to index ${doc.title}:`, err.response?.data || err.message);
      }
    }

    console.log(`✅ Knowledge synchronization complete for Project ${projectId}.`);
  }
}
