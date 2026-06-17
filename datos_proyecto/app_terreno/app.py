import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import os

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Dashboard Ytrio & REE",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Funciones de Carga de Datos ---
@st.cache_data
def load_data(file_path):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return None

# Ruta del archivo (asumiendo que app.py está en el mismo directorio)
DATA_PATH = "BD_Ytrio_LIMPIO.csv"

# --- Estilos CSS Personalizados ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2c3e50;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🌍 Proyecto Exploración Ytrio: Análisis Geoestadístico Interactivo</div>', unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2909/2909414.png", width=100)
st.sidebar.title("Navegación")
section = st.sidebar.radio("Ir a:", [
    "📋 Vista General de Datos",
    "📊 Análisis Exploratorio",
    "🗺️ Análisis Espacial (Mapas)",
    "🤖 Machine Learning (PCA & Clustering)"
])

# Cargar Datos
df = load_data(DATA_PATH)

if df is None:
    st.error(f"No se encontró el archivo de datos: {DATA_PATH}. Por favor, asegúrate de que el archivo existe en el directorio de la aplicación.")
    st.stop()

# --- Filtros Globales (Sidebar) ---
st.sidebar.markdown("---")
st.sidebar.header("⚙️ Filtros Globales")
all_litologies = ["Todas"] + sorted(df["Litology_STD"].dropna().unique().tolist())
selected_litology = st.sidebar.selectbox("Filtrar por Litología:", all_litologies)

if selected_litology != "Todas":
    df_filtered = df[df["Litology_STD"] == selected_litology].copy()
else:
    df_filtered = df.copy()

ree_cols = ["Th_ppm", "La_ppm", "Pr_ppm", "Ce_ppm", "Nd_ppm", "Y_ppm"]
coord_cols = ["ESTE_X", "NORTE_Y", "COTA_M"]

# ==========================================
# 1. VISTA GENERAL DE DATOS
# ==========================================
if section == "📋 Vista General de Datos":
    st.header("📋 Vista General de Datos Limpios")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Muestras", len(df_filtered))
    with col2:
        st.metric("Litologías Únicas", df_filtered["Litology_STD"].nunique())
    with col3:
        st.metric("Promedio Y (ppm)", f"{df_filtered['Y_ppm'].mean():.2f}")
    with col4:
        st.metric("Max Y (ppm)", f"{df_filtered['Y_ppm'].max():.2f}")
        
    st.subheader("Explorador de la Base de Datos")
    st.dataframe(df_filtered.head(100), use_container_width=True)
    
    st.subheader("Estadísticas Descriptivas (Elementos Clave)")
    st.dataframe(df_filtered[ree_cols].describe().T, use_container_width=True)

# ==========================================
# 2. ANÁLISIS EXPLORATORIO
# ==========================================
elif section == "📊 Análisis Exploratorio":
    st.header("📊 Análisis Exploratorio (EDA)")
    
    tab1, tab2, tab3 = st.tabs(["Distribuciones (Boxplots)", "Dispersión (Scatter)", "Correlación"])
    
    with tab1:
        st.subheader("Distribución de Elementos por Litología")
        elemento_box = st.selectbox("Selecciona un elemento para el Boxplot:", ree_cols, index=5) # Default Y_ppm
        
        # Filtrar las top litologías para no saturar el gráfico
        top_litologias = df_filtered["Litology_STD"].value_counts().nlargest(15).index
        df_box = df_filtered[df_filtered["Litology_STD"].isin(top_litologias)]
        
        fig = px.box(df_box, x="Litology_STD", y=elemento_box, color="Litology_STD", 
                     title=f"Boxplot de {elemento_box} en las litologías más frecuentes")
        fig.update_layout(xaxis={'categoryorder':'median descending'}, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
    with tab2:
        st.subheader("Gráficos de Dispersión Bivariante")
        col1, col2 = st.columns(2)
        with col1:
            x_axis = st.selectbox("Eje X:", ree_cols, index=3) # Default Ce
        with col2:
            y_axis = st.selectbox("Eje Y:", ree_cols, index=5) # Default Y
            
        fig2 = px.scatter(df_filtered, x=x_axis, y=y_axis, color="Litology_STD", 
                          hover_data=["Sample"], title=f"{y_axis} vs {x_axis}")
        st.plotly_chart(fig2, use_container_width=True)
        
    with tab3:
        st.subheader("Matriz de Correlación")
        corr = df_filtered[ree_cols].corr()
        fig3 = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale='RdBu_r', zmin=-1, zmax=1)
        st.plotly_chart(fig3, use_container_width=True)

