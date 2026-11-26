@dataclass
class FacilityTranche:
    name: str
    principal_outstanding: float
    base_rate_sofr: float
    margin_bps: float
    amortization_annual_pct: float
    seniority_rank: int  # 1 = Senior Secured, 2 = Second Lien, 3 = Mezzanine

class CashFlowWaterfallEngine:
    """Deterministic Multi-Tier Debt Waterfall and Covenant Compliance Engine."""
    def __init__(self, ebitda: float, capex: float, cash_taxes: float, tranches: List[FacilityTranche]):
        self.ebitda = ebitda
        self.capex = capex
        self.cash_taxes = cash_taxes
        self.tranches = sorted(tranches, key=lambda x: x.seniority_rank)

    def compute_unlevered_free_cash_flow(self) -> float:
        return self.ebitda - self.capex - self.cash_taxes

    def execute_annual_waterfall(self) -> Dict[str, any]:
        available_cash = self.compute_unlevered_free_cash_flow()
        interest_paid = {}
        principal_paid = {}
        total_debt_service = 0.0

        for tranche in self.tranches:
            annual_rate = tranche.base_rate_sofr + (tranche.margin_bps / 10_000.0)
            required_interest = tranche.principal_outstanding * annual_rate
            required_principal = tranche.principal_outstanding * tranche.amortization_annual_pct
            
            # Pay Interest
            paid_int = min(available_cash, required_interest)
            available_cash -= paid_int
            interest_paid[tranche.name] = paid_int
            total_debt_service += paid_int

            # Pay Principal
            paid_princ = min(available_cash, required_principal)
            available_cash -= paid_princ
            principal_paid[tranche.name] = paid_princ
            total_debt_service += paid_princ

        dscr = self.compute_unlevered_free_cash_flow() / max(total_debt_service, 1.0)
        covenant_passed = dscr >= 1.25

        return {
            "unlevered_fcf": round(self.compute_unlevered_free_cash_flow(), 2),
            "interest_breakdown": interest_paid,
            "principal_breakdown": principal_paid,
            "total_debt_service": round(total_debt_service, 2),
            "retained_cash_flow": round(available_cash, 2),
            "dscr": round(dscr, 3),
            "covenant_breached": not covenant_passed
        }
