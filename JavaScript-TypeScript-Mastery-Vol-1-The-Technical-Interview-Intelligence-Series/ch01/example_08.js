function createSecureTokenEngine(secretSalt) {
    let hashCount = 0;
    return {
        generateToken: function(payload) {
            hashCount++;
            return `${payload}-${secretSalt}-${hashCount}`;
        }
    };
}

const engine = createSecureTokenEngine("SECRET_123");
console.log(engine.generateToken("UserSession")); // "UserSession-SECRET_123-1"
