import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

APP_URL = "https://rebarking.streamlit.app/?admin=1234"

def wake_up_app():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            print(f"접속 중: {APP_URL}")
            page.goto(APP_URL, wait_until="domcontentloaded", timeout=60000)
            
            print("페이지 확인 중...")
            time.sleep(5)

            wake_button = page.get_by_role("button", name="Yes, get this app back up")

            try:
                # 최대 10초 동안 깨우기 버튼을 기다림
                wake_button.wait_for(state="visible", timeout=10000)
                print("💤 앱이 수면 상태입니다. 🔘 깨우기 버튼 클릭!")
                wake_button.click()
                print("⏳ 앱이 다시 시작되는 중입니다...")

                # 앱이 다시 올라오는 동안 최대 60초 대기
                for i in range(12):
                    time.sleep(5)
                    print(f"대기 중... {(i + 1) * 5}초")
                print("✅ 깨우기 작업 완료!")

            except PlaywrightTimeoutError:
                print("✅ 깨우기 버튼이 없습니다. 현재 앱이 이미 실행 중인 것으로 판단합니다.")
            
            time.sleep(3)

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            raise

        finally:
            browser.close()

if __name__ == "__main__":
    wake_up_app()
