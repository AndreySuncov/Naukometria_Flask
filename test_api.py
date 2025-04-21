from datetime import datetime

import pytest
from app import app
import json
import psycopg2
import json
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT", 5432)
}


@pytest.fixture(scope='module')
def test_db():
    # Настройка тестовой БД
    test_config = DB_CONFIG.copy()
    test_config['dbname'] = 'test_db'

    conn = psycopg2.connect(**test_config)
    yield conn
    conn.close()

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_data_integrity(client):
    response = client.get('/api/authors?limit=1')
    if response.status_code == 200:
        data = json.loads(response.data)
        if data:
            author = data[0]
            assert isinstance(author['authorid'], int)
            assert isinstance(author['lastname'], str)


def test_error_structure(client):
    response = client.get('/api/invalid_endpoint')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Not found' in data['error']


# Тесты для /api/authors
def test_authors_endpoint(client):
    # Тестирование базового запроса
    response = client.get('/api/authors?limit=5')
    assert response.status_code == 200
    data = json.loads(response.data)
    if data:  # Проверяем только если есть данные
        assert all(key in data[0] for key in ['authorid', 'lastname', 'email'])

    # Более безопасная проверка комбинации фильтров
    response = client.get('/api/authors?lastname=Иванов&status=100&language=ru')
    assert response.status_code in [200, 404]  # Допускаем 404 если нет данных
    if response.status_code == 200:
        data = json.loads(response.data)
        for author in data:
            assert 'иванов' in author['lastname'].lower()
            assert author['status'] == 1
            assert author['language'] == 'RU'


# Тесты для /api/items
def test_items_endpoint(client):
    # Фильтр по году и типу
    response = client.get('/api/items?year_from=2020&typecode=book&limit=3')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert all(item['year'] >= 2020 and
               item['typecode'] == 'book' for item in data)

    # Комплексный фильтр
    params = {
        'title': 'Физика',
        'year_from': 2015,
        'year_to': 2020,
        'language': 'ru'
    }
    response = client.get('/api/items', query_string=params)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert all('физика' in item['title'].lower() and
               2015 <= item['year'] <= 2020 and
               item['language'] == 'RU' for item in data)


# Тесты для /api/affiliations
def test_affiliations_endpoint(client):
    # Фильтр по стране и городу
    response = client.get('/api/affiliations?country=Россия&town=Москва')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert all(aff['country'].lower() == 'россия' and
               'москва' in aff['town'].lower() for aff in data)

    # Фильтр по автору
    response = client.get('/api/affiliations?author=123&limit=2')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert all(aff['author'] == 123 for aff in data)


# Тесты для /api/organizations
def test_organizations_endpoint(client):
    # Поиск по стране и названию
    response = client.get('/api/organizations?countryid=RU&organizationname=библиотека')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert all(org['countryid'] == 'RU' and
               'библиотека' in org['organizationname'].lower() for org in data)


# Тесты для /api/keywords
def test_keywords_endpoint(client):
    # Фильтр по языку и ключевому слову
    response = client.get('/api/keywords?language=en&keyword=physics')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert all(kw['language'] == 'EN' and
               'physics' in kw['keyword'].lower() for kw in data)


# Тесты для /api/references
def test_references_endpoint(client):
    # Проверка всех справочников
    references = [
        'typecode', 'genreid', 'language', 'status',
        'countries', 'towns', 'organization_countries'
    ]

    for ref in references:
        response = client.get(f'/api/references/{ref}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data[ref], list)


def test_error_handling(client):
    # Несуществующий справочник
    response = client.get('/api/references/invalid_ref')
    assert response.status_code == 404

    # Неверный тип данных - проверяем что возвращается ошибка (500 или 400)
    response = client.get('/api/authors?limit=invalid')
    assert response.status_code in [400, 500]
    if response.status_code == 500:
        data = json.loads(response.data)
        assert 'error' in data


# Тесты пагинации
def test_pagination(client):
    # Проверка работы offset
    response1 = client.get('/api/items?limit=5&offset=0')
    data1 = json.loads(response1.data)
    response2 = client.get('/api/items?limit=5&offset=5')
    data2 = json.loads(response2.data)

    assert len(data1) == 5
    assert len(data2) == 5
    assert data1[-1]['itemid'] != data2[0]['itemid']


def test_special_characters(client):
    # Проверяем что запрос с спецсимволами не вызывает ошибок
    special_cases = [
        "O%27Reilly",  # Апостроф
        "Smith-Jones",  # Дефис
        "Café",  # Диакритические знаки
        "株式会社"  # Иероглифы
    ]

    for case in special_cases:
        response = client.get(f'/api/organizations?organizationname={case}')
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert isinstance(data, list)


def test_publications_by_year(client):
    # Тест с дефолтными параметрами
    response = client.get('/api/statistics/publications-by-year')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, dict)
    for year, count in data.items():
        assert 2000 <= int(year) <= datetime.now().year
        assert isinstance(count, int)

    # Тест с кастомным диапазоном
    response = client.get('/api/statistics/publications-by-year?year_from=2010&year_to=2020')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert all(2010 <= int(year) <= 2020 for year in data.keys())


def test_authors_by_city_distribution(client):
    # Тест с минимальным количеством публикаций
    response = client.get('/api/statistics/authors-by-city?min_publications=5')
    assert response.status_code == 200
    data = json.loads(response.data)
    for entry in data:
        assert entry[1] >= 5

    # Тест без параметра (должен использовать дефолтное значение 10)
    response = client.get('/api/statistics/authors-by-city')
    assert response.status_code == 200
    data = json.loads(response.data)
    for entry in data:
        assert entry[1] >= 10

def test_authors_by_city_search(client):
    # Тест с существующим городом
    response = client.get('/api/authors/by-city?city=Москва')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) > 0
    assert all(isinstance(name, str) for name in data)

    # Тест с частичным совпадением
    response = client.get('/api/authors/by-city?city=Санкт')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) > 0

    # Тест с пустым параметром
    response = client.get('/api/authors/by-city')
    assert response.status_code == 400

def test_all_keywords(client):
    response = client.get('/api/keywords/all')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    for entry in data:
        assert isinstance(entry[0], str)  # keyword
        assert isinstance(entry[1], int)  # count
        assert entry[1] > 0


def test_keywords_statistics_endpoint(client):
    # Базовый тест: получить статистику по ключевым словам за текущий год
    response = client.get('/api/statistics/keywords')
    assert response.status_code == 200
    data = json.loads(response.data)

    assert isinstance(data, list)
    assert len(data) <= 150  # Проверяем лимит в 150
    for entry in data:
        assert isinstance(entry, dict)
        assert 'keyword' in entry
        assert 'language' in entry
        assert 'count' in entry
        assert isinstance(entry['keyword'], str)
        assert isinstance(entry['language'], str)
        assert isinstance(entry['count'], int)
        assert entry['count'] > 0

    # Тест: получить статистику за конкретный год
    response = client.get('/api/statistics/keywords?year=2020')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    for entry in data:
        assert isinstance(entry['keyword'], str)
        assert isinstance(entry['count'], int)

    # Тест: фильтрация по ключевому слову
    response = client.get('/api/statistics/keywords?keyword=интернет')
    assert response.status_code in [200, 404]  # Может быть пустой результат
    if response.status_code == 200:
        data = json.loads(response.data)
        for entry in data:
            assert 'интернет' in entry['keyword'].lower()

    # Тест: фильтрация по языку
    response = client.get('/api/statistics/keywords?language=ru')
    assert response.status_code == 200
    data = json.loads(response.data)
    for entry in data:
        assert entry['language'].upper() == 'RU'
