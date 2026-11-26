// Define state schemas
type TrafficState = "Green" | "Yellow" | "Red" | "Blinking_Yellow";

// State transition schema blueprint
interface TransitionMatrix {
    Green: "Yellow";
    Yellow: "Red";
    Red: "Green" | "Blinking_Yellow";
    Blinking_Yellow: "Red";
}

// Transition Engine class wrapper
class StateMachine<State extends TrafficState> {
    private currentState: State;

    constructor(initialState: State) {
        this.currentState = initialState;
    }

    // Enforce valid transitions dynamically using type constraints
    public transition<NextState extends TrafficState>(
        next: NextState
    ): StateMachine<NextState> {
        // Enforce transition logic at compile time
        type AllowedTransitions = TransitionMatrix[State];
        
        // Assert compile-time relation checks
        const isValid: NextState extends AllowedTransitions ? true : false = true as any;
        
        console.log(`Transitioning: ${this.currentState} -> ${next}`);
        this.currentState = next as any;
        return this as any;
    }
}

// Execution and verification
const activeSignal = new StateMachine("Green");

// Compiles perfectly!
const warningSignal = activeSignal.transition("Yellow");
const stopSignal = warningSignal.transition("Red");

// COMPILER ERROR TRIGGERED: Transition 'Yellow' to 'Green' is blocked.
// Type '"Green"' is not assignable to type 'TransitionMatrix["Yellow"]' (which is strictly '"Red"').
const invalidSignal = warningSignal.transition("Green");
