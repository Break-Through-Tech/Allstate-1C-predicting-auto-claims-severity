# Approach 2: XGBoost in plain language

XGBoost takes the claim's 116 anonymous category fields and 14 numeric fields.
The ID identifies a claim but is not a predictor. The recorded loss is the answer
used while learning. Category names carry no assumed numeric order. Categories
with fewer than 30 examples in the fitting data are grouped; unseen or missing
categories follow the model's learned missing-value branch. Numeric fields keep
their original scale.

The model builds a sequence of small decision trees. Each tree asks questions
about the fields and adds a correction to the running prediction. Later trees
help correct errors left by earlier trees. The configured absolute-error
objective encourages predictions near the typical middle outcome for claims
with similar features. Trees can learn curved relationships and combinations of
fields that a linear model may miss.

The output is a predicted claim loss in the same units as the recorded `loss`.
There is no log transform or inverse transform. It is an estimate for one claim,
not a guarantee, an upper loss bound, or a causal explanation.

Five saved training folds compare five initial settings. Each claim is predicted
by a model that did not fit on that claim; preprocessing is also learned only
inside each fit portion. Pooled out-of-fold MAE is the average absolute mistake
across those predictions. A lower value is better. We then write a reason for
changing exactly one setting, run that sixth configuration on the same folds,
and retain the change only if its training-CV improvement reaches the team's
recorded threshold. Validation is released only in the team's recorded sequence;
test claims stay reserved.

Real training is still awaiting readiness and validation-policy decisions.
Synthetic smoke scores demonstrate that the software runs; they do not establish
accuracy on claims. Even after real training, unusually large losses and
categories with little training evidence may be hard to predict. The eventual
receipt must report before/after MAE and whether the follow-up was worth keeping.
