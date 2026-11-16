# Limitations & Data Governance

- **Dataset period**: Historical H&M observation period, not current 2026 behavior. *(Mitigation: Interpret as methodology validation on this dataset.)*
- **No order_id**: Exact order count is unavailable. *(Mitigation: Define Frequency as distinct purchase days.)*
- **No quantity field**: Repeated rows may represent multiple units. *(Mitigation: Do not mechanically drop exact transaction duplicates.)*
- **No browsing/cart events**: CVR and cart-abandonment cannot be measured. *(Mitigation: Exclude rather than fabricate proxies.)*
- **No campaign-treatment data**: Marketing impact cannot be estimated causally. *(Mitigation: Use A/B tests or uplift modeling for treatment effectiveness.)*
- **Unsupervised clustering**: No ground-truth segment labels. *(Mitigation: Use multiple metrics, stability, profiling and interpretability.)*
- **Cold-start customers**: 9,699 customers have zero purchases. *(Mitigation: Separate into unactivated onboarding cohort rather than RFM clustering.)*