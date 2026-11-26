function computeMultiplier(factor) {
    const baseline = 1.5;
    return factor * baseline;
}

function processTransaction(amount) {
    const conversionRate = computeMultiplier(amount);
    return amount * conversionRate;
}

function initInvoice() {
    const rawTotal = 1500;
    const finalTotal = processTransaction(rawTotal);
    return finalTotal;
}

initInvoice();
