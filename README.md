---
# Leave whatever original metadata configuration was up here exactly as it was
---

## 📦 Part of the Operations Excellence Suite

This repository is an independent component of a modular, three-tier ecosystem designed to handle end-to-end workforce optimization and capacity logistics:

1. **🌐 [Global Load Balancer](https://github.com/uddeshya18/ops-global-load-balancer):** Manages multi-site resource routing, high-level queue balancing, and macro-level SLA parity across diverse locales.
2. **🧮 [Workforce Capacity Engine (This Tool)](https://github.com/uddeshya18/workforce-capacity-engine):** Handles granular, localized micro-headcount requirements using 95th-percentile trimmed-mean AHT modeling.
3. **📈 [Demand Forecast Simulator ](#):** Executes 4-week look-ahead predictive volume modeling and "What-If" growth scenario testing based on historical trends.

---

# Capacity-Planning
## 📊 Strategic Capacity Planner



# 🛡️ Weekly QA Command Center
### Dynamic Resource Allocation & Capacity Modeling

A premium **Streamlit** dashboard designed for real-time operational management. This tool automates the complex task of workforce planning by mapping live demand against team bandwidth, ensuring SLA compliance through data-driven utilization tracking.

## 🎯 Strategic Impact
* **Utilization Optimization:** Prevents over-burn by calculating real-time team saturation percentages.
* **Risk Mitigation:** Automatically flags "Critical" workflows where projected volume exceeds man-day capacity.
* **Data Integrity:** Implements a 95th-percentile AHT filter to eliminate statistical outliers, ensuring forecasting is based on stable, realistic performance metrics.

## 🏗️ Core Engineering Logic
* **Stateful Planning:** Integrates user-defined inputs (Total QAs, Productive Hours) with historical data to generate instantaneous gap analyses.
* **Custom UI/UX:** Built with a high-premium dark theme using custom CSS injection for an "Executive Command Center" experience.
* **Dynamic Visualization:** Employs conditional formatting to highlight utilization risks (Metric values automatically transition to **Red** when exceeding 100% capacity).
* **Automated Reporting:** Features a localized export engine to generate CSV reports for stakeholder alignment.

## 🧮 Technical Formula
The core planning engine operates on the following resource model:

$$\text{Capacity (Weekly Hours)} = \text{Available QAs} \times \text{Daily Productive Hours} \times 5$$

$$\text{Utilization \%} = \left( \frac{\sum (\text{Projected Volume} \times \text{AHT})}{\text{Total Capacity}} \right) \times 100$$

## 🛠️ Tech Stack
* **Frontend:** Streamlit (UI & State Management)
* **Data Processing:** Pandas, NumPy
* **Styling:** Custom CSS (Flex-box Banners, Dark Mode, High-Contrast Metrics)
* **Version Control:** Git

## 🚀 Usage Workflow
1. **Import:** Upload historical performance CSVs to establish AHT baselines.
2. **Configure:** Define team constraints (Headcount and Productive Hours).
3. **Forecast:** Enter projected weekly volumes for specific workflows (e.g., ARQ7, ScreenRendering).
4. **Action:** Analyze the **Status Banner** for "Healthy" vs "Over-Capacity" warnings and export the final plan.

---
*Developed for high-stakes operational environments to replace legacy spreadsheet dependency.*
