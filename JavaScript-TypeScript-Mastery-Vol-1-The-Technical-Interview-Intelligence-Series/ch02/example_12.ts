type FilterByValueType<Source, TargetType> = {
    [K in keyof Source as Source[K] extends TargetType ? K : never]: Source[K];
};

interface ComplexSystemNode {
    id: string;
    throughputMb: number;
    operational: boolean;
    logsDirectory: string;
}

type StringPropertiesOnly = FilterByValueType<ComplexSystemNode, string>;
/*
Resolves strictly to:
{
    id: string;
    logsDirectory: string;
}
*/
