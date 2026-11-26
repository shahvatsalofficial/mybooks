// Type assertion is limited to the factory constructor
export function makeUSD(value: number): USD {
    return value as USD;
}

export function makeEUR(value: number): EUR {
    return value as EUR;
}

export function makeINR(value: number): INR {
    return value as INR;
}

const walletUSD = makeUSD(150.50);
const walletEUR = makeEUR(100.00);

function depositUSDFunds(funds: USD) {
    console.log(`Depositing ${funds} USD`);
}

depositUSDFunds(walletUSD); // Safe and compile-ready!

// Compilation Error: Argument of type 'EUR' is not assignable to parameter of type 'USD'.
depositUSDFunds(walletEUR); 

// Compilation Error: Type 'USD' is not assignable to type 'EUR'.
const mySavings: EUR = walletUSD;
