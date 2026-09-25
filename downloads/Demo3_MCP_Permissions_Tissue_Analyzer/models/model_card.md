# tissue_rf_v2

Random-forest classifier over tile-level texture features, trained on 1,200
hematoxylin and eosin slides from the 2024-2025 cohort.

**Classes:** normal, mild_injury, necrosis

**Performance:** 0.91 balanced accuracy on a held-out set of 300 clean slides.

**Known limitation.** Artifact-containing slides (folds, tears, pen marks) were
excluded from the training set. The model has no artifact class. On a slide
containing a fold it will still return one of the three labels above, usually
with high probability.
