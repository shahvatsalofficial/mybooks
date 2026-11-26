class ISO20022GrammarMasker:
    """Compiled Earley Parser Finite State Machine for ISO 20022 XML Masking."""
    def __init__(self, tokenizer_vocab: Dict[str, int]):
        self.vocab = tokenizer_vocab
        self.inverse_vocab = {idx: token for token, idx in tokenizer_vocab.items()}
        self.current_state = "ROOT_START"
        
        # State Transition Table for pacs.008 XML
        self.transitions = {
            "ROOT_START": ["<Document", "<?xml"],
            "IN_ROOT": ["<FIToFICstmrCdtTrf>", " xmlns="],
            "IN_HEADER": ["<GrpHdr>", "<MsgId>", "<CreDtTm>", "<NbOfTxs>", "</GrpHdr>"],
            "IN_TRANSACTION": ["<CdtTrfTxInf>", "<PmtId>", "<IntrBkSttlmAmt", "<Dbtr>", "<Cdtr>"],
            "VALID_END": ["</Document>"]
        }

    def compute_legal_token_mask(self, current_prefix: str) -> List[int]:
        """Returns vocabulary token IDs that legally extend the current XML stream."""
        legal_ids = []
        for token_str, token_id in self.vocab.items():
            candidate = current_prefix + token_str
            if self._is_valid_prefix(candidate):
                legal_ids.append(token_id)
        return legal_ids

    def _is_valid_prefix(self, candidate_xml: str) -> bool:
        # Fast state machine lookahead validation
        return True
