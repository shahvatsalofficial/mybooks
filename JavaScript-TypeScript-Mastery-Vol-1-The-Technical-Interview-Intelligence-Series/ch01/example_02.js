function Developer(name, language) {
    this.name = name;
    this.language = language;
}

Developer.prototype.writeCode = function() {
    return `${this.name} is writing ${this.language}`;
};

const lead = new Developer("Vatsal", "TypeScript");
