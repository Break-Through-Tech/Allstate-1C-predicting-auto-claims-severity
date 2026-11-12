# Approach 1 Explained: The Regularized Linear Model

Owner: Rachel Cheung · Issue #44 · Technical details: [Approach 1 experiment record](approach1_glm_record.md)

**In one sentence:** the model estimates a claim's final paid amount by starting from a typical amount and adjusting it up or down by a small percentage for each piece of claim information. On validation claims it is off by **$1,250 on average**, compared with $1,803 for always guessing the typical claim.

## What it predicts

For each auto insurance claim, the model predicts `loss`: the final amount paid, in the same units as the data. It sees the claim's 130 anonymous fields. Results describe how well it works on this supplied file. They don't show it would work the same way on future claims, and we haven't confirmed which fields are known when a claim is first filed.

## Inputs

All 130 fields in the data, and nothing else:

- **116 category fields** (`cat1`–`cat116`). Each holds a label such as `A` or `B`. The labels are codes, not rankings, so `B` is not "more" than `A`.
- **14 number fields** (`cont1`–`cont14`), each already between 0 and 1.

The claim ID and the paid amount are never inputs. The meanings of the fields are hidden, so the model can't use or reveal what any field represents.

## How the inputs are prepared (encoding)

A linear model needs numbers, so each field is converted first. These rules are learned from training claims only:

- **Category fields become yes/no columns.** For example, a field with labels `A`, `B` and `C` becomes three columns: "is it A?", "is it B?", "is it C?". A claim gets a 1 in the matching column and 0 elsewhere.
- **Rare labels are pooled.** A label seen fewer than 30 times in training doesn't have enough examples to learn from reliably, so all of a field's rare labels share one "rare" column. This affected 352 labels across 30 fields.
- **New labels are handled safely.** A label never seen in training is treated like a rare label, so the model still makes a prediction.
- **Number fields are put on the same scale.** Each is rescaled so 1 unit means "one standard deviation", which lets the penalty below treat every field fairly.

After this step every claim is a row of **808 numbers**.

## How it learns

The model gives each of the 808 columns a **weight** and adds them up. Two choices shape how those weights are found:

1. **It learns on the log scale.** Claim amounts are very lopsided: most are a few thousand, but a few exceed $100,000. The model learns from `log(1 + loss)` instead of `loss` itself, which turns the lopsided amounts into a nearly balanced shape. In practice this means **each weight acts as a percentage change**, not a dollar change. It also pulls predictions toward the typical (median) claim, which is what our error measure, MAE, rewards.
2. **It is penalized for large weights.** With 808 weights and many weak signals, an unrestricted model would chase noise in the training claims. A penalty (ridge regression) keeps every weight small unless the data clearly supports it, and it spreads weight across fields that move together (such as `cont11` and `cont12`) instead of picking one arbitrarily.

## Key settings

| Setting | Value | What it means |
| :--- | :--- | :--- |
| Penalty strength (`alpha`) | **100** | How hard large weights are discouraged. Picked from six options (1 to 100,000) using training data only. |
| Rare-label cutoff | 30 claims | Labels seen less often than this are pooled. |
| Target | `log(1 + loss)` | Learn on the log scale, then convert back. |
| Prediction limits | $6 to $121,012 | Predictions are kept inside the range of losses seen in training. None needed limiting. |

**How the penalty was chosen.** The training claims were split into 5 groups. For each option, the model was trained on 4 groups and tested on the 5th, rotating through all 5. Penalties from 1 to 1,000 scored almost the same (within about $1.20 of each other), so the exact choice matters little. Very strong penalties (10,000 and up) made the model too cautious and clearly worse. Under our pre-agreed tie rule, 100 was selected. Validation claims weren't used for any of this.

## What its output means

**A prediction is a dollar amount, best read as a typical outcome for claims like this one, not a guarantee.** Because the model learns on the log scale, it builds a prediction by multiplying adjustments together:

> starting amount × (adjustment for cat1's label) × (adjustment for cat2's label) × … × (adjustment for cont14)

Each adjustment is small. For example:

- One standard deviation higher on `cont2` raises the prediction by about **5.7%**; on `cont7`, by about **4.4%**.
- The category fields with the biggest influence (`cat57`, `cat100`, `cat77`, `cat80`) change the prediction by up to about **1.4–1.5 times** between their highest and lowest labels.

These match September's finding that `cont2` and `cont7` have the strongest (though still weak) links to loss. But because the fields are anonymous, **a weight shows a statistical pattern in this data, not a cause.** Fields that move together share their weight: `cont1` gets a negative weight while its close partner `cont9` gets a positive one, so neither should be read on its own.

Because predictions are pulled toward the middle, they are narrower than real claims. In the training check, nine in ten predictions fell between about **$990 and $6,630**, while 5% of actual training claims exceed **$8,512**. **The model tends to under-predict very large claims.**

## How well it does

Average error (MAE), in dollars. Lower is better.

| Method | Training check (5 groups) | Validation (28,248 claims) |
| :--- | ---: | ---: |
| Always guess the training average | 1,965.90 | 1,959.63 |
| Always guess the training median | 1,808.99 | 1,802.79 |
| **This model** | **1,245.40** | **1,250.45** |

On validation the model cuts average error by **36%** compared with guessing the average, and **31%** compared with guessing the median. Its training check and validation scores are within $5 of each other, which suggests it isn't overfitting. It was scored on validation only once, and the sealed test claims were never used.

## Limits to keep in mind

- It can only add up effects; it can't capture fields that matter only in combination (interactions) or relationships that bend. Approach 2 (XGBoost) is meant to test whether those exist.
- It under-predicts the largest claims, as described above.
- Results come from one internal split of this file, and September's exploration already looked at all of it. They aren't proof of performance on future claims.