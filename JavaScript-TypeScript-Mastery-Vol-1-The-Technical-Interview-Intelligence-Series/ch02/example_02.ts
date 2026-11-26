class SessionManager {
    public initiateSession() {
        return new SessionManager.SecureSession();
    }
}

// Merging namespace to assign nested entities to class SessionManager
namespace SessionManager {
    export class SecureSession {
        public readonly sessionId = Math.random().toString(36).substring(2);
    }
    
    export const DEFAULT_LEASE_TIME = 3600;
}

const manager = new SessionManager();
const session = manager.initiateSession();
console.log(session.sessionId); // Successfully resolved instance path!
console.log(SessionManager.DEFAULT_LEASE_TIME); // Resolves static constant!
