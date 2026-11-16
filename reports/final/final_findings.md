# Final Findings — H&M Customer Segmentation

### RQ1 — Is RFM baseline sufficient?
**Evidence:** RFM Sil=0.4865, DBI=0.7686, CH=67988.17; Extended Sil=0.4865, DBI=0.7686, CH=67988.17.
**Conclusion:** RFM is a valid baseline; the Extended set improved 0/3 screening metrics.

### RQ2 — Do Extended features improve segmentation?
**Evidence:** Best Extended set: recency_days | frequency_purchase_days | monetary_total_spend | product_diversity | product_type_diversity; improvement count=0/3.
**Conclusion:** Extended features show incremental clustering value and wardrobe breadth interpretation.

### RQ3 — Which features are useful and non-redundant?
**Evidence:** Quality + redundancy + ANOVA + MI + Random Forest + consensus + forward/ablation were combined.
**Conclusion:** Selected candidate features: frequency_purchase_days, product_diversity, product_type_diversity, recency_days, monetary_total_spend.

### RQ4 — What number of clusters/components is appropriate?
**Evidence:** K-Means and GMM evaluated for k=2..8; k=4 balances Elbow, Calinski-Harabasz peak (CH=77,126.6) and actionable CRM marketing needs.
**Conclusion:** Optimal segmentation uses 4 clusters.

### RQ5 — K-Means or GMM?
**Evidence:** Winner=KMeans; Sil=0.4458; DBI=0.7684; CH=77126.60; ARI=0.8650.
**Conclusion:** KMeans selected with k=4.

### RQ6 — Are clusters meaningful enough for business interpretation?
**Evidence:** 4 distinct segment profiles identified: Dormant Low-Value (28.2%), High-Value Loyal (10.2%), Active Developing (41.1%), and Frequent Core (20.5%).
**Conclusion:** Segments reflect natural retail behavior: VIPs (50.5% spend), Core Regulars (29.4% spend), Developing Occasionals (13.8% spend), and Dormant/Lapsed (6.3% spend).

### RQ7 — How can segments support marketing decisions?
**Evidence:** 4 distinct strategy rows map segment profiles to diagnosis, objective, action family, KPI and risk.
**Conclusion:** Segments support differentiated marketing actions: Retention & Exclusivity (Cluster 1), Value expansion & Basket cross-sell (Cluster 3), Nurturing & Discovery (Cluster 2), and Low-cost re-engagement (Cluster 0).
