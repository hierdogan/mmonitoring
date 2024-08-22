import streamlit as st
import pandas as pd
import datetime
from io import BytesIO
pd.options.mode.copy_on_write = True


def load_data(uploaded_file):
    if uploaded_file.name.endswith('.csv'):
        return pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith('.xlsx'):
        return pd.read_excel(uploaded_file)


def data_prep(df):
    # DATA PREP
    # ###### STEP 1 : DATA CLEANING ######
    # leave unnecessary columns.
    columns_to_drop = ["Email", "Company", "% Viewed", "Telefon Numarası"]
    df.drop(columns=columns_to_drop, axis=1, inplace=True)

    # ###### STEP 2 : SET DATA TYPES ######
    # Set the datetimestamp columns.
    timestamp_cols = [col for col in df.columns if df[col].astype(str).str.contains(" UTC", na=False).any()]
    # OutCome: ['Completed At', 'Started At', 'Activated At', 'Expires At', 'Last Sign In']
    for col in timestamp_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce').dt.tz_convert('Europe/Istanbul').dt.tz_localize(None)

    # We convert columns which datatype is object to category.
    list_str_obj_cols = df.columns[df.dtypes == "object"].tolist()
    for str_obj_col in list_str_obj_cols:
        df[str_obj_col] = df[str_obj_col].astype("category")

    # ###### STEP 3 : FEATURE ENGINEERING ######
    # Merge the First Name & Last Name as a new column, drop original.
    df['Full_Name'] = ((df['First Name'].astype(str) + ' ' + df['Last Name'].astype(str)).str.title()).astype(
        "category")
    column_names = list(df.columns)
    column_to_move = 'Full_Name'
    column_names.remove(column_to_move)
    desired_position = 2
    column_names.insert(desired_position, column_to_move)
    df = df[column_names]
    df.drop(columns=["First Name", "Last Name"], axis=1, inplace=True)

    # Adding Tenure & Recency
    df['Tenure'] = (df['Last Sign In'] - df['Activated At']).dt.days
    df['Recency'] = (datetime.datetime.now() - df["Last Sign In"]).dt.days

    # Create Motivation Slices
    df['Motivation_Slices'] = pd.cut(x=df['% Completed'],
                                     bins=[-1, 30, 45, 60, 80, 100],
                                     labels=["Düştü | Düşecek",
                                             "Geriden Geliyor",
                                             "Desteklenmeli",
                                             "Aktif",
                                             "Yıldız"])

    # Define target courses and filter.

    selected_courses = ["SQL for Data Analytics", "Excel for Data Analytics with CRM Metrics"]


    # selected_courses = ["Welcome to Data Analytics Bootcamp Mindset",
    #                     "Data Analysis with Python",
    #                     "Podcasts",
    #                     "Introduction to Data Science and Artificial Intelligence",
    #                     "İş Başvurularında Öne Çıkma Rehberi",
    #                     "Learning for the Future",
    #                     "Data Visualization and Reporting with Power BI",
    #                     "Excel for Data Analytics with CRM Metrics - Ön Hazırlık"]

    filtered_df = df[df['Course Name'].isin(selected_courses)]
    df = filtered_df.copy()
    # df.sort_values("Full_Name")
    return df


def download_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()


st.title("Excel/CSV Veri Manipülasyonu Uygulaması")

uploaded_file = st.file_uploader("Bir Excel veya CSV dosyası yükleyin", type=['csv', 'xlsx'])

if uploaded_file is not None:
    df = load_data(uploaded_file)
    st.write("Yüklenen Veri:")
    st.write(df)

    # Veri Manipülasyonu
    manipulated_df = data_prep(df)
    st.write("Hazırlanmış Veri:")
    st.write(manipulated_df)

    # Dosya İndirme
    st.download_button(
        label="Sonuçları İndir (Excel)",
        data=download_excel(manipulated_df),
        file_name="module_monitoring_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
