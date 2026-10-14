# AgriSmart AI — Model Report

**Team:** _<fill in>_ &nbsp;|&nbsp; **Team ID:** _<fill in>_ &nbsp;|&nbsp; **Date:** _<fill in>_

## Task
Crop-disease image classification. Multi-class classification of a leaf/crop
photo into one disease class or "healthy" from the organizers' shared class
list (~15–20 classes + healthy variants). See `model/labels.py`.

## Dataset & Split
| Split | Source | Role |
|---|---|---|
| Train / Validation | PlantVillage (lab-condition images), ~54,000 images across the shared class list | Model is trained and tuned here only |
| Held-out Test | PlantDoc-style field-condition images, released by organizers | Never trained on; used only for the reported core metric |

_Fill in once the kickoff data is released: exact image counts per split,
per-class counts, and any additional public data added to training (with
citation)._

## Model / Approach
- **Backbone:** MobileNetV2, ImageNet-pretrained (transfer learning), classifier
  head replaced with a linear layer sized to the class list (`model/train.py`).
- **Input:** 224×224 RGB, ImageNet normalization, random-resized-crop /
  flip / color-jitter augmentation on train, center-crop on val/test.
- **Optimizer:** AdamW, configurable learning rate (default 3e-4).
- **Options:** `--freeze-backbone` trains only the classifier head (fast
  baseline); full fine-tuning trains the whole network.
- **Class-index alignment:** training/eval folders are remapped to the
  canonical index order in `model/labels.py` so saved weights always match
  `predict.py`'s output labels regardless of local folder ordering.

_Fill in once trained on real data: final hyperparameters (epochs, batch
size, LR schedule if any), training time, hardware used._

## Metric & Result
- **Primary metric:** Macro-averaged F1 on the held-out field test set
  (chosen over raw accuracy because disease classes are imbalanced).
- **Also reported:** confusion matrix, per-class precision/recall
  (`model/evaluate.py` writes these to `report/test_metrics.json` and
  `report/confusion_matrix.png`).

| Metric | Validation (lab split) | Held-out Test (field, organizer-scored) |
|---|---|---|
| Macro-F1 | _<fill in>_ | _<fill in>_ |
| Accuracy | _<fill in>_ | _<fill in>_ |

_Insert the confusion matrix image and per-class table here once trained on
the real dataset. A pipeline smoke test with synthetic placeholder data is
included in this repo (`model/make_dummy_data.py`) purely to prove the
code runs end-to-end — it produces no meaningful accuracy._

## Baseline
_Fill in: the organizers' published baseline macro-F1, and how this model
compares to it on the held-out field set._

## Limitations
- Expected accuracy drop from lab-condition validation to field-condition
  test, since PlantVillage images are clean/uniform-background while the
  field set has natural lighting, clutter, and occlusion — this gap is the
  deliberate difficulty called out in the problem statement.
- Class list is fixed to what's published at kickoff; diseases outside
  this list are out of scope and will be misclassified into the nearest
  known class.
- Single-leaf, single-label assumption: an image with multiple co-occurring
  issues will only return one label.
- _Add any other honest failure cases observed once trained on real data
  (e.g. specific crops/diseases that underperform, sensitivity to blur or
  extreme lighting)._
