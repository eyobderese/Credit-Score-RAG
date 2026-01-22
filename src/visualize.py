import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless rendering
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

with open("evaluation_results.json") as f:
    data = json.load(f)

labeled = pd.DataFrame(data["results"])
summary = data["metrics"]
unlabeled = pd.DataFrame(data.get("unlabeled", {}).get("probes", []))
coverage = data.get("coverage", {})

sns.set_theme(style="whitegrid", context="talk")
# Create a 2x3 grid of plots with a text panel
fig, axes = plt.subplots(2, 3, figsize=(22, 12))

# Precision@K
ax = axes[0, 0]
sns.barplot(ax=ax, x=["P@1", "P@3", "P@5"], y=[
    summary.get("avg_precision_at_1", 0),
    summary.get("avg_precision_at_3", 0),
    summary.get("avg_precision_at_5", 0)
])
ax.set_title("Precision@K")
ax.set_ylim(0, 1)

# MRR / NDCG
ax = axes[0, 1]
sns.barplot(ax=ax, x=["MRR", "NDCG@5"], y=[
    summary.get("avg_mrr", 0),
    summary.get("avg_ndcg_at_5", 0)
])
ax.set_ylim(0, 1)
ax.set_title("Ranking Metrics")

# Faithfulness and relevancy
ax = axes[0, 2]
sns.barplot(ax=ax, x=["Faithfulness", "Relevancy"], y=[
    summary.get("avg_faithfulness_confidence", 0),
    summary.get("avg_answer_relevancy", 0)
])
ax.set_ylim(0, 100)
ax.set_title("LLM Judging Metrics")

# Confidence vs retrieved count
ax = axes[1, 0]
if not labeled.empty:
    sns.scatterplot(ax=ax, data=labeled, x="retrieved_count", y="confidence")
ax.set_title("Confidence vs Retrieved Count")

# Unlabeled similarity distribution
ax = axes[1, 1]
if not unlabeled.empty:
    sns.histplot(ax=ax, data=unlabeled, x="top_similarity", bins=10)
    ax.set_title("Unlabeled Top Similarity")
else:
    ax.text(0.5, 0.5, "No unlabeled probes", ha="center")
    ax.set_axis_off()

# Summary text panel
ax = axes[1, 2]
ax.axis("off")

def fmt_pct(val):
    return "n/a" if val is None else f"{val:.2f}" if isinstance(val, (int, float)) else str(val)

lines = [
    "Evaluation Summary",
    "",
    f"P@1/3/5: {fmt_pct(summary.get('avg_precision_at_1'))} / {fmt_pct(summary.get('avg_precision_at_3'))} / {fmt_pct(summary.get('avg_precision_at_5'))}",
    f"MRR / NDCG@5: {fmt_pct(summary.get('avg_mrr'))} / {fmt_pct(summary.get('avg_ndcg_at_5'))}",
    f"Faithfulness: {fmt_pct(summary.get('avg_faithfulness_confidence'))}%",
    f"Relevancy: {fmt_pct(summary.get('avg_answer_relevancy'))}%",
    f"Avg Retrieval / Generation: {fmt_pct(summary.get('avg_retrieval_time'))}s / {fmt_pct(summary.get('avg_generation_time'))}s",
    f"Avg Response Time: {fmt_pct(summary.get('avg_response_time'))}s",
    "",
    "Coverage:",
    f"Raw markdown files: {coverage.get('raw_markdown_files', 'n/a')}",
    f"Processed chunks: {coverage.get('processed_chunks', 'n/a')}",
    f"Vector docs: {coverage.get('vector_total_documents', 'n/a')} (collection: {coverage.get('vector_collection', 'n/a')})"
]

ax.text(0, 0.95, "\n".join(lines), ha="left", va="top", fontsize=12)

plt.tight_layout()

# Add figure-level explanations
# fig.text(0.01, 0.98, "How to read:", fontsize=10, ha="left", va="top")
# fig.text(0.01, 0.94, "• Precision@K / MRR / NDCG: ranking quality of retrieved sources", fontsize=9, ha="left", va="top")
# fig.text(0.01, 0.90, "• Faithfulness/Relevancy: LLM judges grounding and directness of answers", fontsize=9, ha="left", va="top")
# fig.text(0.01, 0.86, "• Confidence vs Retrieved: low counts often correlate with low confidence", fontsize=9, ha="left", va="top")
# fig.text(0.01, 0.82, "• Unlabeled Similarity: shift downward may indicate drift or bad thresholds", fontsize=9, ha="left", va="top")
# fig.text(0.01, 0.78, "• Refusal Rate: for OOD probes, higher is safer (less hallucination)", fontsize=9, ha="left", va="top")

out_path = Path(__file__).parent.parent / "evaluation_plots.png"
fig.savefig(out_path, dpi=300, bbox_inches="tight")
print(f"Saved plots to {out_path}")