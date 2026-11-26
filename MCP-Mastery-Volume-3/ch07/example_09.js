// solution_build_drr.js — Solution for Exercise 2: Deficit Round Robin Scheduler
class DRRDispatcher {
  constructor() {
    this.quantum = { GOLD: 10, SILVER: 5, BRONZE: 1 };
    this.deficitCounter = { GOLD: 0, SILVER: 0, BRONZE: 0 };
    this.queues = { GOLD: [], SILVER: [], BRONZE: [] };
    this.tiers = ['GOLD', 'SILVER', 'BRONZE'];
  }

  enqueue(tier, taskName, cost = 1) {
    this.queues[tier].push({ taskName, cost });
  }

  dispatchBatch(maxDispatches = 16) {
    const executed = [];
    let dispatches = 0;

    while (dispatches < maxDispatches) {
      let anyProcessed = false;

      for (const tier of this.tiers) {
        if (this.queues[tier].length === 0) {
          this.deficitCounter[tier] = 0;
          continue;
        }

        // Add quantum credit
        this.deficitCounter[tier] += this.quantum[tier];

        while (this.queues[tier].length > 0 && this.deficitCounter[tier] >= this.queues[tier][0].cost) {
          const task = this.queues[tier].shift();
          this.deficitCounter[tier] -= task.cost;
          executed.push(`[${tier}] ${task.taskName} (cost: ${task.cost})`);
          dispatches++;
          anyProcessed = true;
          if (dispatches >= maxDispatches) break;
        }

        if (dispatches >= maxDispatches) break;
      }

      // If no tasks were processed across all tiers, queues are empty
      if (!anyProcessed) break;
    }

    return executed;
  }
}

// Verification Test Case
const scheduler = new DRRDispatcher();
for (let i = 1; i <= 20; i++) scheduler.enqueue('GOLD', `Gold-Task-${i}`, 1);
for (let i = 1; i <= 20; i++) scheduler.enqueue('SILVER', `Silver-Task-${i}`, 1);
for (let i = 1; i <= 20; i++) scheduler.enqueue('BRONZE', `Bronze-Task-${i}`, 1);

const batch = scheduler.dispatchBatch(16);
console.log('Dispatched Batch of 16 tasks:');
batch.forEach(item => console.log('  ', item));
