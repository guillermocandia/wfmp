import streamlit as st

from data import load_data

st.set_page_config(page_title="WFMP", page_icon="📊", layout="wide")

st.title("WFMP — Arcanes and Mods prices")

with st.sidebar:
    st.subheader("Navigation")
    if "page" not in st.session_state:
        st.session_state.page = "Data"
    if st.button("Data"):
        st.session_state.page = "Data"
    if st.button("Arcanes"):
        st.session_state.page = "Arcanes"
    if st.button("Mods"):
        st.session_state.page = "Mods"

page = st.session_state.get("page", "Data")

if "arcanes_df" not in st.session_state:
    st.session_state["arcanes_df"] = None
if "mods_df" not in st.session_state:
    st.session_state["mods_df"] = None

if page == "Data":
    col_buttons, col_msgs = st.columns([1, 2])

    with col_buttons:
        load_clicked = st.button("Load Data")
        clear_clicked = st.button("Clear Data")

        if load_clicked:
            try:
                arcanes_df, mods_df = load_data()
                st.session_state["arcanes_df"] = arcanes_df
                st.session_state["mods_df"] = mods_df
                st.success("Data loaded")
            except Exception as e:
                st.error(f"Failed to load data: {e}")
        elif clear_clicked:
            st.session_state["arcanes_df"] = None
            st.session_state["mods_df"] = None
            try:
                st.cache_data.clear()
            except Exception:
                pass
            st.info("Data and cache cleared")

        if (
            st.session_state.get("arcanes_df") is not None
            or st.session_state.get("mods_df") is not None
        ):
            st.success("Data loaded.")
        else:
            st.info("No data loaded.")

    with col_msgs:
        st.write("")

elif page == "Arcanes":
    st.header("Arcanes")
    df = st.session_state.get("arcanes_df")
    if df is None or df.empty:
        st.info("No Arcanes data available.")
    else:
        cols = df.columns.tolist()
        with st.expander("Table Controls", expanded=True):
            search = st.text_input("Search name or slug", value="")
            rarity_options = ["(all)"] + sorted(
                [r for r in df["rarity"].dropna().unique()]
            )
            rarity = st.selectbox("Rarity", rarity_options, index=0)
            sort_col = st.selectbox("Sort by", ["(none)"] + cols, index=0)
            ascending = st.checkbox("Ascending", value=True)

        df_display = df.copy()
        if search:
            q = search.lower()
            df_display = df_display[
                df_display["name"].str.lower().str.contains(q)
                | df_display["slug"].str.lower().str.contains(q)
            ]
        if rarity != "(all)":
            df_display = df_display[df_display["rarity"] == rarity]

        if sort_col != "(none)":
            df_display = df_display.sort_values(by=sort_col, ascending=ascending)

        st.dataframe(df_display)

        csv = df_display.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV", csv, file_name="arcanes_filtered.csv", mime="text/csv"
        )

elif page == "Mods":
    st.header("Mods")
    df = st.session_state.get("mods_df")
    if df is None or df.empty:
        st.info("No Mods data available.")
    else:
        cols = df.columns.tolist()
        with st.expander("Table Controls", expanded=True):
            search = st.text_input("Search name or slug", value="", key="mods_search")
            rarity_options = ["(all)"] + sorted(
                [r for r in df["rarity"].dropna().unique()]
            )
            rarity = st.selectbox("Rarity", rarity_options, index=0, key="mods_rarity")
            sort_col = st.selectbox(
                "Sort by", ["(none)"] + cols, index=0, key="mods_sort"
            )
            ascending = st.checkbox("Ascending", value=True, key="mods_asc")

        df_display = df.copy()
        if search:
            q = search.lower()
            df_display = df_display[
                df_display["name"].str.lower().str.contains(q)
                | df_display["slug"].str.lower().str.contains(q)
            ]
        if rarity != "(all)":
            df_display = df_display[df_display["rarity"] == rarity]

        if sort_col != "(none)":
            df_display = df_display.sort_values(by=sort_col, ascending=ascending)

        st.dataframe(df_display)

        csv = df_display.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV", csv, file_name="mods_filtered.csv", mime="text/csv"
        )
