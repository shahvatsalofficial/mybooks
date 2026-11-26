// UnpackPromise.ts
export type Unpack<T> = T extends Promise<infer U> ? U : T;
