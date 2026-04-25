"""SQL generation service backed by a seq2seq Hugging Face model."""

from typing import List

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


class SQLGeneratorService:
    """Generate SQL from natural language and schema headers."""

    def __init__(
        self,
        model_id: str,
        max_input_length: int = 512,
        max_target_length: int = 128,
        num_beams: int = 4,
    ) -> None:
        """Load the text-to-SQL model once and reuse it for all requests."""
        self.max_input_length = max_input_length
        self.max_target_length = max_target_length
        self.num_beams = num_beams
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_id)
        self.model.eval()
        self.model.to(self.device)

    def build_input(self, question: str, headers: List[str]) -> str:
        """Construct the model input from question and flattened schema headers."""
        context = " | ".join(header.strip() for header in headers if header.strip())
        return f"question: {question.strip()} context: {context}"

    def generate_sql(self, question: str, headers: List[str]) -> str:
        """Generate SQL for a single question."""
        input_text = self.build_input(question, headers)
        inputs = self.tokenizer(
            input_text,
            return_tensors="pt",
            max_length=self.max_input_length,
            truncation=True,
        )
        inputs = {key: value.to(self.device) for key, value in inputs.items()}

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=self.max_target_length,
                num_beams=self.num_beams,
                early_stopping=True,
            )

        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
