import os
import csv
import time
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException
import undetected_chromedriver as uc

output_file = "florida_bars_full.csv"
image_folder = "bar_images"
os.makedirs(image_folder, exist_ok=True)

def download_images(images, name, idx):
    img_paths = []
    for i, img_url in enumerate(images):
        try:
            img_data = requests.get(img_url, timeout=10).content
            safe_name = name.replace(" ", "+").replace("/", "_")
            file_name = f"{safe_name}_{idx}_{i}.jpg"
            file_path = os.path.join(image_folder, file_name)
            with open(file_path, "wb") as handler:
                handler.write(img_data)
            img_paths.append(file_path)
        except Exception as e:
            print(f"❌ Image download failed: {e}")
    return "|".join(img_paths)

def scrape_bars():
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    driver = uc.Chrome(options=options)

    search_query = "Bar in Florida, USA"
    print(f"\n🔍 Searching: {search_query}")
    driver.get("https://www.google.com/maps")
    time.sleep(5)

    search_box = driver.find_element(By.ID, "searchboxinput")
    search_box.clear()
    search_box.send_keys(search_query)
    search_box.send_keys(Keys.ENTER)
    time.sleep(8)

    data = []
    results = driver.find_elements(By.CLASS_NAME, "hfpxzc")

    for idx, r in enumerate(results[:15]):  # scrape 15 bars
        try:
            driver.execute_script("arguments[0].scrollIntoView();", r)
            r.click()
            time.sleep(8)

            try:
                name = driver.find_element(By.CLASS_NAME, "DUwDvf").text
            except:
                name = "Unknown"

            try:
                address = driver.find_element(By.XPATH, '//button[@data-item-id="address"]').text
            except:
                address = "Unknown"

            try:
                hours = driver.find_element(By.CLASS_NAME, "OqCZI").text
            except:
                hours = "Unknown"

            try:
                url = driver.current_url
                latlng = url.split("/@")[1].split(",")[:2]
                latitude = latlng[0]
                longitude = latlng[1]
            except:
                latitude = longitude = "Unknown"

            try:
                image_elements = driver.find_elements(By.CSS_SELECTOR, ".UsdlK img")
                image_urls = list({img.get_attribute("src") for img in image_elements if img.get_attribute("src")})
                images = download_images(image_urls, name, idx)
            except:
                images = "Not Found"

            place_id = name.replace(" ", "+")

            print(f"✅ Extracted: {name}")
            data.append([name, "Bar", address, hours, latitude, longitude, images, place_id])

            time.sleep(3)

        except StaleElementReferenceException:
            print("⚠️ Skipped due to stale element.")
            continue
        except Exception as e:
            print(f"❌ Skipped due to error: {e}")
            continue

    driver.quit()
    return data

def main():
    bars = scrape_bars()
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Type", "Address", "Opening Hours", "Latitude", "Longitude", "Images", "Place ID"])
        writer.writerows(bars)
    print(f"\n✅ Done. Data saved to {output_file}")

if __name__ == "__main__":
    main()
