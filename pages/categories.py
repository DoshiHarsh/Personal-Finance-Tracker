import streamlit as st
from core_components.functions import db_operations, category_dialog, display_card_ui

# Due to unknown limitation, setting values to st.session_state with function defined in another script doesn't always execute.
for table in ["categories", "detailed_transactions"]:
    if f"{table}_df" not in st.session_state:
        st.session_state[f"{table}_df"] = db_operations.table_query(
            f"Select * from {table}"
        )

block1 = st.columns([6, 2], vertical_alignment="bottom")
block1[0].title("Categories")
block1[1].button("New Category", on_click=category_dialog, use_container_width=True)
display_card_ui(
    st.session_state["categories_df"].sort_values("category_name"),
    type="categories",
    default_page_size=25,
)
