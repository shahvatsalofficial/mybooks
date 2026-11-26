const isDrained = process.stdout.write(wireString);
if (!isDrained) {
  // Backpressure event: Pause reading stdin until the drain event fires!
  await new Promise((resolve) => process.stdout.once("drain", resolve));
}
