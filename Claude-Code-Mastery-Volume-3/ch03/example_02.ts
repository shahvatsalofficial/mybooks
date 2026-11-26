/**
 * Enterprise Token Economics & Context Compactor Engine
 * Package: @enterprise/token-finops
 * Author: Vatsal Shah, Lead Enterprise AI Architect
 */

import * as fs from 'fs';
import * as path from 'path';

export interface BudgetConfig {
    maxTaskTokens: number;
    maxTaskDollars: number;
    haikuDegradationThreshold: number; // 0.0 to 1.0 (e.g. 0.75)
    costPerMillionInputSonnet: number;
    costPerMillionCacheHitSonnet: number;
    costPerMillionInputHaiku: number;
}

export interface TurnMetrics {
    turnNumber: number;
    inputTokens: number;
    cacheHitTokens: number;
    outputTokens: number;
    costDollars: number;
}

export class ContextCompactor {
    private budget: BudgetConfig;
    private turnHistory: TurnMetrics[] = [];
    private totalSpend: number = 0;
    private totalTokens: number = 0;

    constructor(budget: BudgetConfig) {
        this.budget = budget;
    }

    /**
     * Layer 1: AST Skeletonizer for TypeScript / JavaScript Source Code
     */
    public skeletonizeSource(sourceCode: string, targetFunctionName: string): string {
        const lines = sourceCode.split('\n');
        let skeletonLines: string[] = [];
        let inTargetFunction = false;
        let braceDepth = 0;

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const trimmed = line.trim();

            // Detect target function boundary
            if (trimmed.includes(targetFunctionName)) {
                inTargetFunction = true;
                skeletonLines.push(line);
                braceDepth += (line.match(/{/g) || []).length;
                braceDepth -= (line.match(/}/g) || []).length;
                continue;
            }

            if (inTargetFunction) {
                skeletonLines.push(line);
                braceDepth += (line.match(/{/g) || []).length;
                braceDepth -= (line.match(/}/g) || []).length;
                if (braceDepth <= 0) {
                    inTargetFunction = false;
                    braceDepth = 0;
                }
                continue;
            }

            // Replace non-target function bodies with stubs
            if (trimmed.startsWith('public ') || trimmed.startsWith('private ') || trimmed.startsWith('function ')) {
                if (trimmed.includes('{')) {
                    const signature = line.substring(0, line.indexOf('{')).trim();
                    skeletonLines.push(`    ${signature} { /* [PRUNED_BODY_BY_AST_COMPACTOR] */ }`);
                } else {
                    skeletonLines.push(line);
                }
            } else if (trimmed.startsWith('import ') || trimmed.startsWith('export interface') || trimmed.startsWith('export type')) {
                // Always preserve imports, interfaces, and type declarations
                skeletonLines.push(line);
            }
        }

        return skeletonLines.join('\n');
    }

    /**
     * Layer 2: Circuit Breaker & Model Selection FSM
     */
    public recordTurnAndEvaluateCircuitBreaker(
        inputTokens: number, 
        cacheHitTokens: number, 
        outputTokens: number,
        isHaiku: boolean
    ): { allowExecution: boolean; recommendedModel: string; reason?: string } {
        const rateInput = isHaiku ? this.budget.costPerMillionInputHaiku : this.budget.costPerMillionInputSonnet;
        const rateHit = this.budget.costPerMillionCacheHitSonnet;

        const uncachedTokens = Math.max(0, inputTokens - cacheHitTokens);
        const turnCost = (uncachedTokens / 1_000_000 * rateInput) + 
                         (cacheHitTokens / 1_000_000 * rateHit) + 
                         (outputTokens / 1_000_000 * 15.00);

        this.totalSpend += turnCost;
        this.totalTokens += inputTokens;

        this.turnHistory.push({
            turnNumber: this.turnHistory.length + 1,
            inputTokens,
            cacheHitTokens,
            outputTokens,
            costDollars: turnCost
        });

        // Hard Circuit Breaker Trip
        if (this.totalSpend >= this.budget.maxTaskDollars) {
            return {
                allowExecution: false,
                recommendedModel: 'HALTED',
                reason: `HARD CIRCUIT BREAKER TRIPPED: Task spend ($${this.totalSpend.toFixed(2)}) exceeded ceiling ($${this.budget.maxTaskDollars.toFixed(2)})`
            };
        }

        if (this.totalTokens >= this.budget.maxTaskTokens) {
            return {
                allowExecution: false,
                recommendedModel: 'HALTED',
                reason: `HARD CIRCUIT BREAKER TRIPPED: Task token consumption (${this.totalTokens}) exceeded quota (${this.budget.maxTaskTokens})`
            };
        }

        // Half-Open State: Model Auto-Degradation
        const spendRatio = this.totalSpend / this.budget.maxTaskDollars;
        if (spendRatio >= this.budget.haikuDegradationThreshold) {
            return {
                allowExecution: true,
                recommendedModel: 'claude-3-5-haiku-20241022',
                reason: `DEGRADATION ACTIVE: Task spend at ${(spendRatio * 100).toFixed(1)}% of budget. Switching to Haiku to conserve quota.`
            };
        }

        return {
            allowExecution: true,
            recommendedModel: 'claude-3-5-sonnet-20241022'
        };
    }
}
