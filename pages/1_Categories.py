import streamlit as st
import pandas as pd
from Dashboard import db_operations, get_database_tables


@st.experimental_dialog("Add new Category")
@st.experimental_fragment()
def new_category_dialog():
    with st.container():
        category_name = st.text_input("Category Name")
        category_logo = st.text_input("Logo")
        submit_enabled = category_name
        if st.button("Submit", disabled=not submit_enabled):
            new_category = pd.DataFrame(
                {"category_name": [category_name], "category_logo": [category_logo]}
            )
            db_operations.table_insert(table_name="categories", df=new_category)
            del st.session_state["categories_df"]
            get_database_tables(["categories"])
            st.rerun()


st.title("Categories")

block1 = st.columns([6, 2])
if block1[1].button("Add new Category"):
    new_category_dialog()

st.data_editor(
    st.session_state["categories_df"],
    hide_index=True,
    num_rows="dynamic",
    column_order=("category_logo", "category_name"),
)
