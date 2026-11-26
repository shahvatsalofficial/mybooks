# ptu_arbitrage_router.py
import time
from typing import Dict, Any

class PTUArbitrageManager:
    def __init__(self, ptu_capacity_tpm: int = 150000, high_watermark: float = 0.82):
        self.ptu_capacity_tpm = ptu_capacity_tpm
        self.high_watermark = high_watermark
        self.ewma_utilization = 0.0
        self.alpha = 0.25 # Smoothing factor
        self.last_update = time.time()
        self.current_window_tokens = 0

    def record_token_consumption(self, tokens: int):
        now = time.time()
        if now - self.last_update > 60.0:
            # Advance rolling window and calculate EWMA
            instantaneous_rate = self.current_window_tokens
            self.ewma_utilization = (self.alpha * instantaneous_rate) + ((1 - self.alpha) * self.ewma_utilization)
            self.current_window_tokens = 0
            self.last_update = now
            
        self.current_window_tokens += tokens

    def select_execution_target(self, priority: str, estimated_tokens: int) -> Dict[str, str]:
        projected_rate = self.ewma_utilization + self.current_window_tokens
        utilization_ratio = projected_rate / self.ptu_capacity_tpm
        
        # High-priority interactive requests always utilize reserved PTU unless 98% saturated
        if priority == "HIGH":
            if utilization_ratio < 0.98:
                return {"route": "AZURE_PTU_PRIMARY", "target_url": "https://corp-ptu.openai.azure.com"}
            else:
                return {"route": "SPILLOVER_PAYGO", "target_url": "https://corp-paygo-eastus.openai.azure.com"}
                
        # Background/batch traffic spills over when primary crosses 82% threshold
        if utilization_ratio >= self.high_watermark:
            return {"route": "SPILLOVER_PAYGO", "target_url": "https://corp-paygo-eastus.openai.azure.com"}
            
        return {"route": "AZURE_PTU_PRIMARY", "target_url": "https://corp-ptu.openai.azure.com"}
