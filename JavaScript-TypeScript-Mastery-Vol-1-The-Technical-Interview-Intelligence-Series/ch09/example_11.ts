const account = createAccountId("ACT-100");
const invoice = createInvoiceId("INV-999");

EnterpriseBillingRouter.routeInvoice(account, invoice); // Compilation: SUCCESS

// Direct string assignment or reversed signatures fail at compile time:
// EnterpriseBillingRouter.routeInvoice(invoice, account); 
// Error: Argument of type 'InvoiceId' is not assignable to parameter of type 'AccountId'
