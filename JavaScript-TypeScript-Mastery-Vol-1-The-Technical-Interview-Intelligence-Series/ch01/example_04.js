Developer.prototype.role = "Software Engineer";
const manager = new Developer("Sarah", "Go");
manager.role = "Engineering Manager"; // Shadowing occurs here

console.log(manager.role); // "Engineering Manager" (read directly from instance)
console.log(Object.getPrototypeOf(manager).role); // "Software Engineer" (read from prototype)
