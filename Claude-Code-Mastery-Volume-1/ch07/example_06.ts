// THE DANGEROUS DEFENSIVE MASKING ANTI-PATTERN
// Original failing line:
const commission = broker.commissionRate * trade.notionalValue;

// Flawed agent patch (Silent Semantic Corruption):
const commission = (broker?.commissionRate ?? 0.0) * (trade?.notionalValue ?? 0.0);
