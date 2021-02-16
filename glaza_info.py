import requests
import os
from bs4 import BeautifulSoup
import json


def get_all_ad(page: str) -> list:
    """ Получаем код страницы и выбираем ссылки на объявления
        page: text url
        :return list
    """
    soup = BeautifulSoup(page, features="lxml")
    urls = soup.find('div', {'id': 'dle-content'}).find_all('h3', {'class': 'h5 mb-0 short-title'})
    urls_array = [url.find('a').get('href') for url in urls]
    return urls_array


def get_date_in_html(page: str) -> dict:
    """ Получаем код страницы и создаем словарь с данными для получения формы
        page: text url
        :return словарь с formConfig, id, date
    """
    soup = BeautifulSoup(page, features="lxml")
    dat = soup.find('div', {'id': 'top-modal'}).find("div", {"class": "btn-vip"}).get("data-uf-settings")
    return json.loads(dat)


def get_date_post(page: str) -> dict:
    """ Получаем код страницы в текстовом формате
    забираем данные с именами: csrfToken, formConfig, id, username и создаем словарь
    page: text url
    :return: dict: csrfToken, formConfig, id, username
    """
    soup = BeautifulSoup(page, features='lxml')
    dat = soup.find('form', {"method": "POST"}).find_all("input", {"type": "hidden"})
    return {name.get('name'): name.get('value') for name in dat}


def check_ad(page: str) -> str:
    """ Проверим можно ли поднять объявление
    :param page: str - html страница с объявлением
    :return: str
    """
    soup = BeautifulSoup(page, features='lxml')
    try:
        dat = soup.find('div', {'id': 'top-modal'}).find("div", {"class": "btn-vip"}).\
            find("span", {"class": "result-date"}).text
    except:
        dat = False
    return dat

def login_glaza_info(login: str, password: str):
    with requests.Session() as s:
        # Шапка для отправки GET запроса.
        headers = {
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0",
        }

        # Данные для POST запроса для авторизации на сайте
        data = {
            "login_name": login,
            "login_password": password,
            "login": "submit"
        }

        # Подгружаем первую страницу и полуаем cookie
        s.get(url="https://glaza.info", headers=headers)

        # Авторизуемся на сайте
        r = s.post(url="https://glaza.info", data=data)

        # # Сохраняем cookies они понадабятся в будуйщем для отправки запросов.
        # cooki = r.cookies.get_dict()

        # получаем страницу с объявлениями
        get_ads = s.get(url="https://board.glaza.info/user/vova/news/")

        # Получаем список ссылок на существующие объявления
        ad_urls = get_all_ad(get_ads.text)

        # Пройдемся по каждой ссылке и поднимем объявление
        for url in ad_urls:
            # Получам страницу с объявлением
            url_for_up = s.get(url=url)

            # Проверяем доступно ли поднятие объявления
            check = check_ad(url_for_up.text)
            if check:
                print("\033[31m {}\033[0m" .format(check))
                break

            # Забираем из полученой страницы, url_for_up, данные для GET запроса
            date_in_html = get_date_in_html(url_for_up.text)

            # Забираем данные с GET запроса для получения формы
            data = {
                "formConfig": date_in_html["formConfig"],
                "fields[id]": date_in_html["fields"]["id"],
                "fields[date]": date_in_html["fields"]["date"],
            }

            # Добавляем данные в headers для корректнго полученя формы.
            headers["X-Requested-With"] = "XMLHttpRequest"

            # Получаем страницу с формой для POST запроса
            url_for_with_post = s.get(url="https://board.glaza.info/engine/ajax/uniform/uniform.php",
                                      params=data,
                                      headers=headers).text
            # Создаем славарь для отправки POST запроса
            dict_for_post = get_date_post(url_for_with_post)

            # Отправляем POST запрос и тем самым поднимаем объявление
            s.post(url="https://board.glaza.info/engine/ajax/uniform/uniform.php",
                   data=dict_for_post,
                   headers=headers)



# login и password сохранены в виртуальной среде. Подгружаем их
LOGIN = os.getenv("LOGIN_GLAZA")
PASSWORD = os.getenv("PASSWORD_GLAZA")

res = login_glaza_info(LOGIN, PASSWORD)
