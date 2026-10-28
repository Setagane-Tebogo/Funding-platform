# FundBridge proposal outcomes

Copy `proposal_training_template.csv` to `proposal_outcomes.csv` and add anonymised historical businesses. Record the financial values supplied at analysis time, then label the outcome after the business has operated long enough to evaluate it.

Use `profitableWithin18Months` as `1` when the business reached positive monthly profit within 18 months and `0` otherwise. Use `monthsToProfitability` for the observed month, or leave it blank when it was not reached.

Do not create labels from the model's own predictions. The trainer requires at least 50 real records and both outcome classes.
