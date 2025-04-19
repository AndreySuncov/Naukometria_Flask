import tabula
import pandas as pd
import glob

# Укажите путь к вашему PDF-файлу
pdf_path = "Категорирование Перечня.pdf"
# Укажите путь для сохранения CSV
csv_path = "output.csv"

# Извлечение всех таблиц из PDF
tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)

# Сохранение в CSV (если таблиц несколько, будет создано несколько файлов)
for i, table in enumerate(tables):
    table.to_csv(f"output_{i}.csv", index=False)

print("Таблицы успешно сохранены в CSV!")