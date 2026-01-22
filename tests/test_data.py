"""
Test Data and Fixtures

Sample test data for evaluating the RAG system.
"""

# Sample queries with expected information
TEST_QUERIES = [
    {
        "question": "What is the minimum credit score for FHA loans?",
        "expected_keywords": ["580", "FHA", "credit score"],
        "expected_sources": ["credit_scoring_manual.md"],
        "category": "credit_score"
    },
    {
        "question": "What is the minimum credit score for conventional mortgages?",
        "expected_keywords": ["620", "conventional", "minimum"],
        "expected_sources": ["credit_scoring_manual.md"],
        "category": "credit_score"
    },
    {
        "question": "What are the maximum DTI ratios for conventional mortgages?",
        "expected_keywords": ["28%", "36%", "DTI", "conventional"],
        "expected_sources": ["risk_assessment_guidelines.md"],
        "category": "dti"
    },
    {
        "question": "What documentation is required for self-employed borrowers?",
        "expected_keywords": ["tax returns", "2 years", "self-employed", "1040"],
        "expected_sources": ["underwriting_policies.md", "risk_assessment_guidelines.md"],
        "category": "documentation"
    },
    {
        "question": "What are the reserve requirements for investment properties?",
        "expected_keywords": ["6 months", "investment", "reserves"],
        "expected_sources": ["risk_assessment_guidelines.md"],
        "category": "reserves"
    },
    {
        "question": "What is the maximum LTV for jumbo loans?",
        "expected_keywords": ["jumbo", "LTV"],
        "expected_sources": ["risk_assessment_guidelines.md"],
        "category": "ltv"
    },
    {
        "question": "What are the waiting periods after Chapter 7 bankruptcy?",
        "expected_keywords": ["48 months", "Chapter 7", "bankruptcy"],
        "expected_sources": ["credit_scoring_manual.md"],
        "category": "derogatory"
    },
    {
        "question": "What is the minimum down payment for FHA loans with a credit score of 580?",
        "expected_keywords": ["3.5%", "FHA", "580", "down payment"],
        "expected_sources": ["credit_scoring_manual.md"],
        "category": "down_payment"
    }
]

# Edge case queries
EDGE_CASE_QUERIES = [
    {
        "question": "What is the policy for cryptocurrency loans?",
        "expected_behavior": "Should indicate not found or prohibited",
        "category": "not_found"
    },
    {
        "question": "Tell me about car insurance requirements",
        "expected_behavior": "Should mention property insurance but may not be specific to auto",
        "category": "partial_match"
    }
]

# Sample document chunks for unit testing
SAMPLE_DOCUMENT_CHUNK = """
## Credit Score Requirements

### Personal Loans
- Minimum credit score: 580
- Preferred score: 670 or higher
- Exception threshold: 550 (requires manual underwriting)

### Mortgage Loans
- Conventional: Minimum 620
- FHA: Minimum 580 (with 3.5% down payment)
- FHA: Minimum 500 (with 10% down payment)
- Jumbo loans: Minimum 700
"""

SAMPLE_METADATA = {
    "source": "credit_scoring_manual.md",
    "title": "Credit Scoring Manual",
    "version": "3.2",
    "effective_date": "January 2026",
    "section": "Credit Score Requirements"
}
