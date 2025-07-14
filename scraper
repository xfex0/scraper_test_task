import requests
from bs4 import BeautifulSoup
import json
import re
import logging
import time
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class McDonaldsScraper:
    BASE_URL = "https://www.mcdonalds.com/ua/uk-ua/eat/fullmenu.html"
    
    def __init__(self, timeout: int = 10, retry_count: int = 3):
        self.menu_items = []
        self.timeout = timeout
        self.retry_count = retry_count
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_menu(self) -> bool:
        """
        Main method to scrape McDonald's menu
        Returns: bool - True if successful, False otherwise
        """
        try:
            logger.info("Starting menu scraping...")
            
            soup = self._get_page_soup(self.BASE_URL)
            if not soup:
                logger.error("Failed to load main page")
                return False
            
            items = soup.select('.menu-item')
            
            if not items:
                logger.warning("No menu items found. Trying alternative selectors...")
                alternative_selectors = [
                    '.cmp-category__item',
                    '.menu-category__item',
                    '[data-module="MenuItem"]',
                    '.product-item'
                ]
                
                for selector in alternative_selectors:
                    items = soup.select(selector)
                    if items:
                        logger.info(f"Found {len(items)} items with selector: {selector}")
                        break
                
                if not items:
                    logger.error("No menu items found with any selector")
                    return False
            
            logger.info(f"Found {len(items)} menu items to process")
            
            successful_items = 0
            for i, item in enumerate(items, 1):
                try:
                    logger.info(f"Processing item {i}/{len(items)}")
                    
                    item_data = self._extract_item_data(item)
                    if item_data:
                        self.menu_items.append(item_data)
                        successful_items += 1
                
                    time.sleep(0.2)
                    
                except Exception as e:
                    logger.error(f"Error processing item {i}: {str(e)}")
                    continue
            
            if successful_items > 0:
                logger.info(f"Successfully processed {successful_items} items")
                self._save_to_json()
                return True
            else:
                logger.error("No items were successfully processed")
                return False
                
        except KeyboardInterrupt:
            logger.info("Scraping interrupted by user")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during scraping: {str(e)}")
            return False
    
    def _get_page_soup(self, url: str) -> Optional[BeautifulSoup]:
        """
        Get BeautifulSoup object for a given URL with retry logic
        """
        for attempt in range(self.retry_count):
            try:
                logger.info(f"Attempting to load {url} (attempt {attempt + 1}/{self.retry_count})")
                
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                logger.info("Page loaded successfully")
                return soup
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1}")
                if attempt < self.retry_count - 1:
                    time.sleep(2 ** attempt)  
                    
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error on attempt {attempt + 1}")
                if attempt < self.retry_count - 1:
                    time.sleep(2 ** attempt)
                    
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error: {e}")
                if e.response.status_code == 429:  
                    if attempt < self.retry_count - 1:
                        time.sleep(5)
                        continue
                break
                
            except Exception as e:
                logger.error(f"Unexpected error loading page: {str(e)}")
                break
        
        return None
    
    def _extract_item_data(self, item) -> Optional[Dict[str, Any]]:
        """
        Extract data from a single menu item
        """
        try:
            name_selectors = ['.item-name', '.cmp-category__item-name', '.product-name', 'h3', 'h4']
            description_selectors = ['.item-description', '.cmp-category__item-description', '.product-description', 'p']
            portion_selectors = ['.portion-size', '.serving-size', '.weight']
            
            item_data = {
                'name': self._extract_text_by_selectors(item, name_selectors),
                'description': self._extract_text_by_selectors(item, description_selectors),
                'calories': self._extract_nutrition(item, 'calories'),
                'fats': self._extract_nutrition(item, 'fats'),
                'carbs': self._extract_nutrition(item, 'carbs'),
                'proteins': self._extract_nutrition(item, 'proteins'),
                'unsaturated_fats': self._extract_nutrition(item, 'unsaturated-fats'),
                'sugar': self._extract_nutrition(item, 'sugar'),
                'salt': self._extract_nutrition(item, 'salt'),
                'portion': self._extract_text_by_selectors(item, portion_selectors)
            }            
            if not item_data['name']:
                logger.warning("Item has no name, skipping")
                return None
            
            logger.debug(f"Successfully extracted data for: {item_data['name']}")
            return item_data
            
        except Exception as e:
            logger.error(f"Error extracting item data: {str(e)}")
            return None
    
    def _extract_text_by_selectors(self, item, selectors: list) -> str:
        """
        Try multiple selectors to extract text
        """
        for selector in selectors:
            try:
                element = item.select_one(selector)
                if element:
                    text = self._clean_text(element.text)
                    if text:
                        return text
            except Exception as e:
                logger.debug(f"Error with selector {selector}: {str(e)}")
                continue
        
        return ""
    
    def _extract_nutrition(self, item, nutrient: str) -> Optional[str]:
        """
        Extract specific nutrient values from menu item
        """
        try:            
            nutrition_selectors = [
                f'.nutrition-{nutrient}',
                f'[data-nutrient="{nutrient}"]',
                f'.{nutrient}',
                f'[class*="{nutrient}"]'
            ]
            
            for selector in nutrition_selectors:
                try:
                    element = item.select_one(selector)
                    if element:
                        value = self._clean_text(element.text)
                        if value:
                            return value
                except Exception:
                    continue            
           
            text_content = item.get_text()
            nutrition_patterns = {
                'calories': r'(\d+)\s*(?:кал|cal|ккал)',
                'fats': r'жир[иы]?\s*:?\s*(\d+(?:\.\d+)?)\s*г',
                'carbs': r'вуглевод[иы]?\s*:?\s*(\d+(?:\.\d+)?)\s*г',
                'proteins': r'білк[иы]?\s*:?\s*(\d+(?:\.\d+)?)\s*г',
                'sugar': r'цукор\s*:?\s*(\d+(?:\.\d+)?)\s*г',
                'salt': r'сіль\s*:?\s*(\d+(?:\.\d+)?)\s*г'
            }
            
            if nutrient in nutrition_patterns:
                match = re.search(nutrition_patterns[nutrient], text_content, re.IGNORECASE)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting nutrition {nutrient}: {str(e)}")
            return None
    
    def _clean_text(self, text: Optional[str]) -> str:
        """
        Clean and normalize text
        """
        if not text:
            return ""
        
        try:            
            cleaned = re.sub(r'\s+', ' ', text).strip()            
            cleaned = re.sub(r'[^\w\s\-.,()/:№]', '', cleaned)
            return cleaned
        except Exception as e:
            logger.debug(f"Error cleaning text: {str(e)}")
            return str(text) if text else ""
    
    def _save_to_json(self, filename: str = 'menu_data.json') -> bool:
        """
        Save menu items to JSON file
        """
        try:
            if not self.menu_items:
                logger.warning("No menu items to save")
                return False
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.menu_items, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Successfully saved {len(self.menu_items)} items to {filename}")
            return True
            
        except IOError as e:
            logger.error(f"Error saving to file {filename}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving file: {str(e)}")
            return False
    
    def get_menu_items(self) -> list:
        """
        Get the scraped menu items
        """
        return self.menu_items
    
    def clear_menu_items(self):
        """
        Clear the current menu items
        """
        self.menu_items = []
        logger.info("Menu items cleared")

if __name__ == "__main__":
    scraper = McDonaldsScraper()
    
    try:
        success = scraper.scrape_menu()
        
        if success:
            items = scraper.get_menu_items()
            print(f"Successfully scraped {len(items)} menu items")
            
            for i, item in enumerate(items[:3]):
                print(f"\nItem {i+1}:")
                print(f"  Name: {item['name']}")
                print(f"  Description: {item['description'][:100]}...")
                print(f"  Calories: {item['calories']}")
        else:
            print("Scraping failed")
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")