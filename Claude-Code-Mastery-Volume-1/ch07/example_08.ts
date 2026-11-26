// src/contracts/IBillingService.ts
export interface IBillingService {
  chargeInvoice(request: ChargeInvoiceRequest): Promise<ChargeInvoiceResult>;
  getInvoiceById(invoiceId: string): Promise<InvoiceDTO>;
  refundTransaction(transactionId: string, amountCents: number): Promise<RefundResult>;
}
