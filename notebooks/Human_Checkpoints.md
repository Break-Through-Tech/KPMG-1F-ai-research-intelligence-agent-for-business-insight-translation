# Original checkpoint sketch (superseded)

This preserves the original design sketch, not executable Python. It contains
unfinished syntax and undefined APIs. Use [Human_in_Loop_Checkpoint.ipynb](Human_in_Loop_Checkpoint.ipynb)
for the working prototype and [the output contract](../docs/human-checkpoint.md)
for setup, evidence, and human-review requirements.

```text
insight = {
    "industry": "finance"
    "insight" : " Banks can fully automate quarterly reporting."
}
industry = insight["industry"]
query = f"""(
    Retrieve all the regulations around this topic {industry} and this insight: {insight}
)
rules = regulation_retriever.search(
"query" 
)
prompt = f"""{
    Industry:
    {industry}
 
    Relevant Regulations:
    {retrieved_regulations}
 
    Insight:
    {insight}
 
    Using the relevant regulations available, rate whether the insight that we have is legitimate and doable in the company.
"""
}
```
