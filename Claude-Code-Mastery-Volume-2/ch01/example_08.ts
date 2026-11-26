// Architectural Anti-Pattern (Fatally Corrupts STDIO Transport):
console.log("Connected to PostgreSQL database cluster on port 5432"); // Written to stdout! Crash!

// Production Architecture Standard:
console.error("[INFO] Connected to PostgreSQL database cluster on port 5432"); // Written to stderr! Safe!
process.stderr.write("[DEBUG] Connection pool initialized with 10 workers\n");
