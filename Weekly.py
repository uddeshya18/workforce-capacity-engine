import streamlit as st
import pandas as pd

# --- STABLE DARK MODE CONFIG ---
st.set_page_config(page_title="QA Command Center", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a !important; } /* Darker Slate */
    h1, h2, h3, p, label, span, div { color: #ffffff !important; }
    
    /* Metrics Styling */
    div[data-testid="stMetric"] {
        background-color: #1e293b !important;
        border: 2px solid #334155 !important;
        border-radius: 10px;
        padding: 15px;
    }
    [data-testid="stMetricValue"] { color: #38bdf8 !important; font-weight: bold; }
    
    /* STABLE HTML TABLE STYLING - This replaces the broken interactive tables */
    table {
        width: 100%;
        border-collapse: collapse;
        color: white;
        background-color: #1e293b;
        border-radius: 8px;
        overflow: hidden;
    }
    th {
        background-color: #334155;
        color: #38bdf8;
        text-align: left;
        padding: 12px;
    }
    td {
        padding: 10px;
        border-bottom: 1px solid #334155;
    }
    tr:hover { background-color: #2d3e50; }
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

st.title("🛡️ QA Weekly Command Center")

files = st.file_uploader("Upload Historical CSVs", type="csv", accept_multiple_files=True)

if files:
    df, aht_col = load_data(files)
    metrics = df[df[aht_col] > 0].groupby('Mapped_WF')[aht_col].apply(lambda x: x[x <= x.quantile(0.95)].mean()).reset_index()
    overall_avg = metrics[aht_col].median()
    all_wfs = pd.DataFrame({'Mapped_WF': list(WF_MAPPING.values())}).drop_duplicates()
    final_metrics = all_wfs.merge(metrics, on='Mapped_WF', how='left').fillna(overall_avg)

    col_in, col_out = st.columns([1, 2.5])
    
    with col_in:
        st.subheader("Team Setup")
        qas = st.number_input("Total QAs", min_value=1, value=7)
        prod_h = st.slider("Productive Hours/Day", 4.0, 8.0, 6.5, step=0.5)
        weekly_cap = qas * prod_h * 5
        st.write("---")
        vols = {wf: st.number_input(f"Vol: {wf}", value=0) for wf in WF_MAPPING.values()}

    with col_out:
        results = []
        total_h = 0
        for wf in WF_MAPPING.values():
            aht = final_metrics.loc[final_metrics['Mapped_WF'] == wf, aht_col].values[0]
            hrs = (vols[wf] * aht) / 3600
            total_h += hrs
            results.append({
                "Workflow": wf, 
                "AHT": f"{aht:.2f}", 
                "Volume": vols[wf], 
                "Work (Hrs)": f"{hrs:.2f}",
                "Man-Days": f"{(hrs/prod_h):.2f}",
                "Status": "🚨 OVER" if (total_h / weekly_cap) > 1 else "✅ SAFE"
            })
        
        util = (total_h / weekly_cap * 100) if weekly_cap > 0 else 0
        m1, m2, m3 = st.columns(3)
        m1.metric("Required Hrs", f"{total_h:.2f}")
        m2.metric("Available Hrs", f"{weekly_cap:.2f}")
        m3.metric("Utilization", f"{util:.2f}%")
        
        # WE ARE USING st.write(df.to_html()) INSTEAD OF st.table()
        # This is a bulletproof way to avoid that Red Box error
        res_df = pd.DataFrame(results)
        st.write(res_df.to_html(index=False, escape=False), unsafe_allow_html=True)
        
        st.write("") # Spacer
        st.download_button("📥 Download Report", res_df.to_csv(index=False), "Weekly_Plan.csv")
else:
    st.info("Upload your Mercury CSV files to get started.")
