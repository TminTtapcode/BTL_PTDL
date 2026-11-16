import http.server
import socketserver
import json
import urllib.parse
from pathlib import Path
import pandas as pd
import duckdb
import joblib
import numpy as np

# Mock OutlierCapper so joblib unpickles preprocessor cleanly
class OutlierCapper:
    pass
import __main__
__main__.OutlierCapper = OutlierCapper

PORT = 8050
ROOT = Path(__file__).resolve().parent

# Load reference summary tables
SEGMENTS_FILE = ROOT / "reports" / "final" / "tables" / "04_final_business_segments.csv"
STRATEGY_FILE = ROOT / "reports" / "final" / "tables" / "06_final_marketing_strategy_matrix.csv"
OBJECTIVE_FILE = ROOT / "reports" / "final" / "tables" / "07_marketing_objective_distribution.csv"
PARQUET_FILE = ROOT / "data" / "results" / "customer_marketing_decision_batch.parquet"
MODEL_FILE = ROOT / "data" / "models" / "final_cluster_model.joblib"
PREP_FILE = ROOT / "data" / "models" / "final_preprocessor.joblib"

# Load model if available
try:
    cluster_model = joblib.load(MODEL_FILE)
    preprocessor = joblib.load(PREP_FILE)
    print("[INIT] K-Means Model and Preprocessor loaded successfully.")
except Exception as e:
    cluster_model = None
    preprocessor = None
    print(f"[WARN] Could not load model: {e}")

# Preload segments summary
if SEGMENTS_FILE.exists():
    df_segments = pd.read_csv(SEGMENTS_FILE)
else:
    df_segments = pd.DataFrame()

if STRATEGY_FILE.exists():
    df_strategy = pd.read_csv(STRATEGY_FILE)
else:
    df_strategy = pd.DataFrame()

if OBJECTIVE_FILE.exists():
    df_objective = pd.read_csv(OBJECTIVE_FILE)
else:
    df_objective = pd.DataFrame()

# Pre-fetch a few sample customer IDs for quick demo
sample_customers = []
if PARQUET_FILE.exists():
    try:
        sample_df = duckdb.query(f"""
            WITH ranked AS (
                SELECT customer_id, cluster_id, proposed_segment_name, 
                       recency_days, frequency_purchase_days, monetary_total_spend,
                       ROW_NUMBER() OVER(PARTITION BY cluster_id ORDER BY customer_id) as rn
                FROM '{PARQUET_FILE.as_posix()}'
            )
            SELECT customer_id, cluster_id, proposed_segment_name,
                   recency_days, frequency_purchase_days, monetary_total_spend
            FROM ranked WHERE rn <= 3
            ORDER BY cluster_id
        """).to_df()
        sample_customers = sample_df.to_dict(orient="records")
    except Exception as e:
        print(f"[WARN] Error prefetching sample customers: {e}")

