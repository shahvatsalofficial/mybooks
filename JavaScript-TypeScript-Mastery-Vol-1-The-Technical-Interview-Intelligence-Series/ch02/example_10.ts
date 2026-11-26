// 1. Pick: Select a sub-collection of keys
type CustomPick<T, K extends keyof T> = {
    [P in K]: T[P];
};

// 2. Omit: Filter out specific keys by using Exclude in mapping paths
type CustomOmit<T, K extends keyof any> = CustomPick<T, Exclude<keyof T, K>>;
