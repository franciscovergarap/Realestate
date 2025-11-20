import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# Configuración de la página
st.set_page_config(
    page_title="Evaluador de Rentabilidad Inmobiliaria",
    page_icon="🏢",
    layout="wide"
)

# --- TÍTULO Y INTRODUCCIÓN ---
st.title("🏢 Evaluador de Inversión Inmobiliaria")
st.markdown("""
Esta herramienta te permite evaluar la viabilidad financiera de una propiedad 
calculando el flujo de caja, Cap Rate y ROI proyectado.
""")

st.markdown("---")

# --- BARRA LATERAL: INPUTS ---
st.sidebar.header("1. Datos de la Propiedad")
precio_propiedad = st.sidebar.number_input("Precio de Compra ($)", min_value=0, value=350000000, step=1000000)
plusvalia_anual = st.sidebar.slider("Plusvalía Anual Estimada (%)", 0.0, 10.0, 3.0) / 100

st.sidebar.header("2. Financiamiento")
usa_financiamiento = st.sidebar.checkbox("¿Requiere Crédito Hipotecario?", value=True)

if usa_financiamiento:
    porcentaje_pie = st.sidebar.slider("Porcentaje de Pie (%)", 0, 100, 20)
    tasa_interes_anual = st.sidebar.number_input("Tasa de Interés Anual (%)", min_value=0.0, value=4.5, step=0.1)
    plazo_anos = st.sidebar.slider("Plazo del Crédito (Años)", 5, 30, 20)
else:
    porcentaje_pie = 100
    tasa_interes_anual = 0
    plazo_anos = 0

st.sidebar.header("3. Ingresos y Gastos Operativos")
alquiler_mensual = st.sidebar.number_input("Alquiler Mensual Estimado ($)", min_value=0, value=1800000, step=50000)
vacancia_anual = st.sidebar.slider("Tasa de Vacancia (%)", 0, 20, 5) / 100
gastos_comunes = st.sidebar.number_input("Gastos Comunes / Mantención Mensual ($)", min_value=0, value=150000)
contribuciones = st.sidebar.number_input("Contribuciones/Impuestos (Mensualizado) ($)", min_value=0, value=80000)
comision_admin = st.sidebar.slider("Comisión Administración (%)", 0, 20, 7) / 100

# --- CÁLCULOS FINANCIEROS ---

# 1. Estructura de Capital
monto_pie = precio_propiedad * (porcentaje_pie / 100)
monto_prestamo = precio_propiedad - monto_pie

# 2. Cálculo Cuota Hipotecaria (Fórmula de amortización francesa)
cuota_mensual = 0
if usa_financiamiento and monto_prestamo > 0 and tasa_interes_anual > 0:
    r = (tasa_interes_anual / 100) / 12
    n = plazo_anos * 12
    cuota_mensual = monto_prestamo * (r * (1 + r)**n) / ((1 + r)**n - 1)
elif usa_financiamiento and tasa_interes_anual == 0:
    cuota_mensual = monto_prestamo / (plazo_anos * 12)

# 3. Ingresos Operativos Netos (NOI)
ingreso_bruto_anual = alquiler_mensual * 12
perdida_vacancia = ingreso_bruto_anual * vacancia_anual
ingreso_efectivo = ingreso_bruto_anual - perdida_vacancia

# 4. Gastos Operativos
gasto_admin_anual = ingreso_efectivo * comision_admin
gastos_fijos_anual = (gastos_comunes + contribuciones) * 12
total_gastos_operativos = gasto_admin_anual + gastos_fijos_anual

noi_anual = ingreso_efectivo - total_gastos_operativos # Net Operating Income

# 5. Flujo de Caja
servicio_deuda_anual = cuota_mensual * 12
cash_flow_anual = noi_anual - servicio_deuda_anual
cash_flow_mensual = cash_flow_anual / 12

# 6. Indicadores
cap_rate = (noi_anual / precio_propiedad) * 100
cash_on_cash = (cash_flow_anual / monto_pie) * 100 if monto_pie > 0 else 0
grm = precio_propiedad / ingreso_bruto_anual if ingreso_bruto_anual > 0 else 0

# --- VISUALIZACIÓN DE RESULTADOS ---

# Fila 1: KPIs Principales
col1, col2, col3, col4 = st.columns(4)
col1.metric("Flujo de Caja Mensual", f"${cash_flow_mensual:,.0f}", delta_color="normal")
col2.metric("Cap Rate", f"{cap_rate:.2f}%")
col3.metric("Cash on Cash Return", f"{cash_on_cash:.2f}%")
col4.metric("Cuota Hipotecaria", f"${cuota_mensual:,.0f}")

st.markdown("---")

# Fila 2: Gráficos
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("Proyección de Retorno Acumulado (10 Años)")
    # Crear proyección
    years = list(range(1, 11))
    equity_data = []
    cash_data = []
    
    valor_propiedad_proy = precio_propiedad
    acumulado_cash = 0
    
    for y in years:
        valor_propiedad_proy *= (1 + plusvalia_anual)
        acumulado_cash += cash_flow_anual
        # Simple equity calculation (aproximado, sin amortización detallada para el gráfico rápido)
        equity_gain = valor_propiedad_proy - precio_propiedad
        equity_data.append(equity_gain)
        cash_data.append(acumulado_cash)

    df_proyeccion = pd.DataFrame({
        "Año": years,
        "Flujo Caja Acumulado": cash_data,
        "Plusvalía Acumulada": equity_data
    })
    
    fig_line = px.bar(df_proyeccion, x="Año", y=["Flujo Caja Acumulado", "Plusvalía Acumulada"],
                      title="Retorno Total: Flujo de Caja + Plusvalía",
                      labels={"value": "Monto ($)", "variable": "Fuente de Retorno"})
    st.plotly_chart(fig_line, use_container_width=True)

with c2:
    st.subheader("Desglose de Ingresos")
    # Waterfall chart simplificado con bar chart
    data_waterfall = {
        "Concepto": ["Ingreso Bruto", "Vacancia", "Gastos Op.", "Deuda", "Flujo Neto"],
        "Monto": [ingreso_bruto_anual, -perdida_vacancia, -total_gastos_operativos, -servicio_deuda_anual, cash_flow_anual]
    }
    fig_water = go.Figure(go.Waterfall(
        name = "20", orientation = "v",
        measure = ["relative", "relative", "relative", "relative", "total"],
        x = data_waterfall["Concepto"],
        y = data_waterfall["Monto"],
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
    ))
    fig_water.update_layout(title = "Cascada de Flujo Anual", showlegend=False)
    st.plotly_chart(fig_water, use_container_width=True)

# --- TABLA DE RESUMEN ---
with st.expander("Ver Tabla de Detalles Financieros"):
    resumen = {
        "Concepto": ["Precio Compra", "Pie Inicial", "Monto Crédito", "NOI Anual", "Servicio Deuda Anual", "Cash Flow Anual"],
        "Valor": [precio_propiedad, monto_pie, monto_prestamo, noi_anual, servicio_deuda_anual, cash_flow_anual]
    }
    df_resumen = pd.DataFrame(resumen)
    st.dataframe(df_resumen.style.format({"Valor": "${:,.0f}"}), use_container_width=True)

