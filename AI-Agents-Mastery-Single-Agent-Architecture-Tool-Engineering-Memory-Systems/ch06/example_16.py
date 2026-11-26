import re
from typing import List, Tuple

class EntityRelationExtractor:
    def extract_triplets(self, text_passage: str) -> List[Tuple[str, str, str]]:
        triplets = []
        # Pattern-matched extraction pipeline (in prod, backed by few-shot LLM prompts)
        patterns = [
            (r"([A-Za-z0-9_]+)\s+authenticates\s+via\s+([A-Za-z0-9_]+)", "AUTHENTICATES_VIA"),
            (r"([A-Za-z0-9_]+)\s+replicates\s+to\s+([A-Za-z0-9_]+)", "REPLICATES_TO"),
            (r"([A-Za-z0-9_]+)\s+deploys\s+on\s+([A-Za-z0-9_]+)", "DEPLOYS_ON")
        ]
        for pat, rel in patterns:
            for match in re.finditer(pat, text_passage, re.IGNORECASE):
                triplets.append((match.group(1), rel, match.group(2)))
        return triplets

extractor = EntityRelationExtractor()
text = "The AuthGateway authenticates via OktaSAML. The UserDatabase replicates to RedisCache."
triplets = extractor.extract_triplets(text)
print("Extracted GraphRAG Triplets:")
for s, r, o in triplets:
    print(f"  ({s}) --[{r}]--> ({o})")
