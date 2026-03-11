import streamlit as st
import pandas as pd

# --- FORCED WHITE THEME ---
st.set_page_config(page_title="QA Command Center", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    h1, h2, h3, p, label, span, div { color: #000000 !important; }
    div[data-testid="stMetric"] {
        background-color: #F8F9FA !important;
        border: 1px solid #000000 !important;
        border-radius: 8px;
    }
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

uploaded_files = st.file_uploader("Upload Historical CSV Files", type="csv", accept_multiple_files=True)

if uploaded_files:
    df, aht_col = load_data(uploaded_files)
    metrics = df[df[aht_col] > 0].groupby('Mapped_WF')[aht_col].apply(lambda x: x[x <= x.quantile(0.95)].mean()).reset_index()
    overall_avg = metrics[aht_col].median()
    all_wfs = pd.DataFrame({'Mapped_WF': list(WF_MAPPING.values())}).drop_duplicates()
    final_metrics = all_wfs.merge(metrics, on='Mapped_WF', how='left').fillna(overall_avg)

    tab1, tab2 = st.tabs(["📅 Capacity Planner", "📊 AHT Variance Report"])

    with tab1:
        c1, c2 = st.columns([1, 2.5])
        with c1:
            qas = st.number_input("Total QAs", min_value=1, value=7)
            prod_h = st.slider("Productive Hours/Day", 4.0, 8.0, 6.5, step=0.5)
            weekly_cap = qas * prod_h * 5
            st.write("---")
            vols = {wf: st.number_input(f"Vol: {wf}", value=0) for wf in WF_MAPPING.values()}
        
        with c2:
            results = []
            total_h = 0
            for wf in WF_MAPPING.values():
                aht = final_metrics.loc[final_metrics['Mapped_WF'] == wf, aht_col].values[0]
                hrs = (vols[wf] * aht) / 3600
                total_h += hrs
                results.append({"Workflow": wf, "AHT": aht, "Vol": vols[wf], "Hrs": hrs})
            
            util = (total_h / weekly_cap * 100) if weekly_cap > 0 else 0
            m1, m2, m3 = st.columns(3)
            m1.metric("Load (Hrs)", f"{total_h:.2f}")
            m2.metric("Capacity (Hrs)", f"{weekly_cap:.2f}")
            m3.metric("Utilization", f"{util:.2f}%")
            
            res_df = pd.DataFrame(results)
            res_df["Man-Days"] = (res_df["Hrs"] / prod_h).map(lambda x: f"{float(x):.2f}")
            res_df["Status"] = "🚨 OVER" if util > 100 else "✅ SAFE"
            st.table(res_df)
            st.download_button("Download CSV", res_df.to_csv(index=False), "Weekly_Plan.csv")

    with tab2:
        st.subheader("AHT Comparison")
        var_list = []
        for wf in WF_MAPPING.values():
            pred = final_metrics.loc[final_metrics['Mapped_WF'] == wf, aht_col].values[0]
            act = st.number_input(f"Actual AHT: {wf}", value=float(pred), key=f"v_{wf}")
            var_list.append({"Workflow": wf, "Predicted": f"{pred:.2f}", "Actual": f"{act:.2f}", "Diff": f"{act-pred:+.2f}"})
        st.table(pd.DataFrame(var_list))
else:
    st.info("Upload files to start.")