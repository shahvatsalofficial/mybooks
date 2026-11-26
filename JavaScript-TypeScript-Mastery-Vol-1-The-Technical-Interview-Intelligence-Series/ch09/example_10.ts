// BrandedTypes.ts
// Strict nominal branded type boundaries

export type Brand<T, K extends string> = T & { readonly __brand: K };

export type AccountId = Brand<string, "AccountId">;
export type InvoiceId = Brand<string, "InvoiceId">;

export function createAccountId(id: string): AccountId {
    return id as AccountId;
}

export function createInvoiceId(id: string): InvoiceId {
    return id as InvoiceId;
}

// Enterprise Router Enforcement
export class EnterpriseBillingRouter {
    public static routeInvoice(accountId: AccountId, invoiceId: InvoiceId) {
        console.log(`[Router] Valid Nominal boundaries aligned. Account: ${accountId}, Invoice: ${invoiceId}`);
    }
}
