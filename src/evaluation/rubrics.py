"""Rubric definitions for Scripture RAG evaluation.

Each rubric defines criteria for evaluating a single dimension of RAG response quality.
All rubrics follow chain-of-thought format: evidence first, then verdict.

Dimensions:
1. factual_accuracy - Answer matches scripture content
2. citation_accuracy - Citations support claims made
3. completeness - Covers question fully
4. source_relevance - Uses relevant vs tangential scripture
5. theological_appropriateness - Doctrinally sound interpretation
"""

from dataclasses import dataclass
from enum import Enum


class Dimension(Enum):
    """Evaluation dimensions for scripture RAG responses."""

    FACTUAL_ACCURACY = "factual_accuracy"
    CITATION_ACCURACY = "citation_accuracy"
    COMPLETENESS = "completeness"
    SOURCE_RELEVANCE = "source_relevance"
    THEOLOGICAL_APPROPRIATENESS = "theological_appropriateness"


@dataclass
class Rubric:
    """Single evaluation rubric with judge prompt template."""

    dimension: Dimension
    description: str
    prompt_template: str
    weight: float = 1.0

    def build_prompt(
        self,
        question: str,
        answer: str,
        citations: list[dict],
        retrieved_context: str = "",
    ) -> str:
        """Build the judge prompt for this rubric.

        Args:
            question: User's original question
            answer: RAG system's generated answer
            citations: List of citations with 'reference' and 'text' keys
            retrieved_context: Full retrieved context (for source_relevance)

        Returns:
            Formatted prompt for the judge LLM
        """
        citations_str = self._format_citations(citations)

        return self.prompt_template.format(
            question=question,
            answer=answer,
            citations=citations_str,
            retrieved_context=retrieved_context,
        )

    def _format_citations(self, citations: list[dict]) -> str:
        """Format citations for inclusion in prompt."""
        if not citations:
            return "None provided"

        lines = []
        for c in citations:
            ref = c.get("reference", "Unknown")
            text = c.get("text", "")
            lines.append(f"- {ref}: \"{text}\"")
        return "\n".join(lines)


# =============================================================================
# RUBRIC DEFINITIONS
# =============================================================================

