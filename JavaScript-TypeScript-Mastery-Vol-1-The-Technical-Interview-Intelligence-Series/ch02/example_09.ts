// Completely remove readonly and optional flags from a deeply structured type
type OpaqueMutable<T> = {
    -readonly [P in keyof T]-?: OpaqueMutable<T[P]>;
};
