from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch
from typing import List, Dict, Union
import logging

logger = logging.getLogger(__name__)

class NLPService:
    def __init__(self, model_name: str = "ProsusAI/finbert"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name).to(self.device)
            self.model.eval()
            self.pipeline = pipeline("sentiment-analysis", model=self.model, tokenizer=self.tokenizer, device=0 if torch.cuda.is_available() else -1)
            logger.info(f"FinBERT loaded on {self.device}")
        except Exception as e:
            logger.error(f"Failed to load FinBERT: {e}")
            self.pipeline = None

    def analyze(self, texts: Union[str, List[str]]) -> List[Dict]:
        if self.pipeline is None:
            return [{'label': 'neutral', 'score': 0.5} for _ in range(len(texts) if isinstance(texts, list) else 1)]
        if isinstance(texts, str):
            texts = [texts]
        results = self.pipeline(texts)
        for r in results:
            r['label'] = r['label'].lower()
        return results

nlp = NLPService()
