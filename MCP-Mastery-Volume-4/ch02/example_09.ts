export async function initiateDeviceAuthorization(clientId: string, tenantId: string = "common") {
  const endpoint = `https://login.microsoftonline.com/${tenantId}/oauth2/v2.0/devicecode`;
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      client_id: clientId,
      scope: "Files.Read Files.Read.All offline_access"
    })
  });

  const data = await response.json();
  // Returns: user_code, verification_uri, device_code, expires_in, interval
  return {
    userCode: data.user_code,
    verificationUri: data.verification_uri,
    deviceCode: data.device_code,
    intervalSeconds: data.interval || 5,
    expiresInSeconds: data.expires_in
  };
}
