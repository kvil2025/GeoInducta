import pandas as pd
import numpy as np

# Datos crudos extraídos del informe de terreno de Quinhue con siglas originales
data = [
    # Qui-CA-107
    {
        "Estacion": "Qui-CA-107", "Intervalo": "(0 - 1) m", "Muestra_ID": "1140115",
        "Litologia": "Granito + Qz ± bt", "Horizonte": "LP-US", "Alteracion": "+Caol / -OxFe",
        "Observaciones": "Sup (0-1): LP-US, +Caol / -OxFe. (Gro)", "Sector": "Este"
    },
    {
        "Estacion": "Qui-CA-107", "Intervalo": "(1 - 2) m", "Muestra_ID": "1140116",
        "Litologia": "Granito + Qz ± bt", "Horizonte": "UP", "Alteracion": "-Caol = OxFe",
        "Observaciones": "Inf (1-2): UP, -Caol = OxFe. (Gro)", "Sector": "Este"
    },
    # Qui-CA-108
    {
        "Estacion": "Qui-CA-108", "Intervalo": "(0 - 1) m", "Muestra_ID": "1140117",
        "Litologia": "Granito + Qz ± bt", "Horizonte": "UP/LP", "Alteracion": "+Caol + OxFe",
        "Observaciones": "Muestra 117: UP/LP, +Caol + OxFe. (Gro)", "Sector": "Este"
    },
    {
        "Estacion": "Qui-CA-108", "Intervalo": "(0 - 1) m", "Muestra_ID": "1140118",
        "Litologia": "Granito + Qz ± bt", "Horizonte": "LP", "Alteracion": "± Caol + OxFe",
        "Observaciones": "Muestra 118: LP, ± Caol + OxFe. (Gro)", "Sector": "Este"
    },
    # Qui-CA-109
    {
        "Estacion": "Qui-CA-109", "Intervalo": "(0 - 1) m", "Muestra_ID": "1140119",
        "Litologia": "Granito + Qz ± bt", "Horizonte": "LP/US", "Alteracion": "± Caol + OxFe",
        "Observaciones": "Muestra LP/US, ± Caol + OxFe. (Gro)", "Sector": "Este"
    },
    # Qui-CA-110
    {
        "Estacion": "Qui-CA-110", "Intervalo": "(0 - 1) m", "Muestra_ID": "1140120",
        "Litologia": "Granito + Qz + bt", "Horizonte": "LP/US", "Alteracion": "+Caol ± OxFe",
        "Observaciones": "Nivel (0-1): LP/US, +Caol ± OxFe. (Gro)", "Sector": "Este"
    },
    {
        "Estacion": "Qui-CA-110", "Intervalo": "(1 - 2) m", "Muestra_ID": "1140121",
        "Litologia": "Granito + Qz + bt", "Horizonte": "US/LP", "Alteracion": "+Caol ± OxFe",
        "Observaciones": "Nivel (1-2): US/LP, +Caol ± OxFe. (Gro)", "Sector": "Este"
    },
    # Zona Muestreo 1
    {
        "Estacion": "Zona Muestreo 1", "Intervalo": "-", "Muestra_ID": "GPS",
        "Litologia": "Control de inicio de zona", "Horizonte": "-", "Alteracion": "-",
        "Observaciones": "Punto de referencia georreferenciado en Qui-CA.", "Sector": "Este"
    },
    # Qui-CA-111
    {
        "Estacion": "Qui-CA-111", "Intervalo": "(0 - 1) Norte", "Muestra_ID": "1140122",
        "Litologia": "Granito + Qz - bt", "Horizonte": "LP", "Alteracion": "+Caol - OxFe",
        "Observaciones": "Norte: LP, +Caol - OxFe. (Gro)", "Sector": "Este"
    },
    {
        "Estacion": "Qui-CA-111", "Intervalo": "(0 - 1) Sur", "Muestra_ID": "1140123",
        "Litologia": "Granito + Qz - bt", "Horizonte": "LP", "Alteracion": "± Caol - OxFe",
        "Observaciones": "Sur: LP, ± Caol - OxFe. (Gro)", "Sector": "Este"
    },
    # Zona Muestreo 2
    {
        "Estacion": "Zona Muestreo 2", "Intervalo": "Punto 372", "Muestra_ID": "GPS",
        "Litologia": "Pegmatita (Qz + Msc)", "Horizonte": "-", "Alteracion": "-",
        "Observaciones": "Control estructural y mineralógico singular del sector.", "Sector": "Este"
    },
    # Qui-CA-112
    {
        "Estacion": "Qui-CA-112", "Intervalo": "Pared Este (0-1)", "Muestra_ID": "1140124",
        "Litologia": "Granito con stockwork de Qz + Msc. ± bt en granito", "Horizonte": "LP", "Alteracion": "± Caol ± OxFe",
        "Observaciones": "Pared Este: LP con ± Caol ± OxFe.", "Sector": "Este"
    },
    {
        "Estacion": "Qui-CA-112", "Intervalo": "Pared Este (0-2)", "Muestra_ID": "1140125",
        "Litologia": "Granito con stockwork de Qz + Msc. ± bt en granito", "Horizonte": "LP", "Alteracion": "± Caol ± OxFe",
        "Observaciones": "Pared Este: LP con ± Caol ± OxFe.", "Sector": "Este"
    },
    {
        "Estacion": "Qui-CA-112", "Intervalo": "Pared Oeste (0-1)", "Muestra_ID": "1140126",
        "Litologia": "Pegmatitas (Qz + Msc) (LP)", "Horizonte": "LP", "Alteracion": "± Caol ± OxFe",
        "Observaciones": "Pared Oeste: Cambia lateralmente a Pegmatitas (Qz + Msc) (LP), ± Caol ± OxFe.", "Sector": "Oeste"
    },
    # Qui-CA-113
    {
        "Estacion": "Qui-CA-113", "Intervalo": "(0 - 1) m", "Muestra_ID": "1140127",
        "Litologia": "Granito + Qz + bt + Msc", "Horizonte": "LP", "Alteracion": "-Caol ± OxFe",
        "Observaciones": "Muestra 127: LP, -Caol ± OxFe. (Gro)", "Sector": "Este"
    },
    {
        "Estacion": "Qui-CA-113", "Intervalo": "(1 - 2) m", "Muestra_ID": "1140128",
        "Litologia": "Granito + Qz + bt + Msc", "Horizonte": "UP", "Alteracion": "-Caol ± OxFe",
        "Observaciones": "Muestra 128: UP, -Caol ± OxFe. (Gro)", "Sector": "Este"
    },
    # Qui-CA-114
    {
        "Estacion": "Qui-CA-114", "Intervalo": "(0 - 1) Norte", "Muestra_ID": "1140129",
        "Litologia": "Granito (Qz + bt)", "Horizonte": "UP", "Alteracion": "± Caol ± OxFe",
        "Observaciones": "Norte: UP, ± Caol ± OxFe. (Gro)", "Sector": "Este"
    },
    {
        "Estacion": "Qui-CA-114", "Intervalo": "(0 - 0.3) Sur", "Muestra_ID": "1140130",
        "Litologia": "Granito (Qz + bt)", "Horizonte": "UP", "Alteracion": "-Caol ± OxFe",
        "Observaciones": "Sur: UP, -Caol ± OxFe. (Gro)", "Sector": "Este"
    },
    # Qui-CA-115
    {
        "Estacion": "Qui-CA-115", "Intervalo": "(0 - 1) m", "Muestra_ID": "1140131",
        "Litologia": "Granito + Qz + bt + Msc", "Horizonte": "UP/LP", "Alteracion": "-Caol ± OxFe",
        "Observaciones": "Muestra UP/LP, presenta -Caol ± OxFe. (Gro)", "Sector": "Este"
    },
    # Qui-CA-116
    {
        "Estacion": "Qui-CA-116", "Intervalo": "(0 - 1) m", "Muestra_ID": "1140132",
        "Litologia": "Granito + Qz + bt + Msc", "Horizonte": "US / (LS?)", "Alteracion": "+Caol - OxFe",
        "Observaciones": "Muestra US / (LS?), presenta +Caol - OxFe. (Gro)", "Sector": "Este"
    },
    # Qui-CA-117
    {
        "Estacion": "Qui-CA-117", "Intervalo": "(0 - 1) m", "Muestra_ID": "1140133",
        "Litologia": "Granito + Qz + bt + Msc", "Horizonte": "LP", "Alteracion": "± Caol ± OxFe",
        "Observaciones": "Muestra LP, ± Caol ± OxFe. Zona Superior intruida por pegmatita de Qz + Msc. (Gro)", "Sector": "Este"
    },
    # Qui-CA-118
    {
        "Estacion": "Qui-CA-118", "Intervalo": "(0 - 1) m", "Muestra_ID": "1140134",
        "Litologia": "Granito + Qz + bt", "Horizonte": "LP/US", "Alteracion": "+Caol - OxFe",
        "Observaciones": "Nivel (0-1): LP/US, +Caol - OxFe. (Gro)", "Sector": "Este"
    },
    {
        "Estacion": "Qui-CA-118", "Intervalo": "(1 - 2) m", "Muestra_ID": "1140135",
        "Litologia": "Granito + Qz + bt", "Horizonte": "LP", "Alteracion": "+Caol - OxFe",
        "Observaciones": "Nivel (1-2): LP, +Caol - OxFe. (Gro)", "Sector": "Este"
    },
    # Qui-CA-119
    {
        "Estacion": "Qui-CA-119", "Intervalo": "(0 - 1) m", "Muestra_ID": "1140136",
        "Litologia": "Granito + Qz + bt ± Msc", "Horizonte": "LP/US", "Alteracion": "+Caol ± OxFe",
        "Observaciones": "Nivel (0-1): LP/US, +Caol ± OxFe. (Gro)", "Sector": "Este"
    },
    {
        "Estacion": "Qui-CA-119", "Intervalo": "(1 - 2) m", "Muestra_ID": "1140137",
        "Litologia": "Granito + Qz + bt ± Msc", "Horizonte": "LP", "Alteracion": "+Caol ± OxFe",
        "Observaciones": "Nivel (1-2): LP, +Caol ± OxFe. (Gro)", "Sector": "Este"
    },
    # Qui-CA-120
    {
        "Estacion": "Qui-CA-120", "Intervalo": "(0 - 1) m", "Muestra_ID": "1140138",
        "Litologia": "Granito + Qz - bt", "Horizonte": "LP", "Alteracion": "-Caol ± OxFe",
        "Observaciones": "Muestra LP, manifiesta -Caol ± OxFe. (Gro)", "Sector": "Este"
    },
    # Qui-CA-121
    {
        "Estacion": "Qui-CA-121", "Intervalo": "(0 - 1) m", "Muestra_ID": "1140139",
        "Litologia": "Granito (Qz + bt)", "Horizonte": "LP", "Alteracion": "+Caol - OxFe",
        "Observaciones": "Nivel (0-1): LP, +Caol - OxFe. (Gro)", "Sector": "Este"
    },
    {
        "Estacion": "Qui-CA-121", "Intervalo": "(1 - 2) m", "Muestra_ID": "1140140",
        "Litologia": "Granito (Qz + bt)", "Horizonte": "LP", "Alteracion": "+Caol ± OxFe",
        "Observaciones": "Nivel (1-2): LP, +Caol ± OxFe. (Gro)", "Sector": "Este"
    },
    {
        "Estacion": "Qui-CA-121", "Intervalo": "(2 - 3) m", "Muestra_ID": "1140141",
        "Litologia": "Granito (Qz + bt)", "Horizonte": "LP", "Alteracion": "± Caol + OxFe",
        "Observaciones": "Nivel (2-3): LP, ± Caol + OxFe. (Gro)", "Sector": "Este"
    },
    # Qui-CA-122
    {
        "Estacion": "Qui-CA-122", "Intervalo": "(0 - 1) m", "Muestra_ID": "1140142",
        "Litologia": "Granito (Qz + bt)", "Horizonte": "UP/LP", "Alteracion": "+Caol ± OxFe",
        "Observaciones": "Muestra UP/LP, marcada con +Caol ± OxFe.", "Sector": "Oeste"
    },
    # Qui-CA-123
    {
        "Estacion": "Qui-CA-123", "Intervalo": "(0 - 1) m", "Muestra_ID": "1140143",
        "Litologia": "Granito (Qz + bt)", "Horizonte": "UP/LP", "Alteracion": "± Caol + OxFe",
        "Observaciones": "Muestra UP/LP, marcada con ± Caol + OxFe. (Gro)", "Sector": "Oeste"
    },
    # Qui-CA-124
    {
        "Estacion": "Qui-CA-124", "Intervalo": "(0 - 1) m", "Muestra_ID": "1140144",
        "Litologia": "Granito (Qz - bt)", "Horizonte": "UP/LP", "Alteracion": "± OxFe - Caol",
        "Observaciones": "Muestra UP/LP, ± OxFe - Caol. (Gro)", "Sector": "Oeste"
    },
    # Qui-CA-125
    {
        "Estacion": "Qui-CA-125", "Intervalo": "(0 - 1) m", "Muestra_ID": "1140145",
        "Litologia": "Granito + Qz + bt - Msc", "Horizonte": "LP/US", "Alteracion": "+OxFe - Caol",
        "Observaciones": "Muestra LP/US, +OxFe - Caol. (Gro)", "Sector": "Oeste"
    },
    # Qui-CA-126
    {
        "Estacion": "Qui-CA-126", "Intervalo": "(0 - 1) m", "Muestra_ID": "1140146 (Duplicado)",
        "Litologia": "Granito + Qz - bt", "Horizonte": "UP/LP", "Alteracion": "+Caol ± OxFe",
        "Observaciones": "Sub-muestra 1: UP/LP, +Caol ± OxFe. Duplicado.", "Sector": "Oeste"
    },
    {
        "Estacion": "Qui-CA-126", "Intervalo": "(0 - 1) m", "Muestra_ID": "1140147 (Alt)",
        "Litologia": "Granito + Qz - bt", "Horizonte": "UP", "Alteracion": "++OxFe - Caol",
        "Observaciones": "Sub-muestra 2: UP, ++OxFe - Caol. Ver nota estructural.", "Sector": "Oeste"
    },
    # Qui-CA-127
    {
        "Estacion": "Qui-CA-127", "Intervalo": "(0 - 1) m", "Muestra_ID": "1140148",
        "Litologia": "Granito + Qz - bt", "Horizonte": "UP", "Alteracion": "++OxFe - Caol",
        "Observaciones": "Muestra UP, ++OxFe - Caol. (Gro)", "Sector": "Oeste"
    },
    # Qui-CA-128
    {
        "Estacion": "Qui-CA-128", "Intervalo": "(0 - 0.5) m", "Muestra_ID": "1140149",
        "Litologia": "Granito + Qz - bt", "Horizonte": "LP", "Alteracion": "± Caol + OxFe",
        "Observaciones": "Muestra LP, ± Caol + OxFe. (Gro)", "Sector": "Oeste"
    },
    # Qui-CA-129
    {
        "Estacion": "Qui-CA-129", "Intervalo": "(0 - 0.5) m", "Muestra_ID": "1140150",
        "Litologia": "Granito + Qz - bt", "Horizonte": "UP", "Alteracion": "-Caol = OxFe",
        "Observaciones": "Muestra UP, -Caol = OxFe. (Gro)", "Sector": "Oeste"
    }
]

df_quinhue = pd.DataFrame(data)
df_quinhue.to_csv("Quinhue_datos_campo_limpios.csv", index=False, encoding='utf-8')
df_quinhue.to_excel("Quinhue_datos_campo_limpios.xlsx", index=False)
print("¡Archivos CSV y Excel generados con siglas con éxito!")
