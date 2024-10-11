from flask import Flask, render_template, request, redirect, url_for, session
import os
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import seaborn as sns

app = Flask(__name__)

# Папка для загрузки файлов
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Убедимся, что папка для загрузок существует
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Начальные параметры модели
parameters = {
    'cost_AT': 300000,
    'rental_share': 80,
    'sales_share': 20,
    'monthly_rent': 9491,
    'annual_rent': 113893,
    'indexation_russia_2024': 5,
    'indexation_russia_2025': 5,
    'indexation_foreign_2024': 0,
    'indexation_foreign_2025': 2,
}

# Загружаем данные из файлов, если они существуют
baza_at_path = os.path.join(UPLOAD_FOLDER, 'baza_at.xlsx')
tariffs_and_ottok_path = os.path.join(UPLOAD_FOLDER, 'tariffs_and_ottok.xlsx')
sales_data_path = os.path.join(UPLOAD_FOLDER, 'sales.xlsx')

if os.path.exists(sales_data_path):
    sales_data = pd.read_excel(sales_data_path)
else:
    sales_data = pd.DataFrame()  # Пустой DataFrame, если файл не загружен

if os.path.exists(baza_at_path) and os.path.exists(tariffs_and_ottok_path):
    baza_at = pd.read_excel(baza_at_path)
    tariffs_and_ottok = pd.read_excel(tariffs_and_ottok_path)
else:
    baza_at = pd.DataFrame()  # Пустой DataFrame, если файла нет
    tariffs_and_ottok = pd.DataFrame()
    
def calculate_revenue(params):
    yearly_revenue = {}
    cumulative_terminals = pd.Series(0, index=sales_data.columns[1:])  # Инициализация накопительного итога

    if baza_at.empty or sales_data.empty:
        print("Ошибка: Один или оба файла данных отсутствуют.")
        return yearly_revenue

    # Итерация по каждому году с 2026 по 2040
    for year in range(2026, 2041):
        year_column = f'year_{year}'
        sales_revenue, rental_revenue, connection_revenue = 0, 0, 0
        
        # Получаем данные о продажах за текущий год
        if year_column in sales_data.columns:
            total_sales_for_year = sales_data[year_column].sum()
        else:
            total_sales_for_year = 0

        # Выручка от продаж
        sales_revenue = total_sales_for_year * params['cost_AT']
        
        # Обновляем накопительный итог для базы АТ, добавляя продажи текущего года
        cumulative_terminals[year_column] = cumulative_terminals.get(year_column, 0) + total_sales_for_year

        # Выручка от аренды
        terminals_for_rent = cumulative_terminals[year_column] * (params['rental_share'] / 100)
        rental_revenue = terminals_for_rent * params['monthly_rent'] * 12

        # Выручка от услуг связи
        for index, row in tariffs_and_ottok.iterrows():
            segment, subsegment = row['segment'], row['subsegment']
            churn_rate, personalized_rate = row['ottok'], row['tariff']
            indexed_rate = personalized_rate * (1 + params['indexation_russia_2024'] / 100)

            matching_rows = baza_at[(baza_at['segment'] == segment) & (baza_at['subsegment'] == subsegment)]
            if not matching_rows.empty:
                num_terminals = matching_rows.iloc[0][year_column] if year_column in matching_rows.columns else 0
                segment_revenue = num_terminals * indexed_rate * (1 - churn_rate)
                connection_revenue += segment_revenue

        # Итоговая выручка за год
        yearly_revenue[year] = {
            'sales_revenue': sales_revenue,
            'rental_revenue': rental_revenue,
            'connection_revenue': connection_revenue,
            'total_revenue': sales_revenue + rental_revenue + connection_revenue
        }

    return yearly_revenue

