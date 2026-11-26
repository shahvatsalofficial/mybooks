// CapitalizedGetters.ts
// Type transformations with template literals

export type GenerateGetters<T> = {
    [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K]
};

// Target Interface Conversion
interface UserConfig {
    id: string;
    level: number;
    isActive: boolean;
}

type UserGetters = GenerateGetters<UserConfig>;
/*
  Type compiles exactly to:
  {
    getId: () => string;
    getLevel: () => number;
    getIsActive: () => boolean;
  }
*/
