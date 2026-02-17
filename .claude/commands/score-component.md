# Score Component: $ARGUMENTS

Update the AI Platform Building Scorecard for the component: **$ARGUMENTS**

## Instructions

1. Open `spec/SCORECARD.md`
2. Find the row for "$ARGUMENTS"
3. Fill in these columns based on what just happened:

| Column | How to Score |
|--------|-------------|
| **Toil Reduced (1-10)** | 10 = AI did it in minutes, no corrections. 5 = good starting point, significant corrections needed. 1 = starting from scratch would have been faster. |
| **Correction Cycles** | Number of times the AI output needed human intervention before it worked. |
| **AI Time** | Wall clock minutes spent with AI assistance. |
| **Est. Manual Time** | Estimated minutes for a senior engineer without AI. |
| **Toil Shifted?** | Yes = AI converted one type of toil to another. No = AI genuinely reduced toil. Partial = some reduction, some shift. |
| **Notes** | What went wrong, what was surprising, what worked well. |

4. Save the file

## Scoring Guidelines

Be honest. This data becomes talk material. Inflated scores undermine the talk's credibility.

- If AI-generated config needed IAM debugging, that's a correction cycle
- If AI wrote valid YAML but wrong values, that's "Toil Shifted"
- If you had to explain the same thing twice, count each as a correction cycle
- Time spent reviewing AI output counts toward AI Time
