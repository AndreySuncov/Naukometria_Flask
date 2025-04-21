import requests
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Запрос к API
response = requests.get("http://46.8.232.101:5001/api/statistics/keywords?year=2020")
data = response.json()

# Преобразуем в формат: {слово: количество}
word_freq = {entry["keyword"]: entry["count"] for entry in data if entry["keyword"]}

# Генерация облака слов
wordcloud = WordCloud(
    width=1600,
    height=800,
    background_color="white",
    max_words=150
).generate_from_frequencies(word_freq)

# Отображение
plt.figure(figsize=(20, 10))
plt.imshow(wordcloud, interpolation="bilinear")
plt.axis("off")
plt.title("Облако ключевых слов", fontsize=24)
plt.show()
