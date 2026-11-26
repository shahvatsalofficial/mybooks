type DoubleNested = Promise<Promise<Promise<string[]>>>;
type resolved = DeepResolvePromise<DoubleNested>; // Expect: string[]