def calculate_segmented_revenue(params):
    segmented_revenue = {}
    cumulative_terminals = pd.Series(0, index=sales_data.columns[1:])  # Инициализация накопительного итога

    if baza_at.empty or sales_data.empty or tariffs_and_ottok.empty:
        print("Ошибка: Один или оба файла данных отсутствуют.")
        return segmented_revenue

    for year in range(2026, 2041):
        year_column = f'year_{year}'
        segmented_revenue[year] = {}

        # Получаем данные о продажах за текущий год
        if year_column in sales_data.columns:
            total_sales_for_year = sales_data[year_column].sum()
        else:
            total_sales_for_year = 0

        # Обновляем накопительный итог для базы АТ
        cumulative_terminals[year_column] = cumulative_terminals.get(year_column, 0) + total_sales_for_year

        for index, row in tariffs_and_ottok.iterrows():
            segment, subsegment = row['segment'], row['subsegment']
            churn_rate, personalized_rate = row['ottok'], row['tariff']
            indexed_rate = personalized_rate * (1 + params['indexation_russia_2024'] / 100)

            matching_rows = baza_at[(baza_at['segment'] == segment) & (baza_at['subsegment'] == subsegment)]
            if not matching_rows.empty and year_column in matching_rows.columns:
                num_terminals = matching_rows.iloc[0][year_column]
                terminals_for_sale = num_terminals * (params['sales_share'] / 100)
                terminals_for_rent = num_terminals * (params['rental_share'] / 100)
                
                sales_revenue = terminals_for_sale * params['cost_AT']
                rental_revenue = terminals_for_rent * params['monthly_rent'] * 12
                connection_revenue = num_terminals * indexed_rate * (1 - churn_rate)
                
                segmented_revenue[year][f"{segment} - {subsegment}"] = {
                    'sales_revenue': sales_revenue,
                    'rental_revenue': rental_revenue,
                    'connection_revenue': connection_revenue,
                    'total_revenue': sales_revenue + rental_revenue + connection_revenue
                }

    return segmented_revenue

# Функции для построения графиков с использованием Seaborn
def generate_line_chart(total_revenue_by_segment, years):
    fig, ax = plt.subplots()
    for segment, data in total_revenue_by_segment.items():
        sns.lineplot(x=years, y=[data.get(year, 0) for year in years], label=segment, ax=ax)
    ax.set_title('Линейный график выручки по сегментам')
    ax.set_xlabel('Год')
    ax.set_ylabel('Выручка (млн руб.)')
    plt.xticks(years, rotation=45)
    return fig

def generate_bar_chart(total_revenue_by_segment, years):
    fig, ax = plt.subplots()
    labels = list(total_revenue_by_segment.keys())
    sales = [sum([total_revenue_by_segment[seg]['sales_revenue'] for seg in labels])]
    rentals = [sum([total_revenue_by_segment[seg]['rental_revenue'] for seg in labels])]
    sns.barplot(x=labels, y=sales, color="blue", label="Продажи", ax=ax)
    sns.barplot(x=labels, y=rentals, color="orange", label="Аренда", bottom=sales, ax=ax)
    ax.set_title('Столбчатая диаграмма выручки')
    ax.set_ylabel('Выручка (млн руб.)')
    plt.xticks(rotation=45)
    ax.legend()
    return fig

def generate_histogram(total_revenue_by_segment):
    fig, ax = plt.subplots()
    revenues = [data['total_revenue'] for data in total_revenue_by_segment.values()]
    sns.histplot(revenues, bins=10, kde=True, ax=ax)
    ax.set_title('Гистограмма выручки')
    ax.set_xlabel('Выручка (млн руб.)')
    ax.set_ylabel('Количество сегментов')
    return fig

def generate_pie_chart(total_revenue_by_segment):
    fig, ax = plt.subplots()
    labels = list(total_revenue_by_segment.keys())
    sizes = [data['total_revenue'] for data in total_revenue_by_segment.values()]
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=sns.color_palette("pastel"))
    ax.set_title('Круговая диаграмма распределения выручки')
    return fig

def generate_waterfall_chart(total_revenue_by_segment, years):
    fig, ax = plt.subplots()
    cumulative_revenue = [sum([total_revenue_by_segment[seg]['total_revenue'] for seg in total_revenue_by_segment])]
    sns.barplot(x=list(range(len(years))), y=cumulative_revenue, ax=ax)
    ax.set_title('Каскадный график выручки')
    ax.set_xlabel('Год')
    ax.set_ylabel('Накопленная выручка (млн руб.)')
    return fig

