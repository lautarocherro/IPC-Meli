import json
from datetime import datetime, timedelta


weekday_mapping = {
    "Sunday": f"Domingo",
    "Monday": "Lunes",
    "Tuesday": "Martes",
    "Wednesday": "Miércoles",
    "Thursday": "Jueves",
    "Friday": "Viernes",
    "Saturday": f"Sábado"
}

month_mapping = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre"
}


def get_today_str() -> str:
    current_date = get_now_arg()
    weekday = current_date.strftime("%A")
    day = current_date.day
    month = current_date.month
    year = current_date.year
    return f"{weekday_mapping.get(weekday, '')} {day} de {month_mapping.get(month, '')} de {year}"


def get_ytd_inflation(month_inflation: float) -> float:
    current_date = get_now_arg()
    current_month = current_date.month

    # Read ytd inflation file
    with open("datasets/ytd-inflation.json") as file:
        ytd_inflation_json = json.load(file)

    # Modify file with new monthly inflation and save
    ytd_inflation_json[current_date.strftime("%Y-%m")] = month_inflation
    with open("datasets/ytd-inflation.json", "w") as file:
        json.dump(ytd_inflation_json, file)

    year_months_list = [(current_date - timedelta(days=30 * i)).strftime("%Y-%m") for i in range(current_month)][::-1]

    ytd_inflation = 1
    for year_month in year_months_list:
        month_inflation = 1 + ytd_inflation_json[year_month] / 100
        ytd_inflation *= month_inflation

    ytd_inflation -= 1
    ytd_inflation *= 100

    return round(ytd_inflation, 2)


def get_now_arg():
    # Get the current UTC time
    utc_now = datetime.utcnow()

    # Define a timedelta for UTC - 3 hours
    utc_minus_3_delta = timedelta(hours=-3)

    # Calculate the UTC - 3 time by subtracting the timedelta
    utc_minus_3_time = utc_now + utc_minus_3_delta

    return utc_minus_3_time
