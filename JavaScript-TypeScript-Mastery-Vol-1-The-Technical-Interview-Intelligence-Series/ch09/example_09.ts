// DeepResolvePromise.ts
// Robust generic compiler type gymnastics

export type DeepResolvePromise<T> =
    T extends Promise<infer U>
        ? DeepResolvePromise<U>
        : T extends Array<infer V>
            ? Array<DeepResolvePromise<V>>
            : T extends (...args: any[]) => Promise<infer W>
                ? (...args: any[]) => DeepResolvePromise<W>
                : T;
