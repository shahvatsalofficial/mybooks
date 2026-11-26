if (item.json.refund_amount > 500) {
    throw new Error("REFUND_LIMIT_EXCEEDED: Manual Approval Required");
}
return item;