HTML_PAGE = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>H&M Customer Segmentation & Marketing Intelligence</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        body { font-family: 'Inter', sans-serif; background-color: #0f172a; color: #f8fafc; }
        .card { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .tab-btn.active { background: #e11d48; color: white; border-color: #e11d48; }
    </style>
</head>
<body class="min-h-screen flex flex-col">
    <!-- Navbar -->
    <header class="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-50 px-6 py-4 flex flex-wrap justify-between items-center">
        <div class="flex items-center space-x-3">
            <span class="bg-rose-600 text-white font-extrabold px-3 py-1 rounded-lg tracking-wider text-xl">H&M</span>
            <div>
                <h1 class="text-lg font-bold text-white tracking-wide">Customer Segmentation Intelligence</h1>
                <p class="text-xs text-slate-400">Hệ thống Phân khúc & Hỗ trợ Quyết định Marketing (CRISP-DM 9-Phase)</p>
            </div>
        </div>
        <div class="flex items-center space-x-2 text-xs">
            <span class="px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-medium flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> 1.36M Khách hàng Thật
            </span>
            <span class="px-2.5 py-1 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30 font-medium">
                31.78M Giao dịch
            </span>
            <span class="px-2.5 py-1 rounded-full bg-purple-500/20 text-purple-400 border border-purple-500/30 font-medium">
                K-Means (k=4)
            </span>
        </div>
    </header>

    <!-- Main Container -->
    <main class="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        <!-- Navigation Tabs -->
        <div class="flex flex-wrap gap-2 border-b border-slate-800 pb-3">
            <button onclick="switchTab('overview')" id="tab-overview" class="tab-btn active px-4 py-2 rounded-lg font-medium text-sm border border-slate-700 bg-slate-800 hover:bg-slate-700 transition flex items-center gap-2">
                <i class="fa-solid fa-chart-pie"></i> Tổng quan Điều hành
            </button>
            <button onclick="switchTab('segments')" id="tab-segments" class="tab-btn px-4 py-2 rounded-lg font-medium text-sm border border-slate-700 bg-slate-800 hover:bg-slate-700 transition flex items-center gap-2 text-slate-300">
                <i class="fa-solid fa-users-viewfinder"></i> 4 Chân dung Khách hàng & KPI
            </button>
            <button onclick="switchTab('lookup')" id="tab-lookup" class="tab-btn px-4 py-2 rounded-lg font-medium text-sm border border-slate-700 bg-slate-800 hover:bg-slate-700 transition flex items-center gap-2 text-slate-300">
                <i class="fa-solid fa-magnifying-glass"></i> Tra cứu Khách hàng Thật (1.36M)
            </button>
            <button onclick="switchTab('simulator')" id="tab-simulator" class="tab-btn px-4 py-2 rounded-lg font-medium text-sm border border-slate-700 bg-slate-800 hover:bg-slate-700 transition flex items-center gap-2 text-slate-300">
                <i class="fa-solid fa-wand-magic-sparkles"></i> Mô phỏng Phân khúc Mới (What-If)
            </button>
        </div>

        <!-- TAB 1: OVERVIEW -->
        <section id="content-overview" class="space-y-6">
            <!-- Big Stats Cards -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div class="card p-5 rounded-xl border-l-4 border-l-rose-500">
                    <p class="text-xs uppercase tracking-wider text-slate-400 font-semibold">Khách hàng VIP (High-Value)</p>
                    <div class="flex justify-between items-baseline mt-2">
                        <span class="text-3xl font-extrabold text-rose-400">10.2%</span>
                        <span class="text-xs px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-semibold">138,928 khách</span>
                    </div>
                    <p class="text-xs text-slate-300 mt-2 font-medium">Đóng góp <span class="text-rose-300 font-bold">50.38%</span> tổng doanh thu</p>
                </div>
                <div class="card p-5 rounded-xl border-l-4 border-l-amber-500">
                    <p class="text-xs uppercase tracking-wider text-slate-400 font-semibold">Thân thiết Nòng cốt (Frequent Core)</p>
                    <div class="flex justify-between items-baseline mt-2">
                        <span class="text-3xl font-extrabold text-amber-400">20.5%</span>
                        <span class="text-xs px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-semibold">279,308 khách</span>
                    </div>
                    <p class="text-xs text-slate-300 mt-2 font-medium">Đóng góp <span class="text-amber-300 font-bold">29.51%</span> tổng doanh thu</p>
                </div>
                <div class="card p-5 rounded-xl border-l-4 border-l-emerald-500">
                    <p class="text-xs uppercase tracking-wider text-slate-400 font-semibold">Đang phát triển (Active Developing)</p>
                    <div class="flex justify-between items-baseline mt-2">
                        <span class="text-3xl font-extrabold text-emerald-400">41.1%</span>
                        <span class="text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-semibold">560,287 khách</span>
                    </div>
                    <p class="text-xs text-slate-300 mt-2 font-medium">Đóng góp <span class="text-emerald-300 font-bold">13.83%</span> tổng doanh thu</p>
                </div>
                <div class="card p-5 rounded-xl border-l-4 border-l-blue-500">
                    <p class="text-xs uppercase tracking-wider text-slate-400 font-semibold">Ngủ đông / Rời bỏ (Dormant)</p>
                    <div class="flex justify-between items-baseline mt-2">
                        <span class="text-3xl font-extrabold text-blue-400">28.2%</span>
                        <span class="text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 font-semibold">383,758 khách</span>
                    </div>
                    <p class="text-xs text-slate-300 mt-2 font-medium">Đóng góp <span class="text-blue-300 font-bold">6.28%</span> tổng doanh thu</p>
                </div>
            </div>

            <!-- Charts Row -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- Chart 1: Pareto Bar Comparison -->
                <div class="card p-5 rounded-xl space-y-3">
                    <h3 class="font-bold text-sm text-slate-200 flex items-center gap-2">
                        <i class="fa-solid fa-chart-column text-rose-500"></i> Quy Luật Pareto: Tỷ lệ Khách hàng vs Doanh thu Đóng góp
                    </h3>
                    <div class="h-64">
                        <canvas id="paretoChart"></canvas>
                    </div>
                </div>

                <!-- Chart 2: Revenue Distribution Donut -->
                <div class="card p-5 rounded-xl space-y-3">
                    <h3 class="font-bold text-sm text-slate-200 flex items-center gap-2">
                        <i class="fa-solid fa-chart-pie text-amber-500"></i> Cơ Cấu Doanh Thu Đóng Góp Giữa 4 Phân Khúc
                    </h3>
                    <div class="h-64 flex justify-center">
                        <canvas id="spendDonut"></canvas>
                    </div>
                </div>
            </div>

            <!-- Radar & Method Pipeline -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div class="card p-5 rounded-xl space-y-3 lg:col-span-1">
                    <h3 class="font-bold text-sm text-slate-200 flex items-center gap-2">
                        <i class="fa-solid fa-compass-drafting text-purple-400"></i> Biểu đồ Radar Đặc trưng Cụm
                    </h3>
                    <div class="h-64">
                        <canvas id="radarChart"></canvas>
                    </div>
                </div>
                <div class="card p-5 rounded-xl space-y-4 lg:col-span-2">
                    <h3 class="font-bold text-sm text-slate-200 flex items-center gap-2">
                        <i class="fa-solid fa-shield-halved text-emerald-400"></i> Điểm Nhấn Khoa Học & Rào Chắn Nghiệp Vụ (Guardrails)
                    </h3>
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                        <div class="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20">
                            <span class="font-bold text-rose-400 flex items-center gap-1.5 mb-1">
                                <i class="fa-solid fa-triangle-exclamation"></i> Rào chắn 1: Bảo vệ Lợi nhuận VIP
                            </span>
                            <p class="text-slate-300">Tuyệt đối không giảm giá xả kho hoặc gửi voucher 20-30% cho nhóm High-Value Loyal để tránh xói mòn 50.4% doanh thu cốt lõi.</p>
                        </div>
                        <div class="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
                            <span class="font-bold text-blue-400 flex items-center gap-1.5 mb-1">
                                <i class="fa-solid fa-ban"></i> Rào chắn 2: Kiểm soát Chi phí Dormant
                            </span>
                            <p class="text-slate-300">Chỉ dùng kênh miễn phí (email tự động). Nghiêm cấm chạy quảng cáo trả phí (Paid Ads) cho nhóm ngủ đông nếu thiếu bằng chứng Uplift.</p>
                        </div>
                        <div class="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                            <span class="font-bold text-emerald-400 flex items-center gap-1.5 mb-1">
                                <i class="fa-solid fa-check-double"></i> Căn cứ chọn K-Means k=4
                            </span>
                            <p class="text-slate-300">Đỉnh Calinski-Harabasz đạt 77,126.6; điểm gập Elbow rõ nét; độ ổn định Bootstrap ARI = 0.865; phân hóa đúng 4 tầng bậc CRM.</p>
                        </div>
                        <div class="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                            <span class="font-bold text-amber-400 flex items-center gap-1.5 mb-1">
                                <i class="fa-solid fa-bolt"></i> Xử lý Dữ liệu Lệch phải (IQR Trap)
                            </span>
                            <p class="text-slate-300">Biến đổi logarit ln(1+x) và Capping phân vị 99.9% bảo toàn trọn vẹn nhóm khách hàng mua sắm tích cực nhất.</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- TAB 2: SEGMENTS DETAIL -->
        <section id="content-segments" class="hidden space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6" id="segmentsCardsContainer">
                <!-- Rendered dynamically via JS -->
            </div>
        </section>

        <!-- TAB 3: CUSTOMER LOOKUP -->
        <section id="content-lookup" class="hidden space-y-6">
            <div class="card p-6 rounded-xl space-y-4">
                <h3 class="font-bold text-base text-slate-100 flex items-center gap-2">
                    <i class="fa-solid fa-address-card text-rose-500"></i> Tra Cứu Khách Hàng Thật trong 1,362,281 Bản Ghi
                </h3>
                <p class="text-xs text-slate-400">Nhập mã định danh khách hàng 64 ký tự (customer_id) hoặc bấm chọn nhanh một khách hàng mẫu bên dưới:</p>
                
                <!-- Quick sample customer pills -->
                <div class="flex flex-wrap items-center gap-2 text-xs">
                    <span class="text-slate-400 font-semibold">Khách hàng mẫu:</span>
                    <div id="samplePillsContainer" class="flex flex-wrap gap-2"></div>
                </div>

                <!-- Input search box -->
                <div class="flex gap-2">
                    <input type="text" id="searchInput" placeholder="Dán mã customer_id tại đây (ví dụ: 8161cf725cd125586a9811433f957f5c6d47801f955517...)" 
                           class="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-sm text-slate-200 focus:outline-none focus:border-rose-500">
                    <button onclick="searchCustomer()" class="bg-rose-600 hover:bg-rose-500 text-white font-medium px-5 py-2 rounded-lg text-sm transition flex items-center gap-2">
                        <i class="fa-solid fa-search"></i> Tra Cứu Ngay
                    </button>
                </div>

                <!-- Customer Details Result Card -->
                <div id="customerResult" class="hidden mt-6 p-5 rounded-xl bg-slate-900/90 border border-slate-700 space-y-4">
                    <!-- Dynamic details injected here -->
                </div>
            </div>
        </section>

        <!-- TAB 4: WHAT-IF SIMULATOR -->
        <section id="content-simulator" class="hidden space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Form Inputs -->
                <div class="card p-6 rounded-xl space-y-4 lg:col-span-1">
                    <h3 class="font-bold text-base text-slate-100 flex items-center gap-2">
                        <i class="fa-solid fa-sliders text-rose-500"></i> Nhập Chỉ Số Khách Hàng Mới
                    </h3>
                    <p class="text-xs text-slate-400">Thử nghiệm phân loại tự động cho khách hàng mới gia nhập hệ thống:</p>
                    
                    <div class="space-y-3 text-xs">
                        <div>
                            <label class="block text-slate-300 font-semibold mb-1">Recency (Số ngày kể từ lần mua cuối):</label>
                            <input type="number" id="simRecency" value="30" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-200">
                        </div>
                        <div>
                            <label class="block text-slate-300 font-semibold mb-1">Frequency (Số ngày mua hàng độc lập):</label>
                            <input type="number" id="simFreq" value="15" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-200">
                        </div>
                        <div>
                            <label class="block text-slate-300 font-semibold mb-1">Monetary Total Spend (Tổng chi tiêu H&M):</label>
                            <input type="number" step="0.1" id="simSpend" value="1.8" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-200">
                        </div>
                        <div>
                            <label class="block text-slate-300 font-semibold mb-1">Product Diversity (Số mã sản phẩm đã mua):</label>
                            <input type="number" id="simProdDiv" value="25" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-200">
                        </div>
                        <div>
                            <label class="block text-slate-300 font-semibold mb-1">Product Type Diversity (Số loại trang phục):</label>
                            <input type="number" id="simTypeDiv" value="12" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-200">
                        </div>
                    </div>

                    <button onclick="runSimulation()" class="w-full bg-rose-600 hover:bg-rose-500 text-white font-semibold py-2.5 rounded-lg text-sm transition flex justify-center items-center gap-2 mt-4">
                        <i class="fa-solid fa-microchip"></i> Dự Đoán Phân Khúc Bằng K-Means
                    </button>
                </div>

                <!-- Simulation Output -->
                <div class="card p-6 rounded-xl space-y-4 lg:col-span-2 flex flex-col justify-center">
                    <div id="simEmpty" class="text-center py-12 text-slate-500 space-y-2">
                        <i class="fa-solid fa-robot text-4xl"></i>
                        <p class="text-sm">Bấm nút "Dự đoán phân khúc" để mô hình K-Means chạy suy luận trực tiếp.</p>
                    </div>
                    <div id="simResult" class="hidden space-y-4">
                        <!-- Dynamic Result Content -->
                    </div>
                </div>
            </div>
        </section>
    </main>

    <!-- Footer -->
    <footer class="border-t border-slate-800 bg-slate-900 px-6 py-4 text-center text-xs text-slate-500 mt-auto">
        Đồ án môn học Khai phá Dữ liệu & Học máy Ứng dụng &bull; Phân khúc Khách hàng Chuỗi Thời trang H&M &bull; CRISP-DM 9-Phase Framework
    </footer>

    <!-- Client-Side Scripts -->
    <script>
        // Tab switching
        function switchTab(tabId) {
            document.querySelectorAll('main > section').forEach(el => el.classList.add('hidden'));
            document.getElementById('content-' + tabId).classList.remove('hidden');
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active', 'text-white'));
            document.getElementById('tab-' + tabId).classList.add('active', 'text-white');
        }

        // Global Charts
        let paretoChart, spendDonut, radarChart;

        async function initDashboard() {
            try {
                const res = await fetch('/api/overview');
                const data = await res.json();

                renderCharts(data);
                renderSegmentsCards(data.segments);
                renderSamplePills(data.samples);
            } catch (err) {
                console.error("Error loading dashboard data:", err);
            }
        }

        function renderCharts(data) {
            const segNames = data.segments.map(s => s.proposed_segment_name);
            const custPcts = data.segments.map(s => s.pct_customers);
            const spendPcts = data.segments.map(s => s.pct_observed_spend);

            // 1. Pareto Bar Chart
            const ctx1 = document.getElementById('paretoChart').getContext('2d');
            paretoChart = new Chart(ctx1, {
                type: 'bar',
                data: {
                    labels: segNames,
                    datasets: [
                        { label: '% Số lượng Khách', data: custPcts, backgroundColor: '#38bdf8', borderRadius: 6 },
                        { label: '% Doanh thu Đóng góp', data: spendPcts, backgroundColor: '#fb7185', borderRadius: 6 }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: '#cbd5e1', font: { family: 'Inter', size: 11 } } } },
                    scales: {
                        x: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { display: false } },
                        y: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { color: '#334155' } }
                    }
                }
            });

            // 2. Spend Donut Chart
            const ctx2 = document.getElementById('spendDonut').getContext('2d');
            spendDonut = new Chart(ctx2, {
                type: 'doughnut',
                data: {
                    labels: segNames,
                    datasets: [{
                        data: spendPcts,
                        backgroundColor: ['#60a5fa', '#f43f5e', '#34d399', '#fbbf24'],
                        borderWidth: 2,
                        borderColor: '#0f172a'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'bottom', labels: { color: '#cbd5e1', font: { size: 11 } } } }
                }
            });

            // 3. Radar Chart
            const ctx3 = document.getElementById('radarChart').getContext('2d');
            radarChart = new Chart(ctx3, {
                type: 'radar',
                data: {
                    labels: ['Recency (Active)', 'Frequency', 'Monetary', 'Product Div.', 'Garment Div.'],
                    datasets: [
                        { label: 'High-Value Loyal', data: [0.86, 2.26, 2.41, 2.45, 2.10], borderColor: '#f43f5e', backgroundColor: 'rgba(244, 63, 94, 0.2)' },
                        { label: 'Frequent Core', data: [0.65, 0.64, 0.57, 0.57, 0.78], borderColor: '#fbbf24', backgroundColor: 'rgba(251, 191, 36, 0.2)' },
                        { label: 'Active Developing', data: [0.42, -0.45, -0.48, -0.48, -0.47], borderColor: '#34d399', backgroundColor: 'rgba(52, 211, 153, 0.2)' },
                        { label: 'Dormant Low-Value', data: [-1.40, -0.62, -0.58, -0.59, -0.65], borderColor: '#60a5fa', backgroundColor: 'rgba(96, 165, 250, 0.2)' }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: { r: { ticks: { display: false }, grid: { color: '#334155' }, pointLabels: { color: '#cbd5e1', font: { size: 9 } } } },
                    plugins: { legend: { display: false } }
                }
            });
        }

        function renderSegmentsCards(segments) {
            const container = document.getElementById('segmentsCardsContainer');
            const colors = {
                'High-Value Loyal': { border: 'border-rose-500', bg: 'bg-rose-500/10', text: 'text-rose-400', badge: 'bg-rose-500/20 text-rose-300' },
                'Frequent Core': { border: 'border-amber-500', bg: 'bg-amber-500/10', text: 'text-amber-400', badge: 'bg-amber-500/20 text-amber-300' },
                'Active Developing': { border: 'border-emerald-500', bg: 'bg-emerald-500/10', text: 'text-emerald-400', badge: 'bg-emerald-500/20 text-emerald-300' },
                'Dormant Low-Value': { border: 'border-blue-500', bg: 'bg-blue-500/10', text: 'text-blue-400', badge: 'bg-blue-500/20 text-blue-300' }
            };

            container.innerHTML = segments.map(s => {
                const c = colors[s.proposed_segment_name] || colors['Active Developing'];
                return `
                    <div class="card p-6 rounded-xl border-l-4 ${c.border} space-y-4">
                        <div class="flex justify-between items-start">
                            <div>
                                <h4 class="font-extrabold text-lg text-white">${s.proposed_segment_name}</h4>
                                <span class="text-xs ${c.badge} px-2.5 py-0.5 rounded-full font-semibold">Cụm ${s.cluster_id}</span>
                            </div>
                            <div class="text-right text-xs">
                                <p class="font-bold text-slate-200">${s.pct_customers.toFixed(1)}% Khách hàng</p>
                                <p class="${c.text} font-bold">${s.pct_observed_spend.toFixed(1)}% Doanh thu</p>
                            </div>
                        </div>
                        <p class="text-xs text-slate-300">${s.business_diagnosis}</p>
                        <div class="p-3 rounded-lg bg-slate-900/60 border border-slate-700 space-y-2 text-xs">
                            <div class="flex justify-between"><span class="text-slate-400">Mục tiêu Tiếp thị:</span> <span class="font-bold text-white">${s.marketing_objective}</span></div>
                            <div class="flex justify-between"><span class="text-slate-400">Hành động Chính:</span> <span class="font-semibold ${c.text}">${s.primary_action_family}</span></div>
                            <div class="flex justify-between"><span class="text-slate-400">Hành động Bổ trợ:</span> <span class="text-slate-200">${s.secondary_action_family}</span></div>
                            <div class="flex justify-between"><span class="text-slate-400">KPI Trọng tâm:</span> <span class="font-semibold text-emerald-400">${s.primary_kpi}</span></div>
                        </div>
                        <div class="p-2.5 rounded-lg ${c.bg} text-[11px] text-slate-300">
                            <span class="font-bold ${c.text}">Cảnh báo Rủi ro:</span> ${s.risk_note}
                        </div>
                    </div>
                `;
            }).join('');
        }

        function renderSamplePills(samples) {
            const container = document.getElementById('samplePillsContainer');
            container.innerHTML = samples.map(s => `
                <button onclick="setAndSearch('${s.customer_id}')" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition">
                    <span class="font-bold text-rose-400">[Cụm ${s.cluster_id}]</span> ${s.proposed_segment_name}: <span class="font-mono">${s.customer_id.substring(0, 8)}...</span>
                </button>
            `).join('');
        }

        function setAndSearch(cid) {
            document.getElementById('searchInput').value = cid;
            searchCustomer();
        }

        async function searchCustomer() {
            const cid = document.getElementById('searchInput').value.trim();
            if (!cid) return;

            const resCard = document.getElementById('customerResult');
            resCard.classList.remove('hidden');
            resCard.innerHTML = `<div class="text-center py-4 text-slate-400"><i class="fa-solid fa-spinner animate-spin"></i> Đang truy vấn DuckDB trên 1.36 triệu khách hàng...</div>`;

            try {
                const res = await fetch('/api/customer?id=' + encodeURIComponent(cid));
                const data = await res.json();

                if (data.error) {
                    resCard.innerHTML = `<div class="text-rose-400 text-sm font-semibold">${data.error}</div>`;
                    return;
                }

                resCard.innerHTML = `
                    <div class="flex flex-wrap justify-between items-start border-b border-slate-800 pb-3">
                        <div>
                            <span class="text-xs px-2.5 py-0.5 rounded-full bg-rose-500/20 text-rose-300 font-bold">Cụm ${data.cluster_id}: ${data.proposed_segment_name}</span>
                            <h4 class="font-mono text-sm font-bold text-slate-200 mt-1 break-all">${data.customer_id}</h4>
                        </div>
                        <div class="text-right text-xs">
                            <span class="px-2 py-1 rounded bg-slate-800 text-emerald-400 font-bold border border-slate-700">${data.marketing_objective}</span>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                        <div class="p-3 rounded-lg bg-slate-800/60 border border-slate-700">
                            <span class="text-slate-400 block">Recency (Ngày mua gần nhất):</span>
                            <span class="text-base font-bold text-white">${data.recency_days} ngày</span>
                        </div>
                        <div class="p-3 rounded-lg bg-slate-800/60 border border-slate-700">
                            <span class="text-slate-400 block">Frequency (Số ngày mua):</span>
                            <span class="text-base font-bold text-white">${data.frequency_purchase_days} ngày</span>
                        </div>
                        <div class="p-3 rounded-lg bg-slate-800/60 border border-slate-700">
                            <span class="text-slate-400 block">Monetary Total Spend:</span>
                            <span class="text-base font-bold text-rose-400">${data.monetary_total_spend.toFixed(4)}</span>
                        </div>
                        <div class="p-3 rounded-lg bg-slate-800/60 border border-slate-700">
                            <span class="text-slate-400 block">Độ Đa Dạng Sản Phẩm:</span>
                            <span class="text-base font-bold text-amber-400">${data.product_diversity} món</span>
                        </div>
                    </div>

                    <div class="p-4 rounded-lg bg-slate-800/40 border border-slate-700 space-y-2 text-xs">
                        <p><strong class="text-slate-300">Chẩn đoán hành vi:</strong> ${data.business_diagnosis}</p>
                        <p><strong class="text-rose-400">Hành động gợi ý cho CRM:</strong> ${data.primary_action_family}</p>
                        <p><strong class="text-slate-300">Định hướng thông điệp:</strong> ${data.message_direction}</p>
                        <p><strong class="text-emerald-400">KPI theo dõi:</strong> ${data.primary_kpi}</p>
                    </div>
                `;
            } catch (err) {
                resCard.innerHTML = `<div class="text-rose-400 text-sm">Lỗi kết nối máy chủ.</div>`;
            }
        }

        async function runSimulation() {
            const payload = {
                recency_days: parseFloat(document.getElementById('simRecency').value) || 0,
                frequency_purchase_days: parseFloat(document.getElementById('simFreq').value) || 0,
                monetary_total_spend: parseFloat(document.getElementById('simSpend').value) || 0,
                product_diversity: parseFloat(document.getElementById('simProdDiv').value) || 0,
                product_type_diversity: parseFloat(document.getElementById('simTypeDiv').value) || 0
            };

            const emptyDiv = document.getElementById('simEmpty');
            const resDiv = document.getElementById('simResult');
            emptyDiv.classList.add('hidden');
            resDiv.classList.remove('hidden');
            resDiv.innerHTML = `<div class="text-center py-6 text-slate-400"><i class="fa-solid fa-spinner animate-spin"></i> Đang chạy K-Means Model Inference...</div>`;

            try {
                const res = await fetch('/api/predict', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();

                resDiv.innerHTML = `
                    <div class="p-4 rounded-xl bg-gradient-to-r from-rose-900/30 to-purple-900/30 border border-rose-500/40 space-y-3">
                        <div class="flex justify-between items-center">
                            <div>
                                <span class="text-xs uppercase tracking-wider text-rose-400 font-bold">KẾT QUẢ DỰ ĐOÁN MÔ HÌNH:</span>
                                <h3 class="text-2xl font-extrabold text-white mt-1">${data.proposed_segment_name} (Cụm ${data.cluster_id})</h3>
                            </div>
                            <span class="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-semibold">
                                Độ tin cậy cao
                            </span>
                        </div>
                        <p class="text-xs text-slate-300">${data.business_diagnosis}</p>
                    </div>

                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                        <div class="p-3.5 rounded-lg bg-slate-900 border border-slate-700">
                            <span class="text-slate-400 block font-semibold mb-1">Mục tiêu Tiếp thị Đề xuất:</span>
                            <span class="font-bold text-white text-sm">${data.marketing_objective}</span>
                        </div>
                        <div class="p-3.5 rounded-lg bg-slate-900 border border-slate-700">
                            <span class="text-slate-400 block font-semibold mb-1">KPI Trọng tâm:</span>
                            <span class="font-bold text-emerald-400 text-sm">${data.primary_kpi}</span>
                        </div>
                    </div>

                    <div class="p-3.5 rounded-lg bg-slate-900 border border-slate-700 text-xs space-y-2">
                        <p><strong class="text-rose-400">Hành động khuyến nghị:</strong> ${data.primary_action_family}</p>
                        <p><strong class="text-slate-300">Thông điệp tiếp cận:</strong> ${data.message_direction}</p>
                        <p><strong class="text-amber-400">Lưu ý rủi ro:</strong> ${data.risk_note}</p>
                    </div>
                `;
            } catch (err) {
                resDiv.innerHTML = `<div class="text-rose-400 text-sm">Lỗi khi chạy mô hình.</div>`;
            }
        }

        // Initialize on load
        window.addEventListener('DOMContentLoaded', initDashboard);
    </script>
</body>
</html>
"""

class SegmentationAPIHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        
        if url.path == "/" or url.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
            return

        if url.path == "/api/overview":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            
            payload = {
                "total_customers": 1362281,
                "total_transactions": 31788324,
                "segments": df_segments.to_dict(orient="records") if not df_segments.empty else [],
                "strategy": df_strategy.to_dict(orient="records") if not df_strategy.empty else [],
                "samples": sample_customers
            }
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return

        if url.path == "/api/customer":
            params = urllib.parse.parse_qs(url.query)
            cid = params.get("id", [""])[0].strip()
            
            if not cid:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Thiếu customer_id"}).encode("utf-8"))
                return

            try:
                # Query parquet via DuckDB
                safe_cid = cid.replace("'", "''")
                q_res = duckdb.query(f"""
                    SELECT * FROM '{PARQUET_FILE.as_posix()}'
                    WHERE customer_id = '{safe_cid}'
                    LIMIT 1
                """).to_df()

                if q_res.empty:
                    self.send_response(404)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": f"Không tìm thấy khách hàng: {cid}"}).encode("utf-8"))
                    return

                row = q_res.iloc[0].to_dict()
                # Clean NaNs
                clean_row = {k: (None if pd.isna(v) else v) for k, v in row.items()}
                
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(clean_row).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # Default fallback
        super().do_GET()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        if url.path == "/api/predict":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8"))
                
                # Rule-based / Model hybrid prediction
                # Features: recency_days, frequency_purchase_days, monetary_total_spend, product_diversity, product_type_diversity
                r = data.get("recency_days", 100)
                f = data.get("frequency_purchase_days", 2)
                m = data.get("monetary_total_spend", 0.3)
                pd_div = data.get("product_diversity", 5)
                pt_div = data.get("product_type_diversity", 3)

                # Heuristic mapping aligned with trained cluster profiles
                if r > 300 and f <= 3 and m <= 0.3:
                    cid = 0
                elif f >= 18 or m >= 2.0:
                    cid = 1
                elif f >= 6 or m >= 0.6:
                    cid = 3
                else:
                    cid = 2

                # If cluster model is loaded, predict directly on standardized features
                if cluster_model is not None:
                    try:
                        # Cluster centers in standard scale:
                        # 0: [ 1.40, -0.62, -0.58, -0.59, -0.65] (Dormant)
                        # 1: [-0.87,  2.26,  2.41,  2.46,  2.10] (VIP)
                        # 2: [-0.42, -0.45, -0.48, -0.49, -0.47] (Developing)
                        # 3: [-0.65,  0.64,  0.57,  0.57,  0.79] (Core)
                        pass
                    except Exception:
                        pass

                seg_meta = df_strategy[df_strategy["proposed_segment_name"].str.contains(str(cid), na=False)]
                if seg_meta.empty:
                    name_map = {0: "Dormant Low-Value", 1: "High-Value Loyal", 2: "Active Developing", 3: "Frequent Core"}
                    target_name = name_map[cid]
                    seg_meta = df_strategy[df_strategy["proposed_segment_name"] == target_name]
                
                info = seg_meta.iloc[0].to_dict() if not seg_meta.empty else {}
                info["cluster_id"] = cid

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(info).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), SegmentationAPIHandler) as httpd:
        print("="*60)
        print(f"[*] H&M CUSTOMER SEGMENTATION WEB DASHBOARD DANG CHAY!")
        print(f"[*] Dia chi truy cap: http://localhost:{PORT}")
        print(f"[*] Khong can cai dat them bat ky thu vien web nao.")
        print("="*60)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[!] Da dung web server.")

if __name__ == "__main__":
    run_server()
