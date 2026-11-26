interface PriceMap {
    [currency: string]: number;
}
const prices: PriceMap = { USD: 100 };
const price = prices["EUR"]; // Typed as 'number' but is actually 'undefined' at runtime!
console.log(price.toFixed(2)); // Runtime TypeError: Cannot read properties of undefined!
