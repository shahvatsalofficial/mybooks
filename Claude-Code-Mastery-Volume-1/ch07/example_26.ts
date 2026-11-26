// Refactored src/routes/checkout.ts
import { IPaymentGateway } from '../services/IPaymentGateway';
import { ITransactionRepository } from '../services/ITransactionRepository';

export class CheckoutController {
  constructor(
    private readonly paymentGateway: IPaymentGateway,
    private readonly transactionRepo: ITransactionRepository
  ) {}

  public async handleCheckout(req: Request, res: Response): Promise<void> {
    const { amount, currency, token } = req.body;
    const payment = await this.paymentGateway.charge(amount, currency, token);
    await this.transactionRepo.recordTransaction(payment.chargeId, amount);
    res.json({ success: true, chargeId: payment.chargeId });
  }
}
