from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import os
import logging
import asyncio

from main import bot

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
driver_path = os.path.abspath('chromedriver-win64/chromedriver.exe')

# Set Chrome options
chrome_options = Options()
extension_path = r"C:\Users\upayl\AppData\Local\Google\Chrome\User Data\Default\Extensions\omaabbefbmiijedngplfjmnooppbclkk\3.26.1_0"

chrome_options.add_argument(f'--load-extension={extension_path}')

secret_phrases = ['then', 'sing', 'idea', 'siren', 'van', 'panel', 'drift', 'purpose', 'monkey', 'husband', 'lift',
                  'dilemma', 'dignity', 'lesson', 'oil', 'opinion', 'siege', 'ozone', 'mansion', 'able', 'chunk',
                  'citizen', 'glance', 'penalty']


thx_message = '''*Благодарим вас за покупку* 🤍 
В среднем время начисления звезд варьируется от 1 до 5 минут, очень редко бывают задержки, при сбоях со стороны Телеграм\\. 

🙏 Мы будем рады\\, если вы оставите отзыв о вашем опыте с нами\\. Это поможет нам стать лучше и поможет другим пользователям сделать правильный выбор\\.

📄 *Оставить отзыв можно по ссылке*: 
[Отзывы](https://t.me/starsshoppin/7)

Спасибо, что выбираете нас\\! ❤️'''


def create_driver():
    """Create and configure a new WebDriver instance."""
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver




async def proceed_request(username, amount, user_id):
    await bot.send_message(user_id, thx_message, parse_mode='MarkdownV2')
    username = str(username).replace('@', '')
    url = 'https://fragment.com/stars'
    driver = create_driver()
    driver.get(url)
    await asyncio.sleep(2)
    connect_ton = driver.find_elements(By.CLASS_NAME, 'btn.btn-primary.tm-header-action.tm-header-button.ton-auth-link')
    connect_ton[1].click()
    await asyncio.sleep(1)
    connect_ton = driver.find_elements(By.CLASS_NAME, 'go4005132735')
    connect_ton[1].click()
    await asyncio.sleep(1)
    connect_ton = driver.find_elements(By.CLASS_NAME, 'go1369062826.go1367709889')
    connect_ton[0].click()
    await asyncio.sleep(2)
    driver.switch_to.window(driver.window_handles[-1])
    connect_ton = driver.find_element(By.CLASS_NAME, 'sc-eGCbyA.evrCBR')
    connect_ton.click()
    await asyncio.sleep(1)
    wallet_choice = driver.find_elements(By.CLASS_NAME, 'sc-gVgoeb.jOniwN')
    wallet_choice[1].click()
    await asyncio.sleep(2)
    driver.switch_to.window(driver.window_handles[-1])
    inputs = driver.find_elements(By.TAG_NAME, 'input')
    for input in inputs:
        input.send_keys(secret_phrases[inputs.index(input)])
    await asyncio.sleep(1)
    buttons = driver.find_elements(By.TAG_NAME, 'button')
    buttons[1].click()
    await asyncio.sleep(3)
    button = driver.find_element(By.XPATH, "//*[text()='Продолжить']")
    button.click()
    await asyncio.sleep(3)
    button = driver.find_element(By.XPATH, "//*[text()='Продолжить']")
    button.click()
    await asyncio.sleep(2)
    inputs = driver.find_elements(By.TAG_NAME, 'input')
    inputs.pop(-1)
    [input.send_keys('111111') for input in inputs]
    await asyncio.sleep(2)
    button = driver.find_elements(By.TAG_NAME, "button")
    button = button[-1]
    await asyncio.sleep(2)
    button.click()
    await asyncio.sleep(1)
    button = driver.find_element(By.TAG_NAME, 'button')
    button.click()
    await asyncio.sleep(2)
    driver.switch_to.window(driver.window_handles[0])
    await asyncio.sleep(2)
    button = driver.find_element(By.CLASS_NAME, 'go1763956052')
    button.click()
    await asyncio.sleep(2)
    driver.switch_to.window(driver.window_handles[-1])
    button = driver.find_element(By.TAG_NAME, 'button')
    button.click()
    await asyncio.sleep(2)
    input = driver.find_element(By.ID, 'unlock-password')
    input.send_keys('111111')
    await asyncio.sleep(2)
    button = driver.find_element(By.XPATH, "//*[text()='Подтвердить']")
    while button.get_attribute('disabled') is not None:
        await asyncio.sleep(1)
    button.click()
    await asyncio.sleep(2)
    driver.switch_to.window(driver.window_handles[0])
    input = driver.find_element(By.CLASS_NAME, 'form-control.tm-input.tm-search-input')
    input.send_keys(username)
    input = driver.find_element(By.CLASS_NAME, 'form-control.tm-input.tm-amount-input')
    input.send_keys(str(amount))
    await asyncio.sleep(6)
    button = driver.find_element(By.CLASS_NAME, 'btn.btn-primary.btn-block.js-stars-buy-btn')
    button.click()
    await asyncio.sleep(6)
    buttons = driver.find_elements(By.CLASS_NAME, 'btn.btn-primary.btn-block')
    buttons[-1].click()
    await asyncio.sleep(6)
    driver.switch_to.window(driver.window_handles[-1])
    buttons = driver.find_elements(By.TAG_NAME, 'button')
    buttons[-1].click()
    await asyncio.sleep(3)
    inputs = driver.find_elements(By.TAG_NAME, 'input')
    for input in inputs:
        if input.get_attribute('id') == 'unlock-password':
            input.send_keys('111111')
            await asyncio.sleep(1)
            input.send_keys(Keys.RETURN)
            break
    driver.switch_to.window(driver.window_handles[0])
    await asyncio.sleep(2)
    try:
        h1 = driver.find_elements(By.TAG_NAME, 'h1')
        start_time = time.time()
        while len(h1) <= 0:
            await asyncio.sleep(2)
            now = time.time()
            if now-start_time > 500:
                driver.quit()
                return
            h1 = driver.find_elements(By.TAG_NAME, 'h1')
            
        print(h1)
        h1 = [h1 for h1 in h1 if h1.get_attribute('class') == 'tm-main-intro-header']
        print(h1)
        h1 = h1[0]
        text = h1.text
        start_time = time.time()
        while 'acquired' not in text.lower():
            h1 = driver.find_element(By.CLASS_NAME, 'tm-main-intro-header')
            text = h1.text
            await asyncio.sleep(2)
            now = time.time()
            if now-start_time > 500:
                driver.quit()
                return
        await bot.send_message(user_id, '🎉 *Ваши звёзды успешно отправлены\\!* Спасибо за покупку\\. 🌟 ', parse_mode='MarkdownV2')
        driver.quit()
    except Exception as e:
        print(e)
        await asyncio.sleep(300)
        driver.quit()

