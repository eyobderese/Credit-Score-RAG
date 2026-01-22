PRD: Credit Scoring Policy Assistant (RAG-based)
1) Summary

Product name: Credit Scoring Policy Assistant
Type: Internal fintech knowledge assistant (QA)
Objective: Help employees quickly and correctly answer questions about internal credit policies and scoring rules by retrieving authoritative policy text and thresholds from approved documents—without guessing.

2) Problem statement

Credit policy and scoring rules are often spread across manuals, risk guidelines, and update memos. Teams waste time searching, and incorrect interpretation can lead to inconsistent decisions, audit issues, or risk exposure. A normal chatbot tends to “fill gaps” and hallucinate thresholds.

3) Goals & success criteria
Goals

Accurate policy Q&A grounded in approved source documents.

Zero-guessing behavior: if the answer isn’t in the corpus, the assistant says so and suggests next steps.

Fast retrieval of exact thresholds, definitions, and exceptions.

Audit-friendly traceability (citations + policy versioning).

Success criteria (measurable)

Policy accuracy: ≥ 95% on a curated evaluation set (answer must match policy intent and numeric thresholds).

Hallucination rate: ≤ 2% (answers containing claims not supported by sources).

Citation coverage: ≥ 98% of answers include at least one relevant citation snippet.

Time-to-answer: median < 10 seconds end-to-end for typical questions.

User satisfaction: ≥ 4.3/5 among target users after pilot.

4) Non-goals

Making automated credit decisions or scoring borrowers in production.

Customer-facing support (MVP is internal-only).

Editing policy documents or creating new policy content.

Replacing legal/compliance review workflows.

5) Target users & personas

Risk Analyst / Policy Owner: needs precise thresholds, definitions, and change history.

Underwriter / Credit Ops: needs quick interpretation of “what applies” and exceptions.

Product/Engineering: needs rules clarity for implementation and edge cases.

Audit/Compliance: needs traceability—“show me where this came from.”

New hires: needs onboarding-friendly explanations with links to sources.

6) Key user stories

As an underwriter, I ask: “What’s the minimum score cutoff for Product X?” and get the exact threshold with citation and policy version.

As a risk analyst, I ask: “How do we treat thin-file applicants?” and get the rule plus exceptions and the section references.

As engineering, I ask: “Is DTI calculated pre- or post-housing?” and get the definition used internally with an example if documented.

As audit, I ask: “Which document authorizes the exception for segment Y?” and get the specific clause and date.

7) Product experience & UX requirements
Answer format (must-have)

Direct answer first (1–3 sentences).

Citations: list of linked source snippets with document name + section + page (or heading).

Policy metadata: policy name, version/effective date, and applicability (if the doc specifies product/segment).

Confidence behavior:

If insufficient grounding → respond: “Not found in the provided policy docs” + suggest where to look / who owns it.

Never invent numeric thresholds.

Interaction patterns

Follow-up questions supported (“Does this apply to self-employed?”).

Optional “Show more context” to expand retrieved excerpts.

“Compare versions” (if multiple versions exist) for policy changes.

8) Functional requirements
8.1 Core Q&A (MVP)

Natural language questions about:

Score thresholds and cutoffs

Risk bands and mapping rules

Exceptions and override conditions

Definitions (e.g., DTI, utilization)

Eligibility rules tied to score segments

Answers must be grounded in retrieved sources.

8.2 Retrieval & grounding (MVP)

Document ingestion for:

Credit manuals

Risk guidelines

Policy updates/memos (mock/anonymized for now)

Chunking strategy supports:

Tables (threshold matrices)

Bullet lists

Section headings and hierarchy

Retrieval must support filtering by:

Product (e.g., Product X)

Region/jurisdiction (if present)

Effective date/version

Document type (manual vs memo)

8.3 Citations & traceability (MVP)

Every answer includes:

At least one citation for each key claim

Exact threshold citations for any numeric value

“Open source” action to view the surrounding section context.

8.4 Access control (MVP)

Role-based access (RBAC):

Users only retrieve documents they are permitted to see.

Logging of queries and citations for audit (with redaction rules).

8.5 Admin & maintenance (Phase 2)

Policy owners can:

Upload new versions

Deprecate old versions

Tag documents (product/segment/effective date)

Change detection and alerts: “Policy updated—answers may differ.”

9) Data requirements
Data sources (initial)

Mock/anonymized policy manuals and risk guidelines.

Optional: structured rule sheets (CSV) for thresholds to reduce table-parsing ambiguity.

Data handling rules

No PII in the corpus (MVP).

Document versioning required (effective date + revision identifier).

Maintain a “source of truth” registry: doc name, owner, approval status, effective date.

10) System design (high level)
RAG pipeline

Ingest documents → extract text + tables + metadata.

Normalize (headings, section IDs, table structure).

Chunk with table-aware logic.

Embed + index for semantic retrieval, plus lexical search for exact thresholds.

Retrieve top-k with metadata filters.

Generate answer constrained to retrieved content.

Validate: ensure numeric claims appear in citations; otherwise refuse or re-retrieve.

Guardrails

“No source, no answer” rule for thresholds and policy directives.

Hallucination detection heuristic: if answer contains numbers not present in retrieved text → block and retry.

Clear refusal template for out-of-corpus questions.

11) Evaluation plan
Offline evaluation (before pilot)

Build a golden Q&A set:

Threshold questions (tables/matrices)

Exception edge cases

Definitions and calculation rules

Version-sensitive questions

Metrics:

Policy accuracy (human-scored or rubric)

Exact match for thresholds (numeric correctness)

Groundedness (all claims supported by citations)

Hallucination rate

Retrieval recall for key sections

Online evaluation (pilot)

Track:

Answer acceptance rate

Citation click-through

User feedback (“correct/incorrect” + reason)

Top failure modes (missing doc, wrong version, ambiguous question)

12) Security, privacy, and compliance

RBAC enforced at retrieval-time (not just UI).

Audit logs: user, timestamp, question, documents cited, response ID.

Redaction/PII controls (even if MVP is mock): prevent accidental leakage if real docs later include sensitive data.

Data retention policy for logs (configurable).

Clear disclaimer: “Informational—policy source citations included; consult policy owner for overrides.”

13) Rollout plan
MVP (4–8 weeks typical, adjustable)

Ingest mock/anonymized manuals + guidelines

Web UI or Slack/Teams bot interface

Q&A with citations + version display

Offline evaluation suite + baseline report

Pilot (internal)

10–30 users across Risk + Underwriting + Engineering

Weekly review of incorrect answers and missing documentation

Phase 2

Admin console for policy owners

Version comparison, change alerts

Deeper structured extraction for tables and formulas

14) Risks & mitigations

Table/threshold parsing errors → store thresholds in structured form where possible; add numeric grounding checks.

Wrong version retrieved → require effective date filtering and display version prominently.

Ambiguous questions → ask targeted follow-ups (product, segment, effective date) while still attempting retrieval.

Over-trust by users → strong UI cues + citations + refusal behavior.

15) Open questions (to finalize scope)

Which products/regions are in scope for MVP?

Do we need support for policy “draft” vs “approved” states?

What is the preferred interface: Slack/Teams, internal web app, or API-first?

Any hard latency SLOs and concurrency expectations?

Who is the policy owner group for doc approvals and tagging?

If you tell me the preferred interface (Slack/web/API) and whether policies have multiple versions active by region/product, I can tailor the PRD’s scope, workflows, and acceptance criteria more tightly.