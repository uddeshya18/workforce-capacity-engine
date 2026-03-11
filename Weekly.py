import streamlit as st
import pandas as pd
import numpy as np
import re

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

    /* Standard Sized Left-Aligned Button */
    div.stDownloadButton {
        text-align: left;
    }
    div.stDownloadButton > button {
        background-color: #0ea5e9 !important;
        color: white !important;
        border-radius: 6px !important;
        width: auto !important; /* Makes it a normal sized button */
        padding: 8px 20px !important;
        font-weight: bold !important;
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

st.title("🛡️ Weekly QA Command Center")

with st.expander("📂 Step 1: Upload Historical Metrics (Jan/Feb)", expanded=True):
    uploaded_files = st.file_uploader("Drop Mercury CSV files", type="csv", accept_multiple_files=True)

if uploaded_files:
    df, aht_col = load_and_clean(uploaded_files)
    metrics = df[df[aht_col] > 0].groupby('Mapped_WF')[aht_col].apply(lambda x: x[x <= x.quantile(0.95)].mean()).reset_index()
    overall_avg = metrics[aht_col].median()
    all_wfs = pd.DataFrame({'Mapped_WF': list(WF_MAPPING.values())}).drop_duplicates()
    final_metrics = all_wfs.merge(metrics, on='Mapped_WF', how='left').fillna(overall_avg)

    st.markdown("---")
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
            
            # YOUR STATUS LOGIC
            status_val = "Safe" if man_days <= (qas * 5) else "Critical"
            emoji = "✅ " if status_val == "Safe" else "🚨 "
            status_class = "status-safe" if status_val == "Safe" else "status-critical"
            
            results.append({
                "Workflow": wf_name,
                "AHT (Sec)": round(aht, 2),
                "Volume": vol,
                "Hours Needed": round(total_h, 2),
                "Man-Days Needed": round(man_days, 2),
                "Status": f'<span class="{status_class}">{emoji}{status_val}</span>',
                "Plain_Status": status_val # Hidden column for CSV export
            })
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Hours Needed", f"{total_hours_needed:.2f}")
        m2.metric("Team Capacity (Wk)", f"{weekly_team_hours_limit:.2f}")
        util_pct = (total_hours_needed / weekly_team_hours_limit * 100) if weekly_team_hours_limit > 0 else 0
        m3.metric("Utilization", f"{util_pct:.2f}%")
        
        res_df = pd.DataFrame(results)
        # Show table WITHOUT the hidden Plain_Status column
        display_df = res_df.drop(columns=['Plain_Status'])
        st.write(display_df.to_html(index=False, escape=False, classes="dashboard-table"), unsafe_allow_html=True)
        
        st.write("---")
        
        # CLEAN CSV EXPORT LOGIC
        # We create a specific dataframe for export that doesn't have HTML tags
        export_df = res_df.copy()
        export_df['Status'] = export_df['Plain_Status']
        export_df = export_df.drop(columns=['Plain_Status'])
        
        # utf-8-sig makes it open perfectly in Excel without weird characters
        csv_data = export_df.to_csv(index=False).encode('utf-8-sig')
        
        st.download_button(
            label="📥 Export Report",
            data=csv_data,
            file_name="QA_Weekly_Plan.csv",
            mime="text/csv"
        )
