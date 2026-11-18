# Final Findings — H&M Customer Segmentation

## Research Questions

### RQ1 — Is RFM baseline sufficient?

**Evidence:** RFM Sil=0.5024, DBI=0.7431, CH=73480.68; Extended Sil=0.5024, DBI=0.7431, CH=73480.68.

**Conclusion:** RFM is a valid baseline; the Extended set improved 0/3 screening metrics.

### RQ2 — Do Extended features improve segmentation?

**Evidence:** Best Extended set: recency_days | frequency_purchase_days | monetary_total_spend | product_type_diversity | product_diversity | garment_group_diversity; improvement count=0/3.

**Conclusion:** Extended features did not consistently improve all clustering metrics.

### RQ3 — Which features are useful and non-redundant?

**Evidence:** Quality + redundancy + ANOVA + MI + Random Forest + consensus + forward/ablation were combined.

**Conclusion:** Selected candidate features: frequency_purchase_days, product_type_diversity, product_diversity, garment_group_diversity, recency_days, monetary_total_spend

### RQ4 — What number of clusters/components is appropriate?

**Evidence:** K-Means and GMM were evaluated for 2–8 clusters/components using internal metrics, balance and stability; GMM additionally used AIC/BIC.

**Conclusion:** Technical winner uses 4 clusters/components.

### RQ5 — K-Means or GMM?

**Evidence:** Winner=KMeans; Sil=0.4263; DBI=0.7900; CH=148614.50; ARI=0.9907.

**Conclusion:** KMeans selected with k=4.

### RQ6 — Are clusters meaningful enough for business interpretation?

**Evidence:** 4 segment profiles; 15 features have medium/large effect size.

**Conclusion:** Segments are interpreted using measured R/F/M states, Extended descriptors, spending contribution and statistical profile differences.

### RQ7 — How can segments support marketing decisions?

**Evidence:** 4 strategy rows map segment profiles to diagnosis, objective, action family, KPI and risk.

**Conclusion:** Segments support differentiated marketing decision support, but actions remain hypotheses requiring controlled evaluation.

## Final Feature Set

recency_days, frequency_purchase_days, monetary_total_spend, product_type_diversity, product_diversity, garment_group_diversity

## Final Model

**KMeans**, k/components=4.

Silhouette=0.4263; DBI=0.7900; CH=148614.50; Stability ARI=0.9907.

## Final Segments

- **Active Developing** — customers=38.63791684681795%; observed spend=11.96411995837438%; descriptor=No strong extended descriptor
- **High-Value Loyal** — customers=10.966753555250348%; observed spend=52.12294414270979%; descriptor=Broad Fashion Interest
- **Dormant Low-Value** — customers=27.459312726229022%; observed spend=5.794771072688283%; descriptor=No strong extended descriptor
- **Frequent Core** — customers=22.93601687170268%; observed spend=30.118164826227538%; descriptor=Broad Fashion Interest

## Marketing Decision Support

- **Active Developing** → Nurture and progression → Relevant product/category discovery
- **Dormant Low-Value** → Low-cost re-engagement or deprioritization → Low-cost broad re-engagement
- **Frequent Core** → Value expansion → Cross-sell / basket expansion
- **High-Value Loyal** → Retention and value protection → Loyalty / exclusivity / early-access engagement

## Limitations

- **Dataset period**: Historical H&M observation period, not current 2026 behavior. Mitigation: Interpret as methodology validation on this dataset.
- **No order_id**: Exact order count is unavailable. Mitigation: Define Frequency as distinct purchase days.
- **No quantity field**: Repeated rows may represent multiple units. Mitigation: Do not mechanically drop exact transaction duplicates.
- **No browsing/cart events**: CVR and cart-abandonment cannot be measured. Mitigation: Exclude rather than fabricate proxies.
- **No returns/cancellation status**: ReturnRate/CancelRate unavailable. Mitigation: Do not claim these dimensions are included.
- **No campaign-treatment data**: Marketing impact cannot be estimated causally. Mitigation: Use A/B tests, uplift or causal inference for treatment effectiveness.
- **Unsupervised clustering**: No ground-truth segment labels. Mitigation: Use multiple metrics, stability, profiling and interpretability.
- **Cluster naming**: Segment names are interpretations, not true labels. Mitigation: Keep naming rules auditable and preserve cluster IDs.
- **FuturePurchase ranking target**: This is a proxy business outcome for ranking, not the clustering target. Mitigation: Combine supervised ranking with unsupervised clustering utility.
- **Model drift**: Segment structure may change over time. Mitigation: Re-audit and retrain after major behavior shifts.

## Final Interpretation

The study should be interpreted as a reproducible customer-segmentation and marketing-decision-support methodology evaluated on the H&M public dataset. Segment names are business interpretations of measured historical behavior, not ground-truth labels. Marketing actions remain hypotheses to test rather than causally optimal policies.