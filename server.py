"""
Антифишинг API-сервер
Проверяет домены и URL-адреса через официальный API Центрального Банка РФ
Назначение: серверная часть браузерного расширения для выявления
           мошеннических сайтов из предупредительного списка ЦБ РФ
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from datetime import datetime, timedelta

app = FastAPI(title="Антифишинг API", version="1.0")

# Перечень доменных имён социальных сетей.
# Для URL-адресов, принадлежащих данным доменам, выполняется
# проверка полного пути, а не только доменного имени.
SOCIAL_MEDIA_DOMAINS = [
    "vk.com", "vk.ru", "vkontakte.ru",
    "ok.ru", "odnoklassniki.ru",
    "t.me", "telegram.org",
    "youtube.com", "youtu.be",
    "dzen.ru",
    "rutube.ru",
]

# Разрешение Cross-Origin Resource Sharing (CORS)
# для взаимодействия с браузерным расширением.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Кэш-хранилище результатов проверки.
# Ключ: поисковый запрос (домен или URL).
# Значение: словарь с результатом проверки и временем сохранения.
cache = {}
CACHE_DAYS = 1  # срок хранения записей в кэше (в сутках)


def log(message: str, level: str = "INFO"):
    """Выводит сообщение в консоль сервера с меткой времени и уровнем."""
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] [{level}] {message}")


def extract_domain(url: str) -> str:
    """
    Извлекает доменное имя из полного URL-адреса.

    Параметры:
        url (str): полный URL-адрес (например, "https://example.com/path").

    Возвращает:
        str: доменное имя в нижнем регистре без протокола, пути и префикса "www.".
    """
    url = url.lower().strip()
    if "://" in url:
        url = url.split("://")[1]
    domain = url.split("/")[0]
    domain = domain.split(":")[0]
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def is_social_media(domain: str) -> bool:
    """
    Проверяет, относится ли домен к социальным сетям из заданного перечня.

    Параметры:
        domain (str): доменное имя для проверки.

    Возвращает:
        bool: True, если домен является социальной сетью, иначе False.
    """
    domain_clean = domain.lower().replace("www.", "")
    for sm_domain in SOCIAL_MEDIA_DOMAINS:
        if domain_clean == sm_domain or domain_clean.endswith("." + sm_domain):
            return True
    return False


def is_exact_domain_match(domain: str, sites: str) -> bool:
    """
    Выполняет точное сравнение доменного имени со списком сайтов организации.

    Параметры:
        domain (str): проверяемое доменное имя.
        sites (str): строка, содержащая сайты организации (через запятую, точку с запятой или пробел).

    Возвращает:
        bool: True, если найдено точное совпадение доменных имён, иначе False.
    """
    if not sites:
        return False

    # Нормализация строки с сайтами: приведение к единому разделителю ","
    sites_clean = sites.lower().replace(";", ",").replace(" ", ",")
    site_list = [s.strip() for s in sites_clean.split(",") if s.strip()]

    domain_clean = domain.lower()
    if domain_clean.startswith("www."):
        domain_clean = domain_clean[4:]

    for site in site_list:
        site_clean = site.lower()
        # Удаление протокола и пути
        if "://" in site_clean:
            site_clean = site_clean.split("://")[1]
        site_clean = site_clean.split("/")[0]
        if site_clean.startswith("www."):
            site_clean = site_clean[4:]

        if site_clean == domain_clean:
            return True

    return False


def term_in_sites(term: str, sites: str) -> bool:
    """
    Проверяет, содержится ли заданный поисковый запрос (полный URL)
    в списке сайтов организации. Используется для точного сопоставления
    URL-адресов социальных сетей и иных ресурсов, где важен полный путь.

    Параметры:
        term (str): поисковый запрос (URL без протокола).
        sites (str): строка с сайтами организации.

    Возвращает:
        bool: True, если найдено точное совпадение полного URL, иначе False.
    """
    if not sites or not term:
        return False

    sites_lower = sites.lower()
    sites_clean = sites_lower.replace(";", ",").replace(" ", ",")
    site_list = [s.strip() for s in sites_clean.split(",") if s.strip()]

    for site in site_list:
        site_clean = site
        if "://" in site_clean:
            site_clean = site_clean.split("://")[1]
        if site_clean.startswith("www."):
            site_clean = site_clean[4:]

        # Точное совпадение полного URL (включая путь)
        if site_clean == term.lower():
            return True

        # Дополнительная проверка: сравнение без протокола
        term_clean = term.lower()
        if term_clean.startswith("https://"):
            term_clean = term_clean[8:]
        elif term_clean.startswith("http://"):
            term_clean = term_clean[7:]

        if site_clean == term_clean:
            return True

    return False


def check_cbr_api(search_term: str) -> dict:
    """
    Выполняет проверку через публичный API Центрального Банка РФ.
    Осуществляет поиск организаций по заданному термину, затем для каждой
    найденной организации загружает детальную информацию и выполняет
    точное сопоставление доменного имени или полного URL.

    Параметры:
        search_term (str): поисковый запрос (домен или URL без протокола).

    Возвращает:
        dict: словарь с результатами проверки. Ключи:
              - found (bool): True, если найдены совпадения.
              - count (int): количество найденных организаций.
              - companies (list): список организаций (до 5 элементов).
              - error (str): описание ошибки (если есть).
    """
    api_url = "http://www.cbr.ru/warninglistapi/Search"

    log(f"Запрос к API ЦБ РФ: поиск \"{search_term}\"")

    try:
        response = requests.get(
            api_url,
            params={"sphrase": search_term, "page": 0},
            timeout=5
        )

        if response.status_code != 200:
            log(f"Ошибка API ЦБ РФ: код ответа {response.status_code}", "ERROR")
            return {"found": False, "error": f"API вернул код {response.status_code}"}

        data = response.json()
        companies = data.get("Data", [])

        if not companies:
            log(f"По запросу \"{search_term}\" организаций не найдено")
            return {"found": False, "count": 0}

        log(f"Найдено {len(companies)} организаций. Выполняется проверка точных совпадений...")

        matched_companies = []

        for company in companies:
            company_id = company.get("id")
            if not company_id:
                continue

            try:
                detail_response = requests.get(
                    "http://www.cbr.ru/warninglistapi/DetailInfo",
                    params={"id": company_id},
                    timeout=3
                )

                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    info = detail_data.get("Info", [{}])[0]
                    sites = info.get("site", "")

                    # Два метода проверки:
                    # 1) точное совпадение доменного имени (для обычных сайтов);
                    # 2) точное совпадение полного URL (для социальных сетей).
                    if is_exact_domain_match(search_term, sites) or term_in_sites(search_term, sites):
                        matched_companies.append({
                            "name": info.get("nameOrg", "Неизвестно"),
                            "id": company_id,
                            "date_added": info.get("dt", "Неизвестно"),
                            "comment": info.get("comment", ""),
                            "sites": sites
                        })
            except requests.exceptions.RequestException:
                continue

        if matched_companies:
            log(f"Обнаружены совпадения со списком ЦБ РФ: {len(matched_companies)} организаций", "WARNING")
            for mc in matched_companies:
                log(f"  - {mc['name']} (дата внесения: {mc['date_added']})", "WARNING")
            return {
                "found": True,
                "count": len(matched_companies),
                "companies": matched_companies[:5]
            }
        else:
            log("Точных совпадений не обнаружено")
            return {"found": False, "count": 0}

    except requests.exceptions.Timeout:
        log("Таймаут при обращении к API ЦБ РФ", "ERROR")
        return {"found": False, "error": "Таймаут запроса к API ЦБ РФ"}
    except requests.exceptions.ConnectionError:
        log("Ошибка соединения с API ЦБ РФ", "ERROR")
        return {"found": False, "error": "Нет соединения с API ЦБ РФ"}
    except Exception as e:
        log(f"Непредвиденная ошибка: {str(e)}", "ERROR")
        return {"found": False, "error": str(e)}


@app.get("/")
def root():
    """
    Корневой маршрут API.
    Используется для проверки работоспособности сервера.

    Возвращает:
        dict: информация о статусе сервера и доступных маршрутах.
    """
    log("Проверка работоспособности сервера")
    return {
        "status": "ok",
        "service": "Антимошейник API",
        "version": "1.0",
        "endpoints": ["/check-url", "/check-domain"]
    }


@app.get("/check-domain")
def check_domain(domain: str, full_url: str = None):
    """
    Проверяет доменное имя (или полный URL для социальных сетей)
    по предупредительному списку Центрального Банка РФ.

    Параметры:
        domain (str): доменное имя для проверки.
        full_url (str, опционально): полный URL для проверки социальных сетей.

    Возвращает:
        dict: результат проверки со следующими ключами:
              - found (bool): найдено ли совпадение.
              - checked_domain (str): проверенное доменное имя.
              - checked_term (str): поисковый запрос, переданный в API ЦБ РФ.
              - is_social_media (bool): является ли домен социальной сетью.
              - source (str): источник результата ("cache" или "cbr_api").
              - companies (list): список найденных организаций (если found=True).
    """
    domain = extract_domain(domain)

    # Определение поискового запроса
    if is_social_media(domain) and full_url:
        # Для социальных сетей используется URL без протокола
        search_term = full_url.lower()
        if search_term.startswith("https://"):
            search_term = search_term[8:]
        elif search_term.startswith("http://"):
            search_term = search_term[7:]
        log(f"Проверка социальной сети: \"{search_term}\"")
    else:
        search_term = domain
        log(f"Проверка веб-сайта: домен \"{search_term}\"")

    # Проверка кэша
    cache_key = search_term
    if cache_key in cache:
        cached = cache[cache_key]
        if datetime.now() - cached["date"] < timedelta(days=CACHE_DAYS):
            log(f"Результат получен из кэша для \"{cache_key}\"")
            return {**cached["result"], "source": "cache"}

    # Обращение к API ЦБ РФ
    result = check_cbr_api(search_term)

    # Сохранение в кэш
    cache[cache_key] = {
        "result": result,
        "date": datetime.now()
    }

    result["checked_domain"] = domain
    result["checked_term"] = search_term
    result["is_social_media"] = is_social_media(domain)
    result["source"] = "cbr_api"

    return result


@app.get("/check-url")
def check_url(url: str):
    """
    Проверяет URL-адрес: извлекает домен, для социальных сетей
    выполняет проверку по полному URL.

    Параметры:
        url (str): полный URL-адрес для проверки.

    Возвращает:
        dict: результат проверки (см. check_domain) с дополнительным ключом
              original_url (str) — исходный проверяемый URL.
    """
    domain = extract_domain(url)

    log(f"Получен URL для проверки: \"{url}\"")

    if is_social_media(domain):
        result = check_domain(domain, full_url=url)
    else:
        result = check_domain(domain)

    result["original_url"] = url
    return result


# Точка входа серверного приложения
if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("Антимошейник API запущен.")
    print("Документация API: http://localhost:8000/docs")
    print("Пример запроса: http://localhost:8000/check-domain?domain=example.com")
    print("=" * 50)
    uvicorn.run(app, host="127.0.0.1", port=8000)