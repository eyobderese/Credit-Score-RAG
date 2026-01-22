"""
LLM Handler Module

Manages interaction with Groq API for response generation.
"""

from groq import Groq
from typing import List, Dict, Any, Optional
import logging
import time

logger = logging.getLogger(__name__)


class LLMHandler:
    """Handles LLM interactions for answer generation."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.1-70b-versatile",
        temperature: float = 0.1,
        max_tokens: int = 1024
    ):
        """
        Initialize LLM handler.
        
        Args:
            api_key: Groq API key
            model: Model identifier
            temperature: Response randomness (0-1, lower = more deterministic)
            max_tokens: Maximum tokens in response
        """
        self.client = Groq(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        logger.info(f"Initialized LLM handler with model: {model}")
    
    def generate_answer(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate an answer using retrieved context.
        
        Args:
            query: User's question
            context: Retrieved context from documents
            system_prompt: Optional custom system prompt
            
        Returns:
            Dictionary with answer and metadata
        """
        # Use default system prompt if not provided
        if system_prompt is None:
            system_prompt = self._get_default_system_prompt()
        
        # Construct user message
        user_message = self._construct_user_message(query, context)
        
        # Generate response
        try:
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            elapsed_time = time.time() - start_time
            
            answer = response.choices[0].message.content
            
            result = {
                "answer": answer,
                "model": self.model,
                "tokens_used": response.usage.total_tokens,
                "response_time": elapsed_time
            }
            
            logger.info(f"Generated answer in {elapsed_time:.2f}s using {result['tokens_used']} tokens")
            return result
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            raise
    
    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt for policy Q&A."""
        return """You are a precise and trustworthy Credit Policy Assistant. Your role is to answer questions about credit scoring, underwriting policies, and risk assessment guidelines.

CRITICAL RULES:
1. ONLY use information from the provided context documents
2. If the answer is not in the context, say "I don't have information about that in the policy documents"
3. Always cite specific policy documents when answering
4. When providing numerical thresholds (credit scores, percentages, amounts), quote them EXACTLY as in the source
5. If multiple sources have relevant information, mention all of them
6. Be concise but complete - include all relevant details
7. Never make assumptions or add information not in the context
8. If the context is ambiguous, acknowledge the ambiguity

ANSWER FORMAT:
- Start with a direct answer to the question
- Provide specific details and exact thresholds from the policies
- End with source citations in the format: (Source: [document name] - [section])
- If multiple conditions apply, list them clearly

Remember: Accuracy is paramount. An "I don't know" is better than an incorrect answer."""
    
    def _construct_user_message(self, query: str, context: str) -> str:
        """
        Construct the user message with query and context.
        
        Args:
            query: User's question
            context: Retrieved context
            
        Returns:
            Formatted user message
        """
        return f"""Based on the following policy documents, please answer this question:

QUESTION: {query}

POLICY CONTEXT:
{context}

Please provide a precise answer based only on the information above."""
    
    def validate_answer(
        self,
        answer: str,
        context: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Validate that the answer is grounded in the context.
        
        Args:
            answer: Generated answer
            context: Source context
            query: Original query
            
        Returns:
            Validation results with confidence score
        """
        validation_prompt = f"""Evaluate if the following answer is fully supported by the provided context.

QUESTION: {query}

ANSWER: {answer}

CONTEXT: {context}

Respond with:
1. GROUNDED: Yes/No (is the answer fully supported by the context?)
2. CONFIDENCE: 0-100 (how confident are you in this assessment?)
3. ISSUES: List any statements in the answer not found in the context (if any)

Format your response as JSON with keys: grounded, confidence, issues"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a quality assurance expert validating answer accuracy."},
                    {"role": "user", "content": validation_prompt}
                ],
                temperature=0.0,
                max_tokens=512
            )
            
            validation_text = response.choices[0].message.content
            
            # Parse validation (simple heuristic)
            grounded = "yes" in validation_text.lower()[:100]
            
            # Extract confidence if possible
            import re
            confidence_match = re.search(r'confidence["\s:]+(\d+)', validation_text, re.IGNORECASE)
            confidence = int(confidence_match.group(1)) if confidence_match else (90 if grounded else 50)
            
            return {
                "grounded": grounded,
                "confidence": confidence,
                "validation_response": validation_text
            }
            
        except Exception as e:
            logger.warning(f"Validation failed: {e}")
            return {
                "grounded": None,
                "confidence": 50,
                "validation_response": f"Validation error: {str(e)}"
            }
    
    def generate_with_validation(
        self,
        query: str,
        context: str
    ) -> Dict[str, Any]:
        """
        Generate answer and validate it.
        
        Args:
            query: User's question
            context: Retrieved context
            
        Returns:
            Dictionary with answer, validation, and metadata
        """
        # Generate answer
        result = self.generate_answer(query, context)
        
        # Validate answer
        validation = self.validate_answer(
            answer=result["answer"],
            context=context,
            query=query
        )
        
        result["validation"] = validation
        result["confidence_score"] = validation["confidence"]
        
        return result
