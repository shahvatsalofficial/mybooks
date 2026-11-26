const price = prices["EUR"]; // Correctly typed as 'number | undefined'
if (price !== undefined) {
    console.log(price.toFixed(2)); // Compiled successfully and safe!
}
