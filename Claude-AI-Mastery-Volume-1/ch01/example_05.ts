import { Anthropic } from '@anthropic-ai/sdk';

export interface RouteDecision {
  selectedModel: 'claude-3-5-haiku-20241022' | 'claude-3-5-sonnet-20241022' | 'claude-3-opus-20240229';
  reasoningComplexityScore: number; // 0.0 - 1.0
  estimatedInputTokens: number;
  routingRationale: string;
  cacheControlEnabled: boolean;
}

export class EnterpriseModelRouter {
  private client: Anthropic;
  private readonly CODE_KEYWORDS = ['def ', 'function', 'class ', 'import ', 'SELECT ', 'JOIN ', 'curl ', 'apiVersion'];
  private readonly DEEP_ANALYSIS_KEYWORDS = ['forensic', 'statutory', 'counterfactual', 'constitutional', 'philosophical', 'synthesis'];

  constructor(apiKey: string) {
    this.client = new Anthropic({ apiKey });
  }

  public evaluateRoute(prompt: string, hasImages: boolean = false): RouteDecision {
    const charCount = prompt.length;
    const estimatedTokens = Math.ceil(charCount / 3.8);
    let complexityScore = 0.1;

    // Multimodal inputs automatically route to Sonnet 3.5 for world-class visual perception
    if (hasImages) {
      return {
        selectedModel: 'claude-3-5-sonnet-20241022',
        reasoningComplexityScore: 0.85,
        estimatedInputTokens: estimatedTokens + 1600, // Account for image patch tiles
        routingRationale: 'Multimodal input detected; routed to Claude 3.5 Sonnet for vision parsing.',
        cacheControlEnabled: true
      };
    }

    // Check for heavy software engineering signatures
    const codeMatchCount = this.CODE_KEYWORDS.filter(kw => prompt.includes(kw)).length;
    if (codeMatchCount >= 2 || prompt.includes('```')) {
      complexityScore += 0.5;
    }

    // Check for deep qualitative synthesis signatures
    const deepMatchCount = this.DEEP_ANALYSIS_KEYWORDS.filter(kw => prompt.toLowerCase().includes(kw)).length;
    if (deepMatchCount >= 2) {
      complexityScore += 0.4;
    }

    // Long context adjustment
    if (estimatedTokens > 25000) {
      complexityScore += 0.2;
    }

    complexityScore = Math.min(1.0, complexityScore);

    // Decision Logic Matrix
    if (complexityScore >= 0.8 && deepMatchCount >= 2 && codeMatchCount === 0) {
      return {
        selectedModel: 'claude-3-opus-20240229',
        reasoningComplexityScore: complexityScore,
        estimatedInputTokens: estimatedTokens,
        routingRationale: 'Deep qualitative ambiguity and statutory synthesis; routed to Claude 3 Opus.',
        cacheControlEnabled: estimatedTokens > 2048
      };
    } else if (complexityScore >= 0.4 || codeMatchCount >= 1) {
      return {
        selectedModel: 'claude-3-5-sonnet-20241022',
        reasoningComplexityScore: complexityScore,
        estimatedInputTokens: estimatedTokens,
        routingRationale: 'High-density logic, code transformation, or architectural design; routed to Sonnet 3.5.',
        cacheControlEnabled: estimatedTokens > 2048
      };
    } else {
      return {
        selectedModel: 'claude-3-5-haiku-20241022',
        reasoningComplexityScore: complexityScore,
        estimatedInputTokens: estimatedTokens,
        routingRationale: 'Transactional classification, entity extraction, or edge query; routed to Haiku 3.5.',
        cacheControlEnabled: estimatedTokens > 2048
      };
    }
  }

  public async executeRoutedInference(
    prompt: string,
    systemInstruction: string,
    hasImages: boolean = false
  ): Promise<{ text: string; decision: RouteDecision; latencyMs: number }> {
    const decision = this.evaluateRoute(prompt, hasImages);
    const startTime = Date.now();

    const response = await this.client.messages.create({
      model: decision.selectedModel,
      max_tokens: 4096,
      system: systemInstruction,
      messages: [{ role: 'user', content: prompt }]
    });

    const latencyMs = Date.now() - startTime;
    const textOutput = response.content[0].type === 'text' ? response.content[0].text : '';

    return {
      text: textOutput,
      decision,
      latencyMs
    };
  }
}
