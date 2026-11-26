// Legacy src/routes/checkout.ts (Tightly coupled)
import Stripe from 'stripe';
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

app.post('/api/checkout', async (req, res) => {
  const { amount, currency, token } = req.body;
  const charge = await stripe.charges.create({ amount, currency, source: token });
  await db.query('INSERT INTO transactions ...', [charge.id, amount]);
  res.json({ success: true, chargeId: charge.id });
});
