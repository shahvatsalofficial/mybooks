// Vulnerable Canvas Loop (Instantiates fresh object pointers every frame, causing GC stutters)
function renderLeakyParticles(ctx, count) {
    for (let i = 0; i < count; i++) {
        const particle = { x: Math.random() * 100, y: Math.random() * 100 }; // Leaks memory allocations!
        ctx.fillRect(particle.x, particle.y, 2, 2);
    }
}

// Hardened Canvas Loop (Object Pool Pattern)
// Pre-allocates objects in a static array and modifies properties in-place, achieving 0 GC impact.
class HardenedParticlePool {
    constructor(size) {
        this.xArray = new Float32Array(size);
        this.yArray = new Float32Array(size);
        this.size = size;
        this.init();
    }
    init() {
        for (let i = 0; i < this.size; i++) {
            this.xArray[i] = Math.random() * 800;
            this.yArray[i] = Math.random() * 600;
        }
    }
    render(ctx) {
        ctx.fillStyle = "#8B5CF6";
        for (let i = 0; i < this.size; i++) {
            ctx.fillRect(this.xArray[i], this.yArray[i], 2, 2);
        }
    }
}
