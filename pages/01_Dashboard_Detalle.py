# --- FILTRO SOLO PARA PDC ---
if selected_plan == "PDC":
    # Normalizar el nombre de columna en caso haya espacios o mayúsculas
    df_pdc.columns = df_pdc.columns.str.strip().str.lower()
    
    if 'nivel_gobierno' in df_pdc.columns:
        niveles = df_pdc['nivel_gobierno'].dropna().unique().tolist()
        niveles.sort()

        seleccion_nivel = st.sidebar.multiselect(
            "Nivel de Gobierno",
            options=niveles,
            default=niveles
        )

        df_filtrado = df_pdc[df_pdc['nivel_gobierno'].isin(seleccion_nivel)]
    else:
        st.sidebar.error("⚠️ La columna 'nivel_gobierno' no fue encontrada.")
        df_filtrado = df_pdc.copy()
else:
    df_filtrado = df_pdc.copy()