@app.route('/', methods=['GET', 'POST'])
def index():
    global parameters
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    print("Список файлов в папке:", files)  # Отладочный вывод

    if request.method == 'POST':
        # Обновляем параметры из формы
        parameters['cost_AT'] = float(request.form.get('cost_AT', parameters['cost_AT']))
        parameters['rental_share'] = float(request.form.get('rental_share', parameters['rental_share']))
        parameters['sales_share'] = float(request.form.get('sales_share', parameters['sales_share']))
        parameters['monthly_rent'] = float(request.form.get('monthly_rent', parameters['monthly_rent']))
        parameters['annual_rent'] = float(request.form.get('annual_rent', parameters['annual_rent']))
        parameters['indexation_russia_2024'] = float(request.form.get('indexation_russia_2024', parameters['indexation_russia_2024']))
        parameters['indexation_russia_2025'] = float(request.form.get('indexation_russia_2025', parameters['indexation_russia_2025']))
        parameters['indexation_foreign_2024'] = float(request.form.get('indexation_foreign_2024', parameters['indexation_foreign_2024']))
        parameters['indexation_foreign_2025'] = float(request.form.get('indexation_foreign_2025', parameters['indexation_foreign_2025']))

    return render_template('index.html', parameters=parameters, files=files)

@app.route('/calculate', methods=['GET'])
def calculate():
    # Calculate revenue for each year from 2026 to 2040
    yearly_revenue = calculate_revenue(parameters)
    
    # Plot revenue distribution for each year
    years = list(yearly_revenue.keys())
    total_revenues = [yearly_revenue[year]['total_revenue'] for year in years]
    
    fig, ax = plt.subplots()
    ax.plot(years, total_revenues, marker='o')
    ax.set_title('Годовая выручка по каждому году')
    ax.set_xlabel('Год')
    ax.set_ylabel('Общая выручка')
    img = io.BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode()
    
    return render_template('results.html', yearly_revenue=yearly_revenue, graph_url=graph_url)

@app.route('/segment_calculate', methods=['GET'])
def segment_calculate():
    start_year = request.args.get('start_year', default=2026, type=int)
    end_year = request.args.get('end_year', default=2040, type=int)
    chart_types = request.args.getlist('chart_types')  # Получаем список выбранных графиков

    segmented_revenue = calculate_segmented_revenue(parameters)
    years = range(start_year, end_year + 1)

    # Итог по каждому сегменту для выбранного диапазона лет
    total_revenue_by_segment = {}
    for year in years:
        for segment, revenue in segmented_revenue[year].items():
            if segment not in total_revenue_by_segment:
                total_revenue_by_segment[segment] = {
                    'sales_revenue': 0,
                    'rental_revenue': 0,
                    'connection_revenue': 0,
                    'total_revenue': 0
                }
            total_revenue_by_segment[segment]['sales_revenue'] += revenue['sales_revenue']
            total_revenue_by_segment[segment]['rental_revenue'] += revenue['rental_revenue']
            total_revenue_by_segment[segment]['connection_revenue'] += revenue['connection_revenue']
            total_revenue_by_segment[segment]['total_revenue'] += revenue['total_revenue']

    # Генерация графиков
    chart_urls = []
    for chart_type in chart_types:
        fig = None
        if chart_type == 'line':
            fig = generate_line_chart(total_revenue_by_segment, years)
        elif chart_type == 'bar':
            fig = generate_bar_chart(total_revenue_by_segment, years)
        elif chart_type == 'histogram':
            fig = generate_histogram(total_revenue_by_segment)
        elif chart_type == 'pie':
            fig = generate_pie_chart(total_revenue_by_segment)
        elif chart_type == 'waterfall':
            fig = generate_waterfall_chart(total_revenue_by_segment, years)

        if fig:
            img = io.BytesIO()
            fig.savefig(img, format='png')
            img.seek(0)
            chart_urls.append(base64.b64encode(img.getvalue()).decode())
            plt.close(fig)  # Закрываем фигуру после сохранения, чтобы не переполнять память

    return render_template('segment_results.html', segmented_revenue=segmented_revenue,
                           start_year=start_year, end_year=end_year,
                           chart_urls=chart_urls,
                           total_revenue_by_segment=total_revenue_by_segment)




@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            # Сохраняем файл в папку uploads
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            return redirect(url_for('index'))
    
    return render_template('upload.html')

@app.route('/view_file/<filename>')
def view_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Проверяем, существует ли файл перед его открытием
    if os.path.exists(file_path):
        try:
            # Чтение данных из Excel-файла
            df = pd.read_excel(file_path)
            # Преобразование данных в HTML-таблицу для отображения
            data_html = df.to_html(classes='table table-striped', index=False)
            return render_template('view_file.html', table=data_html, filename=filename)
        except Exception as e:
            return f"Ошибка при чтении файла: {e}", 500
    else:
        return "Файл не найден", 404


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
