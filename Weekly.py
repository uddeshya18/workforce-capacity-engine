import streamlit as st
import pandas as pd

# --- DASHBOARD CONFIG & DARK THEME ---
st.set_page_config(page_title="QA Command Center", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a !important; } 
    h1, h2, h3, p, label, span, div { color: #ffffff !important; font-family: 'Inter', sans-serif; }
    
    /* Metrics/Card Styling */
    div[data-testid="stMetric"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 12px;
        padding: 20px;
    }
    [data-testid="stMetricValue"] { color: #38bdf8 !important; font-size: 2rem !important; }

    /* Custom Export Button Styling */
    div.stDownloadButton > button {
        background-color: #0ea5e9 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 10px 24px !important;
        font-weight: bold !important;
    }
    div.stDownloadButton > button:hover {
        background-color: #0284c7 !important;
        color: white !important;
    }

    /* HTML Table Styling */
    .dashboard-table {
        width: 100%;
        border-collapse: collapse;
        background-color: #1e293b;
        border-radius: 12px;
        overflow: hidden;
        color: white;
    }
    .dashboard-table th {
        background-color: #334155;
        color: #94a3b8;
        padding: 15px;
        text-align: left;
    }
    .dashboard-table td {
        padding: 12px 15px;
        border-bottom: 1px solid #334155;
    }
    .status-safe { color: #4ade80; font-weight: bold; }
    .status-critical { color: #f87171; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

WF_MAPPING = {
    "ScreenRendering MM ARQ7 LS": "ScreenRendering MM ARQ7 LS",
    "Binary pref rating of target turn w ref voice V2 - ADS LS": "Binary pref rating of target turn w ref voice V2 - ADS LS",
    "ARQ7-2Pass-with-H2H-Adjudication LS": "ARQ7-2Pass-with-H2H-Adjudication LS",
    "FaceCropAnnotationVID": "FaceCropAnnotationVID",
    "Banyan-EFD-Query-Evaluation-Workflow-S3 LS": "Banyan-EFD-Query-Evaluation-Workflow-S3 LS",
    "ARQ7-AI": "ARQ7-AI",
    "Conversational ARQ7 LS": "Conversational ARQ7",
    "PACE-PRQ-Metis-1P-DAs-Latest LS": "Pace-PRQ-Metis"
}

def load_data(files):
    all_dfs = []
    for f in files:
        df = pd.read_csv(f)
        df.columns = [c.split(':')[-1].strip() for c in df.columns]
        all_dfs.append(df)
    combined = pd.concat(all_dfs, ignore_index=True)
    combined['Mapped_WF'] = combined['Transformation Type'].map(WF_MAPPING)
    aht_col = "Average Handle Time(In Secs)"
    combined[aht_col] = pd.to_numeric(combined[aht_col], errors='coerce')
    return combined, aht_col

st.title("🛡️ Weekly Command Center")

files = st.file_uploader("Step 1: Upload Mercury Metrics", type="csv", accept_multiple_files=True)

if files:
    df, aht_col = load_data(files)
    metrics = df[df[aht_col] > 0].groupby('Mapped_WF')[aht_col].apply(lambda x: x[x <= x.quantile(0.95)].mean()).reset_index()
    overall_avg = metrics[aht_col].median()
    all_wfs = pd.DataFrame({'Mapped_WF': list(WF_MAPPING.values())}).drop_duplicates()
    final_metrics = all_wfs.merge(metrics, on='Mapped_WF', how='left').fillna(overall_avg)

    col_setup, col_viz = st.columns([1, 2.5])

    with col_setup:
        st.subheader("⚙️ Weekly Setup")
        qas = st.number_input("Total Available QAs", min_value=1, value=5)
        prod_h = st.slider("Productive Hours / Day", 4.0, 8.5, 7.5, step=0.25)
        weekly_cap = qas * prod_h * 5
        st.write("---")
        vols = {wf: st.number_input(f"Vol: {wf}", value=0, key=f"vol_{wf}") for wf in WF_MAPPING.values()}

    with col_viz:
        st.subheader("📊 Projected Requirements")
        
        # Calculate Logic
        results = []
        total_h_needed = 0
        for wf in WF_MAPPING.values():
            aht = final_metrics.loc[final_metrics['Mapped_WF'] == wf, aht_col].values[0]
            vol = vols[wf]
            hrs = (vol * aht) / 3600
            total_h_needed += hrs
            
            # Individual Status Logic
            # A workflow is "Critical" if it alone takes more than 50% of total team capacity
            status = "✅ Safe" if hrs < (weekly_cap * 0.5) else "🚨 Critical"
            status_class = "status-safe" if status == "✅ Safe" else "status-critical"
            
            results.append({
                "Workflow": wf,
                "AHT (Sec)": round(aht, 2),
                "Volume": vol,
                "Hours Needed": round(hrs, 2),
                "Man-Days Needed": round(hrs / prod_h, 2),
                "Status": f'<span class="{status_class}">{status}</span>'
            })

        # Metric Header Row
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Hours Needed", f"{total_h_needed:.2f}")
        m2.metric("Team Capacity (Wk)", f"{weekly_cap:.2f}")
        util = (total_h_needed / weekly_cap * 100) if weekly_cap > 0 else 0
        m3.metric("Utilization", f"{util:.2f}%")

        # Table Section
        res_df = pd.DataFrame(results)
        st.write(res_df.to_html(index=False, escape=False, classes="dashboard-table"), unsafe_allow_html=True)
        
        st.write("") 
        
        # Action Footer
        if util > 100:
            st.error(f"⚠️ Over Capacity: Utilization is at {util:.2f}%. Reduce volume or increase hours.")
        else:
            st.success(f"🟢 Healthy Plan: Utilization is at {util:.2f}%. Load is balanced.")
            
        st.download_button("📤 EXPORT REPORT", res_df.to_csv(index=False), "QA_Weekly_Plan.csv")

else:
    st.info("Please upload Mercury CSV files from January and February to generate AHT baselines.")
