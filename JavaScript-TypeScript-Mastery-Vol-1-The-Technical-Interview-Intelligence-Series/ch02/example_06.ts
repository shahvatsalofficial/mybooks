type NakedIsString<T> = [T] extends [string] ? true : false;
type CheckedBlocked = NakedIsString<string | number>; // Resolves strictly to false!
