import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Calculadora de Seguro de Vida", layout="centered")

st.title("Calculadora de Seguro de Vida")
st.write("Prima neta, prima comercial y reserva matemática prospectiva usando tabla de mortalidad real.")

@st.cache_data
def cargar_tabla_mortalidad():
    tabla = pd.read_excel("Mort.xlsx")

    tabla = tabla.rename(columns={
        "x": "Edad",
        "Q(x)": "qx",
        "L(x)": "lx",
        "D(x)": "dx"
    })

    tabla = tabla[["Edad", "qx", "lx", "dx"]].dropna()
    tabla["Edad"] = tabla["Edad"].astype(int)
    tabla["qx"] = tabla["qx"].astype(float)
    tabla["lx"] = tabla["lx"].astype(float)
    tabla["dx"] = tabla["dx"].astype(float)

    return tabla.sort_values("Edad").reset_index(drop=True)


tabla_mortalidad = cargar_tabla_mortalidad()

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

gastos_admin = st.sidebar.number_input("Gastos de administración", 0.0, 1.0, 0.08, 0.01)
gastos_adquisicion = st.sidebar.number_input("Gastos de adquisición", 0.0, 1.0, 0.10, 0.01)
utilidad = st.sidebar.number_input("Utilidad", 0.0, 1.0, 0.15, 0.01)


def lx(tabla, edad):
    fila = tabla[tabla["Edad"] == edad]
    if fila.empty:
        return None
    return fila["lx"].values[0]


def qx(tabla, edad):
    fila = tabla[tabla["Edad"] == edad]
    if fila.empty:
        return None
    return fila["qx"].values[0]


def seguro_temporal(edad, plazo, tasa, tabla):
    v = 1 / (1 + tasa)
    lx_inicial = lx(tabla, edad)
    valor = 0

    for k in range(plazo):
        lx_k = lx(tabla, edad + k)
        qx_k = qx(tabla, edad + k)

        if lx_k is None or qx_k is None:
            break

        kpx = lx_k / lx_inicial
        valor += (v ** (k + 1)) * kpx * qx_k

    return valor


def anualidad_temporal(edad, plazo, tasa, tabla):
    v = 1 / (1 + tasa)
    lx_inicial = lx(tabla, edad)
    valor = 0

    for k in range(plazo):
        lx_k = lx(tabla, edad + k)

        if lx_k is None:
            break

        kpx = lx_k / lx_inicial
        valor += (v ** k) * kpx

    return valor


def calcular_reservas(edad, plazo, suma_asegurada, prima_neta, tasa, tabla):
    reservas = []

    for t in range(plazo + 1):
        edad_t = edad + t
        plazo_restante = plazo - t

        if plazo_restante == 0:
            reservas.append(0)
            continue

        A = seguro_temporal(edad_t, plazo_restante, tasa, tabla)
        a = anualidad_temporal(edad_t, plazo_restante, tasa, tabla)

        reserva = (suma_asegurada * A) - (prima_neta * a)
        reservas.append(reserva)

    return reservas


A = seguro_temporal(edad, plazo, tasa, tabla_mortalidad)
a = anualidad_temporal(edad, plazo, tasa, tabla_mortalidad)

prima_neta_anual = (suma_asegurada * A) / a

prima_comercial_anual = prima_neta_anual * (
    1 + gastos_admin + gastos_adquisicion + utilidad
)

prima_mensual = prima_comercial_anual / 12

reservas = calcular_reservas(
    edad,
    plazo,
    suma_asegurada,
    prima_neta_anual,
    tasa,
    tabla_mortalidad
)

df_reservas = pd.DataFrame({
    "Año": list(range(plazo + 1)),
    "Edad": [edad + i for i in range(plazo + 1)],
    "Reserva matemática": reservas
})

st.subheader("Resultados")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Prima neta anual", f"${prima_neta_anual:,.2f}")

with col2:
    st.metric("Prima comercial anual", f"${prima_comercial_anual:,.2f}")

with col3:
    st.metric("Prima mensual", f"${prima_mensual:,.2f}")

st.info(
    "La reserva matemática se calcula de forma prospectiva: "
    "valor presente actuarial de beneficios futuros menos valor presente actuarial de primas futuras."
)

st.subheader("Tabla de reservas")
st.dataframe(df_reservas, use_container_width=True)

st.subheader("Gráfica de reserva matemática")

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

with st.expander("Ver tabla de mortalidad usada"):
    st.dataframe(tabla_mortalidad, use_container_width=True)

    
