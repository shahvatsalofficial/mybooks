type Color = string | { r: number; g: number; b: number };

// Type Annotation (Loses shape granularity)
const redColor: Record<string, Color> = { primary: "red" };
// redColor.primary.toUpperCase(); // Compilation Error: Color could be the object representation

// Satisfies Operator (Enforces structure while retaining exact type assignments)
const blueColor = { primary: "blue" } satisfies Record<string, Color>;
blueColor.primary.toUpperCase(); // Compilation: SUCCESS (Knows exact type is string)
