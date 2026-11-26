export function arbitrateRuleConflict(higherTierRule: Rule, lowerTierRule: Rule): Rule {
  if (higherTierRule.priority < lowerTierRule.priority) {
    // Lower numerical value represents higher priority (P0 > P1 > P2)
    return higherTierRule;
  }
  return lowerTierRule;
}
