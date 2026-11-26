import path from "path";
import fs from "fs";

export class SecurePathResolver {
  private readonly rootWorkspaceDir: string;

  constructor(rootWorkspaceDir: string) {
    // Resolve and canonicalize the root workspace directory
    this.rootWorkspaceDir = path.resolve(fs.realpathSync(rootWorkspaceDir));
  }

  /**
   * Validates and resolves a user-provided relative path within the secure workspace.
   * Throws an explicit error if the path attempts to escape the root boundary.
   */
  public resolveSafePath(userRelativePath: string): string {
    // 1. Strip null bytes
    const cleanPath = userRelativePath.replace(/\0/g, "");

    // 2. Reject absolute paths immediately
    if (path.isAbsolute(cleanPath)) {
      throw new Error(`SECURITY_VIOLATION: Absolute paths are strictly prohibited: ${cleanPath}`);
    }

    // 3. Resolve path against workspace root
    const resolvedPath = path.resolve(this.rootWorkspaceDir, cleanPath);

    // 4. Verify boundary containment
    if (!resolvedPath.startsWith(this.rootWorkspaceDir + path.sep) && resolvedPath !== this.rootWorkspaceDir) {
      throw new Error(`SECURITY_VIOLATION: Path traversal detected outside workspace: ${cleanPath}`);
    }

    // 5. If file exists, verify realpath (resolving symlinks)
    if (fs.existsSync(resolvedPath)) {
      const realTarget = fs.realpathSync(resolvedPath);
      if (!realTarget.startsWith(this.rootWorkspaceDir + path.sep) && realTarget !== this.rootWorkspaceDir) {
        throw new Error(`SECURITY_VIOLATION: Symlink target escapes workspace root: ${cleanPath} -> ${realTarget}`);
      }
      return realTarget;
    }

    return resolvedPath;
  }
}
