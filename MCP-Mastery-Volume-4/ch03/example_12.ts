import Stripe from "stripe";

const stripeApiKey = process.env.STRIPE_RESTRICTED_KEY || "";
if (stripeApiKey.startsWith("sk_live_")) {
  throw new Error("FATAL: Unrestricted Stripe live secret key detected. Use a restricted key (rk_live_...) with read-only permissions.");
}

const stripe = new Stripe(stripeApiKey, {
  apiVersion: "2024-06-20"
});

export async function inspectCustomerDisputes(customerId: string): Promise<any[]> {
  const disputes = await stripe.disputes.list({
    limit: 10
  });

  // Filter disputes relevant to customer
  const matched = disputes.data.filter((d) => {
    const charge = typeof d.charge === "string" ? d.charge : d.charge?.id;
    return d.evidence?.customer_name?.toLowerCase().includes(customerId.toLowerCase());
  });

  return matched.map((d) => ({
    id: d.id,
    amountCents: d.amount,
    currency: d.currency,
    reason: d.reason,
    status: d.status,
    evidenceDueBy: new Date(d.evidence_details.due_by * 1000).toISOString()
  }));
}
