from pathlib import Path

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "processed" / "HR_cleaned.csv"

st.set_page_config(page_title="HR Dashboard", layout="wide")


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    df.columns = [col.strip() for col in df.columns]

    for col in ["StartDate", "ExitDate"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    if "EmployeeStatus" in df.columns:
        df["EmployeeStatus"] = (
            df["EmployeeStatus"]
            .fillna("Active")
            .astype(str)
            .str.strip()
            .str.title()
            .replace({
                "Future Start": "Active",
                "Leave Of Absence": "Active",
                "Voluntarily Terminated": "Terminated",
                "Terminated For Cause": "Terminated",
                "Active\r": "Active",
            })
        )

    if "DepartmentType" in df.columns:
        df["DepartmentType"] = df["DepartmentType"].fillna("Unknown").astype(str).str.strip()

    if "Current Employee Rating" in df.columns:
        df["Current Employee Rating"] = pd.to_numeric(df["Current Employee Rating"], errors="coerce")

    numeric_score_cols = [
        "Engagement Score",
        "Satisfaction Score",
        "Work-Life Balance Score",
        "Current Employee Rating",
    ]
    for col in numeric_score_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "StartDate" in df.columns:
        df["TenureYears"] = (pd.Timestamp.now().tz_localize(None) - df["StartDate"]).dt.days / 365.25
        df["TenureYears"] = df["TenureYears"].clip(lower=0)

    return df


def render_dashboard(data):
    st.title("HR Workforce Dashboard")
    st.caption("Interactive insights into staffing, engagement, and employee status trends.")

    status_options = sorted(data["EmployeeStatus"].dropna().unique().tolist()) if "EmployeeStatus" in data.columns else ["Active"]
    dept_options = sorted(data["DepartmentType"].dropna().unique().tolist()) if "DepartmentType" in data.columns else []
    business_options = sorted(data["BusinessUnit"].dropna().unique().tolist()) if "BusinessUnit" in data.columns else []
    gender_options = sorted(data["GenderCode"].dropna().unique().tolist()) if "GenderCode" in data.columns else []

    with st.sidebar:
        st.header("Filters")
        selected_status = st.multiselect("Employee status", status_options, default=status_options)
        selected_dept = st.multiselect("Department type", dept_options, default=dept_options)
        selected_business = st.multiselect("Business unit", business_options, default=business_options)
        selected_gender = st.multiselect("Gender", gender_options, default=gender_options)

    filtered = data.copy()
    if selected_status:
        filtered = filtered[filtered["EmployeeStatus"].isin(selected_status)]
    if selected_dept:
        filtered = filtered[filtered["DepartmentType"].isin(selected_dept)]
    if selected_business:
        filtered = filtered[filtered["BusinessUnit"].isin(selected_business)]
    if selected_gender:
        filtered = filtered[filtered["GenderCode"].isin(selected_gender)]

    if filtered.empty:
        st.warning("No records match the selected filters. Adjust the filters to view the dashboard.")
        return

    total_employees = len(filtered)
    active_count = int(filtered["EmployeeStatus"].eq("Active").sum()) if "EmployeeStatus" in filtered.columns else total_employees
    avg_satisfaction = filtered["Satisfaction Score"].mean() if "Satisfaction Score" in filtered.columns else 0
    attrition_rate = (filtered["EmployeeStatus"].eq("Terminated").mean() * 100) if "EmployeeStatus" in filtered.columns else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total employees", f"{total_employees:,}")
    col2.metric("Active employees", f"{active_count:,}")
    col3.metric("Avg. satisfaction", f"{avg_satisfaction:.1f}/5")
    col4.metric("Attrition rate", f"{attrition_rate:.1f}%")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        dept_counts = filtered["DepartmentType"].value_counts().reset_index()
        dept_counts.columns = ["DepartmentType", "Employees"]
        dept_counts = dept_counts.sort_values("Employees", ascending=False)
        st.subheader("Headcount by department")
        st.plotly_chart(px.bar(dept_counts, x="DepartmentType", y="Employees", color="DepartmentType", title="Employees by department"), use_container_width=True)

    with chart_col2:
        if "DepartmentType" in filtered.columns and "EmployeeStatus" in filtered.columns:
            attrition = (
                filtered.groupby("DepartmentType")["EmployeeStatus"]
                .apply(lambda s: (s == "Terminated").mean() * 100)
                .reset_index(name="AttritionRate")
                .sort_values("AttritionRate", ascending=False)
            )
            st.subheader("Attrition by department")
            st.plotly_chart(px.bar(attrition, x="DepartmentType", y="AttritionRate", color="DepartmentType", title="Attrition rate by department"), use_container_width=True)

    scatter_col, tenure_col = st.columns(2)

    with scatter_col:
        if {"Engagement Score", "Satisfaction Score"}.issubset(filtered.columns):
            st.subheader("Engagement vs. satisfaction")
            scatter = px.scatter(
                filtered,
                x="Engagement Score",
                y="Satisfaction Score",
                color="EmployeeStatus",
                hover_data=["DepartmentType", "BusinessUnit", "GenderCode"],
                title="Engagement and satisfaction by employee status"
            )
            st.plotly_chart(scatter, use_container_width=True)

    with tenure_col:
        if "TenureYears" in filtered.columns:
            st.subheader("Tenure distribution")
            tenure_fig = px.histogram(
                filtered,
                x="TenureYears",
                nbins=20,
                color="EmployeeStatus",
                title="Employee tenure distribution"
            )
            st.plotly_chart(tenure_fig, use_container_width=True)

    st.subheader("Recent employee data")
    display_df = filtered.copy()
    for col in ["StartDate", "ExitDate"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].dt.strftime("%Y-%m-%d")
    st.dataframe(display_df.head(12), use_container_width=True)


def main():
    data = load_data()
    render_dashboard(data)


if __name__ == "__main__":
    main()