# ==========================================
# 3. ANÁLISIS ESPACIAL
# ==========================================
elif section == "🗺️ Análisis Espacial (Mapas)":
    st.header("🗺️ Análisis Espacial")
    
    df_spatial = df_filtered.dropna(subset=coord_cols).copy()
    
    if len(df_spatial) == 0:
        st.warning("No hay suficientes datos con coordenadas válidas para mostrar mapas.")
    else:
        elemento_mapa = st.selectbox("Selecciona el elemento a visualizar en el mapa:", ree_cols, index=5)
        
        tab1, tab2 = st.tabs(["Mapa 2D (Planta)", "Mapa 3D"])
        
        with tab1:
            fig_2d = px.scatter(df_spatial, x="ESTE_X", y="NORTE_Y", color=elemento_mapa,
                                size=elemento_mapa, hover_data=["Sample", "Litology_STD", "COTA_M"],
                                color_continuous_scale="Viridis", title=f"Distribución en Planta de {elemento_mapa}")
            # Mantener proporción espacial
            fig_2d.update_yaxes(scaleanchor="x", scaleratio=1)
            st.plotly_chart(fig_2d, use_container_width=True)
            
        with tab2:
            fig_3d = px.scatter_3d(df_spatial, x="ESTE_X", y="NORTE_Y", z="COTA_M", color=elemento_mapa,
                                   size=elemento_mapa, hover_data=["Sample", "Litology_STD"],
                                   color_continuous_scale="Turbo", title=f"Distribución 3D de {elemento_mapa}")
            fig_3d.update_traces(marker=dict(size=4, opacity=0.8))
            st.plotly_chart(fig_3d, use_container_width=True, height=700)

# ==========================================
# 4. MACHINE LEARNING
# ==========================================
elif section == "🤖 Machine Learning (PCA & Clustering)":
    st.header("🤖 Machine Learning Multivariante")
    
    st.write("En esta sección aplicaremos Análisis de Componentes Principales (PCA) y K-Means Clustering a los elementos de Tierras Raras.")
    
    # Preparar datos
    df_ml = df_filtered.dropna(subset=ree_cols).copy()
    if len(df_ml) < 10:
        st.warning("No hay suficientes datos para aplicar Machine Learning.")
    else:
        X = df_ml[ree_cols].values
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # PCA
        pca = PCA()
        X_pca = pca.fit_transform(X_scaled)
        
        col_ml1, col_ml2 = st.columns(2)
        
        with col_ml1:
            st.subheader("Varianza Explicada (PCA)")
            var_exp = pca.explained_variance_ratio_ * 100
            cum_var_exp = np.cumsum(var_exp)
            
            fig_var = go.Figure()
            fig_var.add_trace(go.Bar(x=[f"PC{i+1}" for i in range(len(var_exp))], y=var_exp, name="Individual"))
            fig_var.add_trace(go.Scatter(x=[f"PC{i+1}" for i in range(len(var_exp))], y=cum_var_exp, mode='lines+markers', name="Acumulada"))
            fig_var.update_layout(title="Varianza Explicada por Componente Principal", yaxis_title="Varianza (%)")
            st.plotly_chart(fig_var, use_container_width=True)
            
        # Clustering
        with col_ml2:
            st.subheader("K-Means Clustering")
            n_clusters = st.slider("Número de Clusters (K):", min_value=2, max_value=8, value=3)
            
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(X_scaled)
            df_ml["Cluster"] = [f"Cluster {c}" for c in clusters]
            
            # Mostrar PCA Scatter con Clusters
            df_ml["PC1"] = X_pca[:, 0]
            df_ml["PC2"] = X_pca[:, 1]
            
            fig_pca = px.scatter(df_ml, x="PC1", y="PC2", color="Cluster", hover_data=["Sample", "Litology_STD"] + ree_cols,
                                 title="Clusters proyectados en PC1 y PC2")
            st.plotly_chart(fig_pca, use_container_width=True)
            
        st.subheader("Perfil Promedio por Cluster")
        cluster_profile = df_ml.groupby("Cluster")[ree_cols].mean().reset_index()
        fig_radar = go.Figure()
        
        for i, row in cluster_profile.iterrows():
            fig_radar.add_trace(go.Scatterpolar(
                r=row[ree_cols].values,
                theta=ree_cols,
                fill='toself',
                name=row["Cluster"]
            ))
            
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True)),
            showlegend=True,
            title="Diagrama de Araña de Perfiles de Cluster (Valores Promedio Originales)"
        )
        st.plotly_chart(fig_radar, use_container_width=True)
