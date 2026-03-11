import streamlit as st
import pandas as pd
import numpy as np

# --- CONFIGURATION & PREMIUM UI ---
st.set_page_config(page_title="Weekly QA Command Center", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a !important; }
    h1, h2, h3, p, label, span, div { color: #ffffff !important; font-family: 'Inter', sans-serif; }
    
    /* Metrics Styling */
    div[data-testid="stMetric"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 12px;
        padding: 20px;
    }
    [data-testid="stMetricValue"] { color: #38bdf8 !important; font-size: 2rem !important; }

    /* Premium Export Button */
    div.stDownloadButton > button {
        background-color: #0ea5e9 !important;
        color: white !important;
        border-radius: 8px !important;
        width: 100% !important;
        font-weight: bold !important;
        padding: 12px !important;
        border: none !important;
    }

    /* Table Styling */
    .dashboard-table {
        width: 100%;
        border-collapse: collapse;
        background-color: #1e293b;
        color: white;
        border-radius: 12px;
        overflow: hidden;
    }
    .dashboard-table th { background-color: #334155; color: #94a3b8; padding: 15px; text-align: left; }
    .dashboard-table td { padding: 12px 15px; border-bottom: 1px solid #334155; }
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

def load_and_clean(files):
    all_dfs = []
    for f in files:
        temp_df = pd.read_csv(f)
        temp_df.columns = [c.split(':')[-1].strip() for c in temp_df.columns]
        all_dfs.append(temp_df)
    df = pd.concat(all_dfs, ignore_index=True)
    df['Mapped_WF'] = df['Transformation Type'].map(WF_MAPPING)
    aht_col = "Average Handle Time(In Secs)"
    df[aht_col] = pd.to_numeric(df[aht_col], errors='coerce')
    return df, aht_col

# --- HEADER ---
st.title("🛡️ Weekly QA Command Center")
st.subheader("Monday Morning Planning & Capacity Projection")

with st.expander("📂 Step 1: Upload Historical Metrics (Jan/Feb)", expanded=True):
    uploaded_files = st.file_uploader("Drop Mercury CSV files", type="csv", accept_multiple_files=True)

if uploaded_files:
    df, aht_col = load_and_clean(uploaded_files)
    metrics = df[df[aht_col] > 0].groupby('Mapped_WF')[aht_col].apply(lambda x: x[x <= x.quantile(0.95)].mean()).reset_index()
    overall_avg = metrics[aht_col].median()
    all_wfs = pd.DataFrame({'Mapped_WF': list(WF_MAPPING.values())}).drop_duplicates()
    final_metrics = all_wfs.merge(metrics, on='Mapped_WF', how='left').fillna(overall_avg)

    st.markdown("---") # Replaced st.divider()
    col_sidebar, col_main = st.columns([1, 2.5])
    
    with col_sidebar:
        st.header("⚙️ Weekly Setup")
        qas = st.number_input("Total Available QAs", min_value=1, value=7)
        prod_h = st.slider("Productive Hours / Day", 4.0, 8.5, 7.5, step=0.25)
        weekly_team_hours_limit = qas * prod_h * 5 
        
        st.write("---")
        st.write("**Target Weekly Volumes**")
        march_vols = {wf: st.number_input(f"{wf}", value=0, step=100, key=f"in_{wf}") for wf in WF_MAPPING.values()}

    with col_main:
        st.header("📊 Projected Requirements")
        results = []
        total_hours_needed = 0
        
        for wf_name in WF_MAPPING.values():
            aht = final_metrics.loc[final_metrics['Mapped_WF'] == wf_name, aht_col].values[0]
            vol = march_vols[wf_name]
            total_h = (vol * aht) / 3600
            total_hours_needed += total_h
            man_days = total_h / prod_h
            
            # --- YOUR EXACT STATUS LOGIC ---
            status_val = "✅ Safe" if man_days <= (qas * 5) else "🚨 Critical"
            status_class = "status-safe" if status_val == "✅ Safe" else "status-critical"
            
            results.append({
                "Workflow": wf_name,
                "AHT (Sec)": round(aht, 2),
                "Volume": vol,
                "Hours Needed": round(total_h, 2),
                "Man-Days Needed": round(man_days, 2),
                "Status": f'<span class="{status_class}">{status_val}</span>'
            })
        
        # Summary Cards
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Hours Needed", f"{total_hours_needed:.2f}")
        m2.metric("Team Capacity (Wk)", f"{weekly_team_hours_limit:.2f}")
        util_pct = (total_hours_needed / weekly_team_hours_limit * 100) if weekly_team_hours_limit > 0 else 0
        m3.metric("Utilization", f"{util_pct:.2f}%")
        
        # HTML Rendered Table for Stability
        res_df = pd.DataFrame(results)
        st.write(res_df.to_html(index=False, escape=False, classes="dashboard-table"), unsafe_allow_html=True)
        
        st.write("---")
        # Verdict Alerts
        if util_pct > 100:
            st.error(f"⚠️ Over Capacity: {util_pct:.2f}% Utilization.")
        else:
            st.success(f"🟢 Healthy Plan: {util_pct:.2f}% Utilization.")

        # Export Button - Clean logic
        export_df = pd.DataFrame(results)
        # Remove HTML tags from Exported CSV Status
        export_df['Status'] = export_df['Status'].str.replace(r'<[^>]*>', '', regex=True)
        csv_data = export_df.to_csv(index=False).encode('utf-8')
        st.download_button("📤 EXPORT WEEKLY REPORT (CSV)", csv_data, "Weekly_QA_Plan.csv", "text/csv")
else:
    st.info("👋 Upload Mercury files to begin.")
