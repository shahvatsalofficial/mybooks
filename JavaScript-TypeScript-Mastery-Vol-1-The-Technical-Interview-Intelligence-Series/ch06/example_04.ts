type USD = { amount: number };
type EUR = { amount: number };

function processUSDPayment(payment: USD) {
    console.log(`Processing $${payment.amount} USD`);
}

const euroWallet: EUR = { amount: 100 };

// Compiled successfully under a structural system!
processUSDPayment(euroWallet);
