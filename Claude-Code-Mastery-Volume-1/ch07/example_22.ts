// Legacy implementation (v1.8)
function validateToken(token, callback) {
  jwt.verify(token, secret, (err, decoded) => {
    if (err) return callback(err, null);
    callback(null, decoded);
  });
}

// Flawed autonomous agent migration (v2.0)
async function validateToken(token: string): Promise<UserClaims> {
  // FATAL FLAW: Failed to await the asynchronous verification promise inside a try/catch
  return new Promise((resolve, reject) => {
    jwt.verify(token, secret, (err, decoded) => {
      if (err) reject(new AuthenticationError("INVALID_TOKEN")); // Unhandled Rejection!
      resolve(decoded as UserClaims);
    });
  });
}
