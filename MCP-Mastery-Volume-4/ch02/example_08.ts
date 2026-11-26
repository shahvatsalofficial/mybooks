export interface VfsNode {
  provider: "onedrive" | "dropbox";
  path: string;
  name: string;
  sizeBytes: number;
  isFolder: boolean;
  downloadUrl?: string;
}

export class CloudDriveBridge {
  private oneDriveToken: string = "";
  private dropBoxToken: string = "";

  // Normalize OneDrive Graph API item to common VFS format
  static normalizeOneDriveItem(item: any): VfsNode {
    return {
      provider: "onedrive",
      path: item.parentReference?.path ? `${item.parentReference.path}/${item.name}` : `/${item.name}`,
      name: item.name,
      sizeBytes: item.size || 0,
      isFolder: Boolean(item.folder),
      downloadUrl: item["@microsoft.graph.downloadUrl"]
    };
  }

  // Normalize Dropbox metadata item to common VFS format
  static normalizeDropboxItem(item: any): VfsNode {
    return {
      provider: "dropbox",
      path: item.path_display || item.path_lower,
      name: item.name,
      sizeBytes: item.size || 0,
      isFolder: item[".tag"] === "folder"
    };
  }

  // Unified Search Query Fan-Out
  async searchAllDrives(query: string): Promise<VfsNode[]> {
    const results: VfsNode[] = [];

    // Parallel fetch across providers
    const promises: Promise<void>[] = [];

    if (this.oneDriveToken) {
      promises.push(
        fetch(`https://graph.microsoft.com/v1.0/me/drive/root/search(q='${encodeURIComponent(query)}')`, {
          headers: { Authorization: `Bearer ${this.oneDriveToken}` }
        })
          .then((r) => r.json())
          .then((data) => {
            if (Array.isArray(data.value)) {
              results.push(...data.value.map(CloudDriveBridge.normalizeOneDriveItem));
            }
          })
          .catch((err) => console.error("OneDrive search failed", err))
      );
    }

    if (this.dropBoxToken) {
      promises.push(
        fetch("https://api.dropboxapi.com/2/files/search_v2", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${this.dropBoxToken}`,
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ query, options: { max_results: 25 } })
        })
          .then((r) => r.json())
          .then((data) => {
            if (Array.isArray(data.matches)) {
              results.push(...data.matches.map((m: any) => CloudDriveBridge.normalizeDropboxItem(m.metadata.metadata)));
            }
          })
          .catch((err) => console.error("Dropbox search failed", err))
      );
    }

    await Promise.allSettled(promises);
    return results;
  }
}
