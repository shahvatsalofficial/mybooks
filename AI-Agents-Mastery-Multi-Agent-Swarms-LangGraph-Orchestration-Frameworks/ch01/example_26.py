# Exercise Solution Snippet:
class JuniorDeveloper:
    def __init__(self):
        self.attempts = 0
    def draft(self, critique: str = "") -> str:
        self.attempts += 1
        if self.attempts == 1:
            return "@app.get('/admin')\ndef admin(): return {'data': 'secret'}"
        return "@app.get('/admin')\ndef admin(token: str = Depends(verify_jwt)):\n    return {'data': 'secret'}"

class SeniorAuditor:
    def review(self, code: str) -> Tuple[bool, str]:
        if "Depends(verify_jwt)" not in code:
            return False, "REJECTED: Missing JWT authorization dependency injection."
        return True, "APPROVED: Authentication properly enforced."
