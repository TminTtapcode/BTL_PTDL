# Limitations

## Dataset period

**Implication:** Historical H&M observation period, not current 2026 behavior.

**Mitigation:** Interpret as methodology validation on this dataset.

## No order_id

**Implication:** Exact order count is unavailable.

**Mitigation:** Define Frequency as distinct purchase days.

## No quantity field

**Implication:** Repeated rows may represent multiple units.

**Mitigation:** Do not mechanically drop exact transaction duplicates.

## No browsing/cart events

**Implication:** CVR and cart-abandonment cannot be measured.

**Mitigation:** Exclude rather than fabricate proxies.

## No returns/cancellation status

**Implication:** ReturnRate/CancelRate unavailable.

**Mitigation:** Do not claim these dimensions are included.

## No campaign-treatment data

**Implication:** Marketing impact cannot be estimated causally.

**Mitigation:** Use A/B tests, uplift or causal inference for treatment effectiveness.

## Unsupervised clustering

**Implication:** No ground-truth segment labels.

**Mitigation:** Use multiple metrics, stability, profiling and interpretability.

## Cluster naming

**Implication:** Segment names are interpretations, not true labels.

**Mitigation:** Keep naming rules auditable and preserve cluster IDs.

## FuturePurchase ranking target

**Implication:** This is a proxy business outcome for ranking, not the clustering target.

**Mitigation:** Combine supervised ranking with unsupervised clustering utility.

## Model drift

**Implication:** Segment structure may change over time.

**Mitigation:** Re-audit and retrain after major behavior shifts.
