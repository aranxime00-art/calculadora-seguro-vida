
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Calculadora de Seguro de Vida", layout="centered")

st.title("Calculadora de Seguro de Vida")
st.write("Cálculo de prima, reserva matemática y gráfica de reservas.")

# -----------------------------
# Tabla de mortalidad sencilla
# -----------------------------
def crear_tabla_mortalidad():
    edades = list(range(18, 101))
    qx = []

    for edad in edades:
        if edad < 30:
            qx.append(0.001)
        elif edad < 40:
            qx.append(0.002)
        elif edad < 50:
            qx.append(0.004)
        elif edad < 60:
            qx.append(0.008)
        elif edad < 70:
            qx.append(0.015)
        elif edad < 80:
            qx.append(0.035)
        elif edad < 90:
            qx.append(0.080)
        else:
            qx.append(0.150)

    return pd.DataFrame({
        "Edad": edades,
        "qx": qx
    })


tabla_mortalidad = crear_tabla_mortalidad()

# -----------------------------
# Entradas
# -----------------------------
st.sidebar.header("Datos del seguro")

edad = st.sidebar.number_input(
    "Edad del asegurado",
    min_value=18,
    max_value=80,
    value=30
)

suma_asegurada = st.sidebar.number_input(
    "Suma asegurada",
    min_value=10000,
    max_value=10000000,
    value=1000000,
    step=10000
)

plazo = st.sidebar.number_input(
    "Plazo del seguro en años",
    min_value=1,
    max_value=40,
    value=20
)

tasa = st.sidebar.number_input(
    "Tasa de interés anual",
    min_value=0.0,
    max_value=1.0,
    value=0.05,
    step=0.01
)

gastos_admin = st.sidebar.number_input(
    "Gastos de administración",
    min_value=0.0,
    max_value=1.0,
    value=0.08,
    step=0.01
)

gastos_adquisicion = st.sidebar.number_input(
    "Gastos de adquisición",
    min_value=0.0,
    max_value=1.0,
    value=0.10,
    step=0.01
)

utilidad = st.sidebar.number_input(
    "Utilidad",
    min_value=0.0,
    max_value=1.0,
    value=0.15,
    step=0.01
)

# -----------------------------
# Función de prima pura de riesgo
# -----------------------------
def calcular_prima_riesgo(edad, plazo, suma_asegurada, tasa, tabla):
    valor_actual_beneficios = 0
    valor_actual_primas = 0

    for t in range(plazo):
        edad_actual = edad + t

        if edad_actual not in tabla["Edad"].values:
            break

        qx = tabla.loc[tabla["Edad"] == edad_actual, "qx"].values[0]
        v = 1 / ((1 + tasa) ** (t + 1))

        valor_actual_beneficios += suma_asegurada * qx * v
        valor_actual_primas += v

    if valor_actual_primas == 0:
        return 0

    prima_riesgo = valor_actual_beneficios / valor_actual_primas
    return prima_riesgo


# -----------------------------
# Función de reserva matemática
# -----------------------------
def calcular_reservas(edad, plazo, suma_asegurada, prima_riesgo, tasa, tabla):
    reservas = []

    for t in range(plazo + 1):
        valor_actual_beneficios = 0
        valor_actual_primas_futuras = 0

        for k in range(t, plazo):
            edad_actual = edad + k

            if edad_actual not in tabla["Edad"].values:
                break

            qx = tabla.loc[tabla["Edad"] == edad_actual, "qx"].values[0]
            v = 1 / ((1 + tasa) ** (k - t + 1))

            valor_actual_beneficios += suma_asegurada * qx * v
            valor_actual_primas_futuras += prima_riesgo * v

        reserva = valor_actual_beneficios - valor_actual_primas_futuras

        if reserva < 0:
            reserva = 0

        reservas.append(reserva)

    return reservas


# -----------------------------
# Cálculos
# -----------------------------
prima_riesgo = calcular_prima_riesgo(
    edad,
    plazo,
    suma_asegurada,
    tasa,
    tabla_mortalidad
)

prima_total_anual = prima_riesgo * (1 + gastos_admin + gastos_adquisicion + utilidad)
prima_mensual = prima_total_anual / 12

reservas = calcular_reservas(
    edad,
    plazo,
    suma_asegurada,
    prima_riesgo,
    tasa,
    tabla_mortalidad
)

df_reservas = pd.DataFrame({
    "Año": list(range(plazo + 1)),
    "Edad": [edad + i for i in range(plazo + 1)],
    "Reserva matemática": reservas
})

# -----------------------------
# Resultados
# -----------------------------
st.subheader("Resultados")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Prima de riesgo anual", f"${prima_riesgo:,.2f}")

with col2:
    st.metric("Prima total anual", f"${prima_total_anual:,.2f}")

with col3:
    st.metric("Prima mensual", f"${prima_mensual:,.2f}")

# -----------------------------
# Tabla de reservas
# -----------------------------
st.subheader("Tabla de reservas")

st.dataframe(df_reservas, use_container_width=True)

# -----------------------------
# Gráfico de reserva
# -----------------------------
st.subheader("Gráfico de reserva matemática")

fig, ax = plt.subplots()

ax.plot(
    df_reservas["Año"],
    df_reservas["Reserva matemática"],
    marker="o"
)

ax.set_xlabel("Año")
ax.set_ylabel("Reserva matemática")
ax.set_title("Evolución de la reserva matemática")
ax.grid(True)

st.pyplot(fig)

# -----------------------------
# Tabla de mortalidad
# -----------------------------
with st.expander("Ver tabla de mortalidad usada"):
    st.dataframe(tabla_mortalidad, use_container_width=True)

    