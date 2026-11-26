// Distributive Behavior (Standard)
type ExcludeUnion<T, U> = T extends U ? never : T;
type MixedUnion = string | number | boolean;
type Cleaned = ExcludeUnion<MixedUnion, boolean>; // string | number

// Preventing Auto-Distribution
// Wrapping generics in square brackets forces TS to evaluate the union as a single entity
type NonDistributiveCheck<T, U> = [T] extends [U] ? true : false;
