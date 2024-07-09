import streamlit as st
import pandas as pd
from Dashboard import db_operations


# Function to create the dialog box for new category
@st.experimental_dialog("Add new Category")
def new_category_dialog():
    """
    Create dialog box UI to add new category.
    """
    with st.container():
        category_logo = st.text_input("Logo")
        category_name = st.text_input("Category Name")
        submit_enabled = category_name
        if st.button("Submit", disabled=not submit_enabled):
            new_category = pd.DataFrame(
                {"category_logo": [category_logo], "category_name": [category_name]}
            )
            db_operations.table_insert(table_name="categories", df=new_category)
            del st.session_state["categories_df"]
            st.rerun()


# Due to unknown limitation, setting values to st.session_state with function defined in another script doesn't always execute.
for table in ["categories"]:
    if f"{table}_df" not in st.session_state:
        st.session_state[f"{table}_df"] = db_operations.table_query(
            f"Select * from {table}"
        )

st.title("Categories")

block1 = st.columns([6, 2])
if block1[1].button("Add new Category"):
    new_category_dialog()

# Display the categories dataframe. (to be replaced with Card UI)
st.dataframe(st.session_state["categories_df"], hide_index=True)
