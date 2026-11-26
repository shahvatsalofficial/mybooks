export interface HelmReleaseInfo {
  name: string;
  namespace: string;
  revision: number;
  updated: string;
  status: "deployed" | "failed" | "superseded";
  chart: string;
  appVersion: string;
}

export class HelmReleaseManager {
  // Inspect release revision history for a release
  static async getReleaseHistory(releaseName: string, namespace: string): Promise<HelmReleaseInfo[]> {
    const { execFile } = require("child_process");
    return new Promise((resolve, reject) => {
      execFile("helm", ["history", releaseName, "-n", namespace, "-o", "json"], (err: any, stdout: string) => {
        if (err) return reject(new Error(`Helm History Error: ${err.message}`));
        try {
          const list = JSON.parse(stdout);
          const releases: HelmReleaseInfo[] = list.map((item: any) => ({
            name: releaseName,
            namespace,
            revision: item.revision,
            updated: item.updated,
            status: item.status,
            chart: item.chart,
            appVersion: item.app_version
          }));
          resolve(releases);
        } catch (parseErr) {
          reject(parseErr);
        }
      });
    });
  }

  // Execute safe atomic rollback to previous revision
  static async rollbackRelease(releaseName: string, namespace: string, targetRevision: number): Promise<string> {
    const { execFile } = require("child_process");
    return new Promise((resolve, reject) => {
      // Enforce --wait and --timeout 3m to ensure rollback succeeds before reporting
      execFile(
        "helm",
        ["rollback", releaseName, String(targetRevision), "-n", namespace, "--wait", "--timeout", "3m0s"],
        (err: any, stdout: string) => {
          if (err) return reject(new Error(`Helm Rollback Failed: ${err.message}`));
          resolve(`Rollback of release '${releaseName}' to revision ${targetRevision} completed successfully.`);
        }
      );
    });
  }
}
