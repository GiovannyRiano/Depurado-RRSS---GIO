import streamlit as st
import pandas as pd
import re
import io

# Configuración de la página
st.set_page_config(
    page_title="Limpieza de Redes Sociales",
    page_icon="🧹",
    layout="wide"
)

st.title("🧹 Aplicación de Limpieza de Datos para Redes Sociales (RRSS)")
st.markdown("""
Esta aplicación permite cargar archivos de datos provenientes de redes sociales (Excel o CSV), 
limpiar el texto (eliminar menciones, URLs, emojis, caracteres especiales, duplicados) 
y exportar los resultados listos para análisis.
""")

st.sidebar.header("⚙️ Configuración de Limpieza")

# Carga de archivo
uploaded_file = st.file_uploader("Cargar archivo de datos (Excel o CSV)", type=["xlsx", "xls", "csv"])

def clean_text(text, options):
    if not isinstance(text, str):
        return ""
    
    # Convertir a minúsculas
    if options.get("lowercase", True):
        text = text.lower()
        
    # Eliminar URLs
    if options.get("remove_urls", True):
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
    # Eliminar menciones (@usuario)
    if options.get("remove_mentions", True):
        text = re.sub(r'@[A-Za-z0-9_]+', '', text)
        
    # Manejar Hashtags (#ejemplo)
    if options.get("remove_hashtags_symbol", True):
        text = re.sub(r'#', '', text)
    elif options.get("remove_entire_hashtags", False):
        text = re.sub(r'#[A-Za-z0-9_]+', '', text)
        
    # Eliminar Emojis / Caracteres no ASCII
    if options.get("remove_emojis", True):
        text = text.encode('ascii', 'ignore').decode('utf-8')
        
    # Eliminar puntuación y caracteres especiales
    if options.get("remove_punct", True):
        text = re.sub(r'[^\w\s]', '', text)
        
    # Eliminar números
    if options.get("remove_numbers", False):
        text = re.sub(r'\d+', '', text)
        
    # Eliminar espacios extra y saltos de línea
    if options.get("clean_whitespace", True):
        text = re.sub(r'\s+', ' ', text).strip()
        
    return text

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        st.success(f"Archivo cargado con éxito: `{uploaded_file.name}` ({df.shape[0]} filas, {df.shape[1]} columnas)")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("1. Selección de Columnas")
            text_column = st.selectbox("Selecciona la columna con el texto/mensaje:", options=df.columns)
            
            st.subheader("2. Opciones de Limpieza")
            opt_lowercase = st.checkbox("Convertir a minúsculas", value=True)
            opt_urls = st.checkbox("Eliminar URLs / Enlaces web", value=True)
            opt_mentions = st.checkbox("Eliminar Menciones (@usuario)", value=True)
            opt_hashtag_sym = st.checkbox("Quitar símbolo '#' de hashtags", value=True)
            opt_emojis = st.checkbox("Eliminar Emojis y símbolos", value=True)
            opt_punct = st.checkbox("Eliminar signos de puntuación", value=True)
            opt_numbers = st.checkbox("Eliminar números", value=False)
            opt_whitespace = st.checkbox("Normalizar espacios en blanco", value=True)
            
            st.subheader("3. Filtrado y Duplicados")
            opt_dedup = st.checkbox("Eliminar filas duplicadas", value=True)
            opt_drop_empty = st.checkbox("Eliminar textos vacíos", value=True)
            min_length = st.number_input("Longitud mínima del texto:", min_value=0, value=3)

        cleaning_options = {
            "lowercase": opt_lowercase,
            "remove_urls": opt_urls,
            "remove_mentions": opt_mentions,
            "remove_hashtags_symbol": opt_hashtag_sym,
            "remove_emojis": opt_emojis,
            "remove_punct": opt_punct,
            "remove_numbers": opt_numbers,
            "clean_whitespace": opt_whitespace
        }

        df_cleaned = df.copy()
        
        with col2:
            st.subheader("Vista Previa y Procesamiento")
            
            if st.button("🚀 Ejecutar Limpieza de Datos", type="primary"):
                with st.spinner("Procesando datos..."):
                    clean_col_name = f"{text_column}_LIMPIO"
                    df_cleaned[clean_col_name] = df_cleaned[text_column].astype(str).apply(lambda x: clean_text(x, cleaning_options))
                    
                    if min_length > 0:
                        df_cleaned = df_cleaned[df_cleaned[clean_col_name].str.len() >= min_length]
                        
                    if opt_drop_empty:
                        df_cleaned = df_cleaned[df_cleaned[clean_col_name].str.strip() != ""]
                        
                    if opt_dedup:
                        df_cleaned = df_cleaned.drop_duplicates(subset=[clean_col_name])
                        
                    st.success(f"¡Procesamiento completado! Filas resultantes: {len(df_cleaned)}")
                    
                    st.markdown("### 📊 Comparativa de Texto")
                    st.dataframe(df_cleaned[[text_column, clean_col_name]].head(20), use_container_width=True)
                    
                    st.markdown("### 📥 Descargar Resultado")
                    output_format = st.radio("Formato de descarga:", ["Excel (.xlsx)", "CSV (.csv)"], horizontal=True)
                    
                    if output_format == "Excel (.xlsx)":
                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            df_cleaned.to_excel(writer, index=False, sheet_name='Limpio')
                        buffer.seek(0)
                        
                        st.download_button(
                            label="📥 Descargar Excel Limpio",
                            data=buffer,
                            file_name="datos_rrss_limpios.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        csv_data = df_cleaned.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Descargar CSV Limpio",
                            data=csv_data,
                            file_name="datos_rrss_limpios.csv",
                            mime="text/csv"
                        )
            else:
                st.info("Haz clic en **Ejecutar Limpieza de Datos** para procesar la información.")
                st.dataframe(df.head(10), use_container_width=True)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("👆 Por favor sube un archivo Excel o CSV para comenzar.")