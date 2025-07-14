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

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.menu_items = []

    def scrape_menu(self):
        try:
            logging.info("Скрапінг головного меню")
            self.driver.get(self.BASE_URL)
            time.sleep(5)  # дати JavaScript завантажити

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            product_links = []
            for a in soup.select('a.cmp-category__item-link'):
                href = a.get('href')
                if href and '/product/' in href:
                    full_url = urljoin(self.BASE_URL, href)
                    if full_url not in product_links:
                        product_links.append(full_url)

            logging.info(f"Знайдено {len(product_links)} продуктів")

            for i, link in enumerate(product_links, 1):
                logging.info(f"Обробка {i}/{len(product_links)}: {link}")
                product_data = self._scrape_product_page(link)
                if product_data:
                    self.menu_items.append(product_data)

            self._save_to_json()
            self.driver.quit()

        except Exception as e:
            logging.error(f"Критична помилка: {str(e)}")
            self.driver.quit()

    
    def _scrape_product_page(self, url):          
        
        try: 
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'h1'))
)
            nutrition_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Енергетична цінність')]"))
            )
            nutrition_button.click()
    
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.cmp-nutrition-summary__details-row"))
            )
        except Exception as e:
            logging.warning(f"⚠ Не вдалося відкрити нутрієнти: {e}")

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            name = soup.select_one('h1')
            description = soup.select_one('div.cmp-product-details-main__description')
            portion = soup.select_one('span.cmp-product-details-main__weight')

            product = {
                'name': self._clean_text(name.text) if name else "",
                'description': self._clean_text(description.text) if description else "",
                'portion': self._clean_text(portion.text) if portion else "",
            }

            nutrition = self._extract_nutrition(soup)
            product.update(nutrition)

            return product

        except Exception as e:
            logging.error(f"Помилка при обробці {url}: {str(e)}")
            return None
        

    def _extract_nutrition(self, soup):
        nutrition = {}

        
        blocks = soup.select('div.cmp-nutrition-summary__details-row')
        for block in blocks:
            try:
                label = block.select_one('span.cmp-nutrition-summary__heading-item-name')
                value = block.select_one('span.cmp-nutrition-summary__heading-item-value')

                if not label or not value:
                    continue

                name = self._clean_text(label.text).lower()
                val = self._clean_text(value.text)

                if 'Калорійність' in name:
                    nutrition['calories'] = val
                elif 'Жири' in name:
                    nutrition['fats'] = val
                elif 'Вуглеводи' in name:
                    nutrition['carbs'] = val
                elif 'Білки' in name:
                    nutrition['proteins'] = val
                elif 'Цукор' in name:
                    nutrition['sugar'] = val
                elif 'Сіль' in name:
                    nutrition['salt'] = val
                elif 'Ненасичені жири' in name:
                    nutrition['unsaturated fats'] = val
            except Exception as e:
                continue

        
        for key in ["calories", "fats", "carbs", "proteins", "sugar", "salt", "unsaturated fats"]:
            if key not in nutrition:
                nutrition[key] = ""

        return nutrition

    def _clean_text(self, text):
            if not text:
                return ""
            return re.sub(r'\s+', ' ', text.replace('\xa0', ' ')).strip()

    def _save_to_json(self, filename='menu_data.json'):
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.menu_items, f, ensure_ascii=False, indent=2)
                logging.info(f"Дані збережено у {filename}")
            except Exception as e:
                logging.error(f"Не вдалося зберегти JSON: {str(e)}")

if __name__ == "__main__":
    scraper = McDonaldsUaScraperSelenium()
    scraper.scrape_menu()
    print("✅ Готово. Перевір menu_data.json")
