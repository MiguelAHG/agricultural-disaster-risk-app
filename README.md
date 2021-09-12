# Agricultural Disaster Risk Web App

## Description

This is the repository for a web app deployed on Streamlit Cloud. The app was made as part of a submission to the Project Sparta PH hackathon about Butuan City, Caraga region, Philippines. With this app, the user may:

- Choose from a variety of agricultural disaster risk variables about Butuan City.
- Generate interactive choropleth maps.
- View a summary of disaster risk data on a chosen barangay.
- Generate custom interactive univariate or bivariate charts.

In order to view the app, visit the following link:

https://share.streamlit.io/miguelahg/agricultural-disaster-risk-app/main/app_main.py

## Documentation

For more detailed documentation on the app, visit the following Google Docs file:

[Agricultural Disaster Risk Web App - Datos Puti Team](https://docs.google.com/document/d/1feKAvHEzJG2PmKtZrXvsGHOJL4c-kaTc4b_W_fHP-68/edit?usp=sharing)

This document covers the following topics:

- Background of the Project
- Project Outputs
- Project Procedure
- Local Development Guide
- Recommendations
- Bibliography

## Open Data Sources

This project used open data obtained from the following websites:

- Sparta Portal
  - Open data from the Sparta Portal were cleaned and uploaded to the `cleaning_inputs`, `cleaning_outputs`, and `open_data_maps` folders.
  - We have been instructed that the open data from the Sparta Portal only be "utilized solely for this competition and not for use outside of SPARTA hackathon." Thus, do not download the files in the mentioned folders.
- Global Adminstrative Areas (GADM) Version 3.4
  - Geospatial data on Butuan City were uploaded to `geodata/barangay_topojson.json`.
  - GADM's license states that its data may be used for non-commercial purposes.

Complete references are provided below.

Development Academy of the Philippines. (n.d.). Butuan City Datasets. Sparta Portal. Retrieved September 8, 2021, from https://sparta.dap.edu.ph/opendata/lgu/butuancity/datasets

University of Berkeley, Museum of Vertebrate Zoology and the International Rice Research Institute. (2018, April). Global Adminstrative Areas (GADM) Version 3.4. https://gadm.org

## Credits

This project was created by the Datos Puti Team, a group of senior high school students from a school in Quezon City.

Team leader: Migs Germar

- Handled the overall planning of the project.
- Handled all programming tasks from automated data cleaning to web app development.

Team Members: Lorenzo Layug, Fiona Jao, Uriel Dolorfino

- Contributed to manual data cleaning and final paper writing.

## License

An official license has not yet been chosen for this repository. The repository is only public because this is necessary for the web app to deployed. However, there are limitations on what can be done with its contents. For now, the team would like to request visitors to follow these terms of use:

- You may visit the Streamlit web app and use its features, but not download any data or image displayed in it.
- You may not download, reproduce, distribute, or create derivative works from any part of this repository. As this repository is a submission to the Project Sparta hackathon, this rule is especially true for other participants in the hackathon.
- Personnel involved in the judging process of the Project Sparta hackathon may use the web app, download the contents of the web app, and download the contents of the repository.
