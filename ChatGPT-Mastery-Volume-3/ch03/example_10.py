# multilingual_pii_analyzer.py — European & Asian PII Pipeline
from presidio_analyzer import AnalysisEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import TransformersNlpEngine

# Configure Multilingual Transformer Pipeline (supporting EN, DE, ES, FR)
NLP_CONFIGURATION = {
    "nlp_engine_name": "transformers",
    "models": [
        {"lang_code": "en", "model_name": {"spacy": "en_core_web_trf"}},
        {"lang_code": "de", "model_name": {"spacy": "de_core_news_lg"}},
        {"lang_code": "es", "model_name": {"spacy": "es_core_news_lg"}},
        {"lang_code": "fr", "model_name": {"spacy": "fr_core_news_lg"}}
    ]
}

def create_multilingual_engine() -> AnalysisEngine:
    nlp_engine = TransformersNlpEngine(models_config=NLP_CONFIGURATION["models"])
    registry = RecognizerRegistry()
    registry.load_predefined_recognizers(nlp_engine=nlp_engine)
    return AnalysisEngine(nlp_engine=nlp_engine, registry=registry)
