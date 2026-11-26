type UnpackPromiseDeep<T> = T extends Promise<infer U> 
    ? UnpackPromiseDeep<U> 
    : T;

// Testing deep lookup resolution
type NestedPromise = Promise<Promise<Promise<string[]>>>;
type CleanResolvedData = UnpackPromiseDeep<NestedPromise>; // Resolves directly to string[]!
