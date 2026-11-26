// Permutations.ts
export type Permutation<T, K = T> =
    [T] extends [never]
        ? []
        : K extends K
            ? [K, ...Permutation<Exclude<T, K>>]
            : never;

type TestUnion = 'A' | 'B';
type Perms = Permutation<TestUnion>; // ['A', 'B'] | ['B', 'A']
