"""LLM service for generating responses using OpenAI."""

from openai import OpenAI

from src.utils.exceptions import LLMServiceError


class LLMService:
    """Service for generating text completions using LLM."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.1,
        max_tokens: int = 1000,
    ):
        """
        Initialize LLM service.

        Args:
            api_key: OpenAI API key
            model: Model to use for completions
            temperature: Temperature for generation (lower = more deterministic)
            max_tokens: Maximum tokens in response
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate_answer(self, prompt: str) -> tuple[str, int]:
        """
        Generate answer from prompt.

        Args:
            prompt: Complete prompt including system instructions and question

        Returns:
            Tuple of (response_text, tokens_used)

        Raises:
            LLMServiceError: If generation fails
        """
        if not prompt or not prompt.strip():
            raise LLMServiceError("No se puede generar respuesta con prompt vacío")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            answer_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens

            return answer_text, tokens_used

        except Exception as e:
            raise LLMServiceError(f"Error al generar respuesta del LLM: {str(e)}")
