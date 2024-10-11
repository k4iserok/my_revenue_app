import matplotlib.pyplot as plt
import seaborn as sns
import os

# Создайте папку для миниатюр, если она не существует
os.makedirs("static/thumbnails", exist_ok=True)

# Примерные данные для графиков
data = [10, 20, 30, 40, 50]
years = [2026, 2027, 2028, 2029, 2030]

# 1. Линейный график
plt.figure(figsize=(2, 1.5))
sns.lineplot(x=years, y=data)
plt.title("Линейный график")
plt.axis('off')  # Убираем оси для миниатюр
plt.savefig("static/thumbnails/line_chart.png")
plt.close()

# 2. Столбчатая диаграмма
plt.figure(figsize=(2, 1.5))
sns.barplot(x=years, y=data)
plt.title("Столбчатая диаграмма")
plt.axis('off')
plt.savefig("static/thumbnails/bar_chart.png")
plt.close()

# 3. Гистограмма
plt.figure(figsize=(2, 1.5))
sns.histplot(data, bins=5, kde=True)
plt.title("Гистограмма")
plt.axis('off')
plt.savefig("static/thumbnails/histogram.png")
plt.close()

# 4. Круговая диаграмма
plt.figure(figsize=(2, 1.5))
plt.pie(data, labels=years, autopct='%1.1f%%', colors=sns.color_palette("pastel"))
plt.title("Круговая диаграмма")
plt.axis('off')
plt.savefig("static/thumbnails/pie_chart.png")
plt.close()

# 5. Каскадный график (упрощенная версия)
plt.figure(figsize=(2, 1.5))
sns.barplot(x=years, y=data, color="skyblue")
plt.title("Каскадный график")
plt.axis('off')
plt.savefig("static/thumbnails/waterfall.png")
plt.close()
