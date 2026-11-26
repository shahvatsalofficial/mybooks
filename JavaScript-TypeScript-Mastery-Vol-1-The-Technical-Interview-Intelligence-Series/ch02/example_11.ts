type Getters<T> = {
    [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
};

interface DiagnosticPayload {
    latencyMs: number;
    sensorCode: string;
}

type DiagnosticGetters = Getters<DiagnosticPayload>;
/*
Resolves to:
{
    getLatencyMs: () => number;
    getSensorCode: () => string;
}
*/
