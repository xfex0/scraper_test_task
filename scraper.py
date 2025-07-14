#scraper.py 
import requests
from bs4 import BeautifulSoup
import json
import re

class McDonaldsScraper:
    BASE_URL = "https://www.mcdonalds.com/ua/uk-ua/eat/fullmenu.html"
    
    def __init__(self):
        self.menu_items = []
    
    def scrape_menu(self):
        try:
            response = requests.get(self.BASE_URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all menu items - this selector needs to be adjusted based on actual page structure
            items = soup.select('.menu-item')
            
            for item in items:
                item_data = {
                    'name': self._clean_text(item.select_one('.item-name').text),
                    'description': self._clean_text(item.select_one('.item-description').text),
                    'calories': self._extract_nutrition(item, 'calories'),
                    'fats': self._extract_nutrition(item, 'fats'),
                    'carbs': self._extract_nutrition(item, 'carbs'),
                    'proteins': self._extract_nutrition(item, 'proteins'),
                    'unsaturated_fats': self._extract_nutrition(item, 'unsaturated-fats'),
                    'sugar': self._extract_nutrition(item, 'sugar'),
                    'salt': self._extract_nutrition(item, 'salt'),
                    'portion': self._clean_text(item.select_one('.portion-size').text)
                }
                self.menu_items.append(item_data)
                
            self._save_to_json()
            return True
        except Exception as e:
            print(f"Error during scraping: {e}")
            return False
    
    def _extract_nutrition(self, item, nutrient):
        # Implementation to extract specific nutrient values
        pass
    
    def _clean_text(self, text):
        return re.sub(r'\s+', ' ', text).strip() if text else ""
    
    def _save_to_json(self, filename='menu_data.json'):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.menu_items, f, ensure_ascii=False, indent=2)