RUBRICS = {
    Dimension.FACTUAL_ACCURACY: Rubric(
        dimension=Dimension.FACTUAL_ACCURACY,
        description="Answer matches scripture content without distortion",
        weight=1.5,  # Higher weight - factual accuracy is critical
        prompt_template="""You are evaluating a scripture-based answer for factual accuracy.

## Rubric: Factual Accuracy
The answer must accurately represent what the scriptures actually say. Claims should be verifiable in the cited verses.

FAIL conditions:
- Misquoting or paraphrasing that changes meaning
- Claiming scripture says something it doesn't
- Attributing statements to wrong speakers or books
- Inventing content not in the cited verses

## User Question
{question}

## RAG Answer
{answer}

## Citations Provided
{citations}

## Evaluation
1. Identify specific claims made in the answer
2. Check each claim against the cited scripture text
3. Note any misrepresentations or fabrications

Respond with EXACTLY one of these formats:
PASS: [1-sentence summary of why answer is factually accurate]
FAIL: [Quote the specific inaccuracy and explain the discrepancy]
""",
    ),
    Dimension.CITATION_ACCURACY: Rubric(
        dimension=Dimension.CITATION_ACCURACY,
        description="Each claim has supporting citation",
        weight=1.0,
        prompt_template="""You are evaluating citation quality in a scripture answer.

## Rubric: Citation Accuracy
Every substantive claim about scripture should have a supporting citation. Citations should actually support the claims they're attached to.

FAIL conditions:
- Claims without citations
- Citations that don't support the attached claim
- Missing citations for key points
- Wrong scripture references

## User Question
{question}

## RAG Answer
{answer}

## Citations Provided
{citations}

## Evaluation
1. List the main claims made in the answer
2. Check if each claim has a supporting citation
3. Verify the citation actually supports the claim (not just vaguely related)

Respond with EXACTLY one of these formats:
PASS: All claims properly cited with supporting verses
FAIL: [Identify uncited claims or citations that don't support their claims]
""",
    ),
    Dimension.COMPLETENESS: Rubric(
        dimension=Dimension.COMPLETENESS,
        description="Answer covers all aspects of the question",
        weight=1.0,
        prompt_template="""You are evaluating answer completeness.

## Rubric: Completeness
The answer should address all parts of the user's question. For simple questions, a focused answer is fine. For multi-part questions, each part should be addressed.

FAIL conditions:
- Ignoring part of a multi-part question
- Only partially answering what was asked
- Missing obvious aspects the question implies

PASS even if:
- Answer is concise but complete
- Some peripheral aspects aren't covered

## User Question
{question}

## RAG Answer
{answer}

## Evaluation
1. Break down the question into its component parts/aspects
2. Check if the answer addresses each component
3. Determine if anything critical was missed

Respond with EXACTLY one of these formats:
PASS: Answer addresses all aspects of the question
FAIL: [Identify what aspect of the question was not addressed]
""",
    ),
    Dimension.SOURCE_RELEVANCE: Rubric(
        dimension=Dimension.SOURCE_RELEVANCE,
        description="Uses directly relevant scriptures, not tangential ones",
        weight=1.0,
        prompt_template="""You are evaluating source selection in a scripture answer.

## Rubric: Source Relevance
The answer should cite the most directly relevant scriptures for the topic. Primary sources are preferred over tangentially related verses.

FAIL conditions:
- Using only peripherally related verses
- Missing obvious primary sources on the topic
- Citing verses that barely relate to the question
- Cherry-picking obscure verses when canonical ones exist

PASS even if:
- Not every possible relevant verse is cited
- Answer focuses on a few highly relevant verses

## User Question
{question}

## RAG Answer
{answer}

## Citations Provided
{citations}

## Retrieved Context (full search results)
{retrieved_context}

## Evaluation
1. Assess how directly the cited verses relate to the question
2. Consider if there are obviously more relevant verses that should have been used
3. Determine if the sources meaningfully address the question

Respond with EXACTLY one of these formats:
PASS: Cited scriptures are directly relevant to the question
FAIL: [Explain why the sources are tangential or what key sources are missing]
""",
    ),
    Dimension.THEOLOGICAL_APPROPRIATENESS: Rubric(
        dimension=Dimension.THEOLOGICAL_APPROPRIATENESS,
        description="Doctrinally sound, not speculative beyond text",
        weight=1.0,
        prompt_template="""You are evaluating theological appropriateness of a scripture answer.

## Rubric: Theological Appropriateness
The answer should let scripture speak for itself without imposing interpretations, speculation, or doctrines not found in the text. Avoid denominational bias.

FAIL conditions:
- Speculating beyond what scripture explicitly says
- Imposing specific denominational interpretations as fact
- Drawing conclusions the text doesn't support
- Adding theological claims not grounded in cited verses

PASS conditions:
- Sticks to what scripture explicitly states
- Acknowledges when interpretation is uncertain
- Presents multiple valid interpretations if they exist
- Lets the text speak for itself

## User Question
{question}

## RAG Answer
{answer}

## Citations Provided
{citations}

## Evaluation
1. Check if answer claims are grounded in cited scripture
2. Look for speculation or interpretation presented as fact
3. Assess if the answer appropriately represents what the text says

Respond with EXACTLY one of these formats:
PASS: Answer stays grounded in scripture text without overreaching
FAIL: [Identify specific speculation or unsupported theological claims]
""",
    ),
}


def get_rubric(dimension: Dimension) -> Rubric:
    """Get rubric by dimension."""
    return RUBRICS[dimension]


def get_all_rubrics() -> list[Rubric]:
    """Get all rubric definitions."""
    return list(RUBRICS.values())


def calculate_weighted_score(results: dict[Dimension, bool]) -> float:
    """Calculate weighted pass rate from dimension results.

    Args:
        results: Dict mapping dimension to pass/fail (True/False)

    Returns:
        Weighted score between 0.0 and 1.0
    """
    total_weight = 0.0
    weighted_sum = 0.0

    for dimension, passed in results.items():
        rubric = RUBRICS[dimension]
        total_weight += rubric.weight
        if passed:
            weighted_sum += rubric.weight

    if total_weight == 0:
        return 0.0
    return weighted_sum / total_weight
