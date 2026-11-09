# Evaluation report template

## Dataset and provenance
Record official source URL, download date, file name, label counts and license.

## Split strategy
Current starter baseline uses stratified random split and may overestimate performance
because flows from the same sessions can be correlated. Improve to day/session holdout.

## Model metrics
Record precision, recall, F1, PR-AUC, false-positive rate, confusion matrix,
threshold, training time and inference latency. Include per-attack metrics where possible.

## Neural network comparison
Report training/validation curves, early stopping, preprocessing, and comparison
on exactly the same held-out test data.

## Agent evaluation
Create 20 labeled scenarios; check evidence references, unsupported claims,
tool permission adherence, latency, cost, and reviewer corrections.

## Business metrics
Measure case handling time manually and with assistance on the same defined tasks.
Report sample sizes, distributions, and assumptions. Do not claim financial savings
without observed data.
