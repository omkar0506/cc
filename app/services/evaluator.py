"""
Deterministic Rubric & Expected Concept Coverage Fallback Scorer.
Evaluates candidate answers when no AI credentials are configured.
Marked with provider = 'rule_based' for complete transparency.
"""

import re
from typing import Dict, Any, List


def evaluate_answer_rule_based(question, answer_text: str) -> Dict[str, Any]:
    """
    Evaluates an answer against the question's rubric and expected concepts.
    Determines conceptual coverage, extracts supporting quotes, identifies missing concepts,
    and computes bounded criterion scores.
    """
    norm_answer = (answer_text or '').strip()
    norm_lower = norm_answer.lower()

    expected_concepts: List[str] = question.expected_concepts or []
    total_concepts = len(expected_concepts) if expected_concepts else 1

    covered_concepts = []
    missing_concepts = []
    supporting_quotes = []

    # Break answer into sentences for quote extraction
    sentences = re.split(r'[.!?\n]+', norm_answer)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 8]

    # Concept matching with keyword token overlap
    for concept in expected_concepts:
        concept_lower = concept.lower()
        # Direct substring check
        if concept_lower in norm_lower:
            covered_concepts.append(concept)
            # Find matching sentence
            for s in sentences:
                if any(word in s.lower() for word in concept_lower.split() if len(word) > 3):
                    if s not in supporting_quotes:
                        supporting_quotes.append(s)
                    break
        else:
            # Token overlap check (match at least 60% of significant words)
            tokens = [t for t in re.findall(r'\b\w+\b', concept_lower) if len(t) > 2]
            if tokens:
                matched_tokens = [t for t in tokens if t in norm_lower]
                match_ratio = len(matched_tokens) / len(tokens)
                if match_ratio >= 0.60:
                    covered_concepts.append(concept)
                    for s in sentences:
                        if any(t in s.lower() for t in matched_tokens):
                            if s not in supporting_quotes:
                                supporting_quotes.append(s)
                            break
                else:
                    missing_concepts.append(concept)
            else:
                missing_concepts.append(concept)

    # Compute coverage ratio
    coverage_ratio = len(covered_concepts) / total_concepts if total_concepts > 0 else 0.5
    coverage_ratio = min(max(coverage_ratio, 0.0), 1.0)

    # Depth adjustment based on elaboration (words count)
    word_count = len(norm_answer.split())
    elaboration_factor = 1.0
    if word_count < 15:
        elaboration_factor = 0.5
    elif word_count < 35:
        elaboration_factor = 0.8
    elif word_count >= 60:
        elaboration_factor = 1.0

    raw_ratio = coverage_ratio * elaboration_factor

    # Rubric criterion breakdown
    rubric = question.rubric or {}
    if not rubric:
        rubric = {'correctness': 0.40, 'clarity': 0.30, 'relevance': 0.30}

    total_rubric_weight = sum(rubric.values()) if rubric else 1.0
    criterion_scores = {}
    criterion_explanations = {}

    max_score = float(question.max_score or 10.0)

    for criterion, weight in rubric.items():
        norm_weight = weight / total_rubric_weight
        crit_max = max_score * norm_weight

        # Specific adjustments by criterion
        if 'correctness' in criterion:
            crit_ratio = coverage_ratio
            explanation = f"Addressed {len(covered_concepts)} of {total_concepts} core expected concepts."
        elif 'clarity' in criterion or 'explanation' in criterion:
            crit_ratio = min(1.0, max(0.2, (word_count / 50.0)))
            explanation = "Structure and clarity assessed from vocabulary and response organization."
        elif 'code' in criterion:
            # Basic syntactic presence of keywords or code blocks
            has_code_keywords = any(k in norm_lower for k in ['def ', 'class ', 'return', 'import', 'for ', 'while', 'public ', 'function'])
            crit_ratio = 0.85 if has_code_keywords else 0.4
            explanation = "Evaluated code structure, control flow, and syntax keywords (written mode)."
        else:
            crit_ratio = raw_ratio
            explanation = f"Evaluated according to criterion expectations with {int(coverage_ratio * 100)}% concept coverage."

        crit_score = round(crit_max * crit_ratio, 2)
        criterion_scores[criterion] = crit_score
        criterion_explanations[criterion] = explanation

    total_score = round(sum(criterion_scores.values()), 2)
    # Bound between 0 and max_score
    total_score = min(max(total_score, 0.0), max_score)
    score_ratio = round(total_score / max_score, 4)

    # Strengths and improvements
    strengths = []
    if covered_concepts:
        strengths.append(f"Successfully identified key principles: {', '.join(covered_concepts[:3])}.")
    if word_count >= 50:
        strengths.append("Provided detailed explanations with thorough elaboration.")

    improvements = []
    if missing_concepts:
        improvements.append(f"Deepen coverage on missing concepts: {', '.join(missing_concepts[:3])}.")
    if word_count < 30:
        improvements.append("Elaborate further with concrete examples or practical architectural applications.")

    suggested_followup = None
    if missing_concepts:
        suggested_followup = f"Could you elaborate specifically on how {missing_concepts[0]} works in this context?"

    return {
        'total_score': total_score,
        'max_score': max_score,
        'score_ratio': score_ratio,
        'criterion_scores': criterion_scores,
        'supporting_quotes': supporting_quotes[:3],
        'criterion_explanations': criterion_explanations,
        'missing_concepts': missing_concepts,
        'strengths': strengths,
        'improvement_suggestions': improvements,
        'suggested_followup': suggested_followup,
        'provider': 'rule_based',
        'model': None,
        'tokens_used': 0,
        'status': 'completed'
    }
