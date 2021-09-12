import streamlit as st

def home_feature():
    """Home page of the web app."""

    page_text = """Welcome to the agricultural disaster risk app. If you are using this app on mobile, we recommend using it on **desktop** for a better user experience.

Use the buttons in the sidebar on the left to navigate the app. If this is your first time, we recommend reading the "Help: Variable Selection" page first.

After that, you can use the 3 main features:

- Map of Butuan City
    - A map of Butuan city's barangays is shown. Select an agricultural variable to create a choropleth map where the barangays are colored based on value.
- Barangay Data Summaries
    - Select a barangay to see a summary of its agricultural disaster risk. This includes key risk categories and scores for specific elements and hazards.
- Graphing Tool
    - Select a chart type, agricultural variables, and other options to make an interactive chart with tooltips.

---

# The Team

"Datos Puti" is a group of senior high school students from a school in Quezon City. This app was created by the team as a submission to the Project Sparta hackathon.

Team leader: Migs Germar

- Handled the overall planning of the project.
- Handled all programming tasks from automated data cleaning to web app development.

Team Members: Lorenzo Layug, Fiona Jao, Uriel Dolorfino

- Contributed to manual data cleaning and final paper writing."""

    st.markdown(page_text)