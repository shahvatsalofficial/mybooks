// Dual-Writing Shadow Proxy Implementation
export class BillingShadowProxy implements IBillingService {
  constructor(
    private readonly legacyEngine: LegacyInvoiceEngine,
    private readonly grpcClient: BillingGrpcServiceClient,
    private readonly telemetry: TelemetryEmitter
  ) {}

  async chargeInvoice(request: ChargeInvoiceRequest): Promise<ChargeInvoiceResult> {
    // 1. Authoritative primary execution
    const primaryResult = await this.legacyEngine.chargeInvoice(request);

    // 2. Non-blocking asynchronous shadow evaluation
    setImmediate(async () => {
      try {
        const shadowResult = await this.grpcClient.chargeInvoice(request);
        this.verifySemanticParity(primaryResult, shadowResult, request.invoiceId);
      } catch (err: any) {
        this.telemetry.emitAlarm('billing.shadow_failure', { error: err.message });
      }
    });

    return primaryResult;
  }

  private verifySemanticParity(primary: ChargeInvoiceResult, shadow: any, invoiceId: string): void {
    if (primary.amountChargedCents !== shadow.amountChargedCents || primary.status !== shadow.status) {
      this.telemetry.emitAlarm('billing.parity_mismatch', {
        invoiceId,
        primaryDelta: primary.amountChargedCents,
        shadowDelta: shadow.amountChargedCents
      });
    }
  }
}
