const balanceUSD = makeUSD(500);
const taxEUR = makeEUR(50);

// Compilation Error: TypeScript blocks arithmetic operations between distinct branded types
const total = balanceUSD + taxEUR;
