import SftpClient from "ssh2-sftp-client";

export async function createSecureSftpSession(): Promise<SftpClient> {
  const sftp = new SftpClient();
  await sftp.connect({
    host: process.env.SFTP_HOST,
    port: Number(process.env.SFTP_PORT) || 22,
    username: process.env.SFTP_USER,
    privateKey: fs.readFileSync(process.env.SFTP_KEY_PATH || "/secrets/id_ed25519"),
    algorithms: {
      serverHostKey: ["ssh-ed25519", "ecdsa-sha2-nistp256"],
      cipher: ["chacha20-poly1305@openssh.com", "aes256-gcm@openssh.com"]
    }
  });
  return sftp;
}
