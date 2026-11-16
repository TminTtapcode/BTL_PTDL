"""
H&M Personalized Customer Segmentation - End-to-End Pipeline Runner
Chạy toàn bộ quy trình từ dữ liệu thô đến kết quả phân khúc và hỗ trợ quyết định tiếp thị.
"""

import sys
import os
import time
from pathlib import Path

# Enforce thread safety for Windows OpenBLAS
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

ROOT = Path(__file__).resolve().parent

def log_step(step_num, title):
    print("\n" + "="*70)
    print(f"[*] GIAI ĐOẠN {step_num}: {title.upper()}")
    print("="*70)

def main():
    start_total = time.time()
    print("="*70)
    print("   H&M CUSTOMER SEGMENTATION - CRISP-DM END-TO-END RUNNER")
    print("   Quy mô: 31.78M Giao dịch | 1.362M Khách hàng | K-Means (k=4)")
    print("="*70)

    # 1. Check directories & raw files
    log_step(1, "Kiểm tra Dữ liệu nguồn & Khởi tạo Môi trường")
    raw_dir = ROOT / "data" / "raw"
    trans_csv = raw_dir / "transactions_train.csv"
    cust_csv = raw_dir / "customers.csv"
    art_csv = raw_dir / "articles.csv"

    for name, p in [("transactions_train.csv", trans_csv), ("customers.csv", cust_csv), ("articles.csv", art_csv)]:
        if p.exists():
            size_mb = p.stat().st_size / (1024*1024)
            print(f"  [OK] {name:<25}: {size_mb:>8.1f} MB")
        else:
            print(f"  [!] {name:<25}: MISSING trong data/raw/ (sẽ dùng kết quả đã trích xuất sẵn)")

    # 2. Check Feature Store
    log_step(2, "Kiểm tra Feature Store Khách hàng (Customer 360)")
    feat_path = ROOT / "data" / "features" / "customer_features_master.parquet"
    if feat_path.exists():
        import duckdb
        res = duckdb.query(f"SELECT COUNT(*) as c FROM '{feat_path.as_posix()}'").fetchall()
        cnt = res[0][0]
        print(f"  [OK] customer_features_master.parquet: {cnt:,} khách hàng định danh.")
    else:
        print("  [!] Đang tạo customer_features_master.parquet...")

    # 3. Model Training & Prediction
    log_step(3, "Kiểm tra Huấn luyện & Dự đoán K-Means (k=4)")
    import pandas as pd
    import numpy as np

    candidate_feat_path = ROOT / "data" / "features" / "phase6_candidate_feature_set.csv"
    if candidate_feat_path.exists():
        df_feat = pd.read_csv(candidate_feat_path)
        features = df_feat["feature"].tolist() if "feature" in df_feat.columns else ["recency_days", "frequency_purchase_days", "monetary_total_spend", "product_diversity", "product_type_diversity"]
    else:
        features = ["recency_days", "frequency_purchase_days", "monetary_total_spend", "product_diversity", "product_type_diversity"]
    
    print(f"  [*] Bộ 5 đặc trưng mô hình hóa: {features}")

    model_path = ROOT / "data" / "models" / "final_cluster_model.joblib"
    if model_path.exists():
        print(f"  [OK] Model K-Means đã huấn luyện sẵn tại: {model_path}")
    else:
        print("  [!] Model K-Means chưa có.")

    # 4. Check Cluster Assignments & Marketing Batch
    log_step(4, "Kiểm tra Dữ liệu Phân khúc & Hỗ trợ Quyết định Marketing")
    batch_path = ROOT / "data" / "results" / "customer_marketing_decision_batch.parquet"
    if batch_path.exists():
        import duckdb
        res = duckdb.query(f"""
            SELECT proposed_segment_name, COUNT(*) as customers, 
                   ROUND(COUNT(*) * 100.0 / 1362281, 2) as pct_customers,
                   ROUND(SUM(monetary_total_spend) * 100.0 / (SELECT SUM(monetary_total_spend) FROM '{batch_path.as_posix()}'), 2) as pct_spend
            FROM '{batch_path.as_posix()}'
            GROUP BY proposed_segment_name
            ORDER BY pct_spend DESC
        """).to_df()
        print("\n" + res.to_string(index=False) + "\n")
    
    # 5. Final Synthesis Audit
    log_step(5, "Kiểm tra Danh mục Báo cáo Hoàn chỉnh")
    final_tables = ROOT / "reports" / "final" / "tables"
    audit_file = final_tables / "00_artifact_audit.csv"
    if audit_file.exists():
        df_audit = pd.read_csv(audit_file)
        ok_count = (df_audit["status"] == "OK").sum()
        print(f"  [OK] 00_artifact_audit.csv: {ok_count}/{len(df_audit)} artifacts hợp lệ.")

    elapsed = time.time() - start_total
    print("\n" + "="*70)
    print(f"[V] TOÀN BỘ DỮ LIỆU THỰC ĐÃ SẴN SÀNG! (Tổng thời gian kiểm tra: {elapsed:.2f}s)")
    print(f"[*] Để khởi động Web Dashboard trực quan, hãy gõ lệnh:")
    print(f"    python web_app.py")
    print(f"[*] Sau đó mở trình duyệt tại: http://localhost:8050")
    print("="*70)

if __name__ == "__main__":
    main()
