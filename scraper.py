import logging
import json
import re
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

class McDonaldsUaScraperSelenium:
    BASE_URL = "https://www.mcdonalds.com/ua/uk-ua/eat/fullmenu.html"

    def __init__(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.menu_items = []

    def scrape_menu(self):
        try:
            logging.info("Початок збору даних із головного меню")
            self.driver.get(self.BASE_URL)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a.cmp-category__item-link'))
            )

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            product_links = []
            for a in soup.select('a.cmp-category__item-link'):
                href = a.get('href')
                if href and '/product/' in href:
                    full_url = urljoin(self.BASE_URL, href)
                    if full_url not in product_links:
                        product_links.append(full_url)

            logging.info(f"Знайдено {len(product_links)} посилань на продукти")

            for i, link in enumerate(product_links, 1):
                logging.info(f"Обробка {i}/{len(product_links)}: {link}")
                product_data = self._scrape_product_page(link)
                if product_data:
                    self.menu_items.append(product_data)

            self._save_to_json(filename='scraped_menu_data.json')
            self._update_menu_data()

        except Exception as e:
            logging.error(f"Критична помилка під час збору даних: {str(e)}")
        finally:
            self.driver.quit()

    def _scrape_product_page(self, url):
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'h1'))
            )

            logging.info(f"Перевірка наявності кнопки на {url}")
            nutrition_buttons = self.driver.find_elements(By.XPATH, "//button[contains(., 'Енергетична цінність та вміст поживних речовин')]")
            if not nutrition_buttons:
                logging.warning(f"Кнопка не знайдена на {url}")
            else:
                logging.info(f"Знайдено {len(nutrition_buttons)} кнопок")

            try:
                nutrition_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Енергетична цінність та вміст поживних речовин')]"))
                )
                self.driver.execute_script("arguments[0].scrollIntoView(true);", nutrition_button)
                self.driver.execute_script("arguments[0].click();", nutrition_button)
                WebDriverWait(self.driver, 10).until(
                    lambda d: nutrition_button.get_attribute("aria-expanded") == "true"
                )
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ul.cmp-nutrition-summary__heading-primary"))
                )
            except Exception as e:
                logging.warning(f"Не вдалося відкрити деталі поживної цінності для {url}: {str(e)}")

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            name = soup.select_one('h1')
            description = soup.select_one('div.cmp-product-details-main__description')
            portion_span = soup.select_one('div.cmp-product-details-main__sub-heading > span')

            product = {
                'name': self._clean_text(name.text) if name else "",
                'description': self._clean_text(description.text) if description else "",
                'portion': "",
                'calories': "",
                'fats': "",
                'carbs': "",
                'proteins': "",
                'sugar': "",
                'salt': "",
                'unsaturated fats': ""
            }

            if portion_span:
                portion_text = portion_span.text.split('|')[0].strip()
                product['portion'] = self._clean_portion(portion_text)

            nutrition = self._extract_nutrition(soup)
            product.update(nutrition)

            logging.info(f"Отримані дані для {url}: {product}")
            return product

        except Exception as e:
            logging.error(f"Помилка обробки {url}: {str(e)}")
            return None

    def _extract_nutrition(self, soup):
        nutrition = {
            'calories': "",
            'fats': "",
            'carbs': "",
            'proteins': "",
            'sugar': "",
            'salt': "",
            'unsaturated fats': ""
        }

        metric_mapping = {
            'калорійність': 'calories',
            'жири': 'fats',
            'вуглеводи': 'carbs',
            'білки': 'proteins',
            'цукор': 'sugar',
            'сіль': 'salt',
            'нжк': 'unsaturated fats',
        }

        # Парсинг первинних поживних даних
        primary_list = soup.select('ul.cmp-nutrition-summary__heading-primary > li')
        for li in primary_list:
            metric_span = li.select_one('span.metric')
            value_span = li.select_one('span.value')
            if metric_span and value_span:
                metric_text = self._clean_text(metric_span.text).lower().split()[0]
                value_text = self._clean_text(value_span.text)
                key = metric_mapping.get(metric_text, None)
                if key:
                    nutrition[key] = self._clean_nutrition_value(value_text)

        # Парсинг вторинних поживних даних
        secondary_list = soup.select('div.cmp-nutrition-summary__details-column-view-desktop > ul > li')
        for li in secondary_list:
            metric_span = li.select_one('span.metric')
            value_span = li.select_one('span.value')
            if metric_span and value_span:
                metric_text = self._clean_text(metric_span.text).lower().strip(':')
                value_text = self._clean_text(value_span.text)
                key = metric_mapping.get(metric_text, None)
                if key:
                    nutrition[key] = self._clean_nutrition_value(value_text)

        logging.info(f"Поживні дані: {nutrition}")
        return nutrition

    def _clean_text(self, text):
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text.replace('\xa0', ' ')).strip()

    def _clean_portion(self, text):
        match = re.search(r'(\d+)\s*г', text)
        if match:
            return match.group(1) + ' г'
        return ""

    def _clean_nutrition_value(self, val):
        val = val.split('(')[0].strip()  # Видалити відсотки
        val = val.split('/')[0].strip()  # Видалити дубльовані одиниці
        val = re.sub(r'(\d+)([гк])', r'\1 \2', val)  # Додати пробіл між числом і одиницею
        return val

    def _save_to_json(self, filename='menu_data.json'):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.menu_items, f, ensure_ascii=False, indent=2)
            logging.info(f"Дані збережено у {filename}")
        except Exception as e:
            logging.error(f"Не вдалося зберегти JSON: {str(e)}")

    def _update_menu_data(self):
        try:
            with open("menu_data.json", "r", encoding="utf-8") as f:
                existing_data = json.load(f)
            with open("scraped_menu_data.json", "r", encoding="utf-8") as f:
                scraped_data = json.load(f)

            scraped_dict = {item["name"]: item for item in scraped_data}

            for item in existing_data:
                if item["name"] in scraped_dict:
                    scraped_item = scraped_dict[item["name"]]
                    item["portion"] = scraped_item["portion"] if scraped_item["portion"] else item["portion"]
                    item["calories"] = scraped_item["calories"] if scraped_item["calories"] else item["calories"]
                    item["fats"] = scraped_item["fats"] if scraped_item["fats"] else item["fats"]
                    item["carbs"] = scraped_item["carbs"] if scraped_item["carbs"] else item["carbs"]
                    item["proteins"] = scraped_item["proteins"] if scraped_item["proteins"] else item["proteins"]
                    item["sugar"] = scraped_item["sugar"] if scraped_item["sugar"] else item["sugar"]
                    item["salt"] = scraped_item["salt"] if scraped_item["salt"] else item["salt"]
                    item["unsaturated fats"] = scraped_item["unsaturated fats"] if scraped_item["unsaturated fats"] else item["unsaturated fats"]

            with open("menu_data.json", "w", encoding="utf-8") as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)

            print("✅ Оновлено menu_data.json зібраними даними")
        except Exception as e:
            logging.error(f"Помилка оновлення menu_data.json: {str(e)}")

if __name__ == "__main__":
    scraper = McDonaldsUaScraperSelenium()
    scraper.scrape_menu()
    print("✅ Готово. Перевірте menu_data.json")
