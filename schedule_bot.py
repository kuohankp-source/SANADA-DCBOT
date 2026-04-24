import os
import json
import gspread
import requests
from google.oauth2.service_account import Credentials
from tenacity import retry, stop_after_attempt, wait_exponential

# ==========================================
# 0. 系統登入與驗證 (與交接單共用同一把鑰匙)
# ==========================================
scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds_json = json.loads(os.environ['GCP_CREDENTIALS'])
creds = Credentials.from_service_account_info(creds_json, scopes=scopes)
client = gspread.authorize(creds)

# ==========================================
# 1. 發送到 Discord 的共用邏輯 (含防護機制)
# ==========================================
@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=60))
def send_to_discord(webhook_url, msg):
    if not webhook_url:
        print("⚠️ 找不到 Webhook 網址，請檢查 GitHub Secrets 設定。")
        return
    
    payload = {'content': msg}
    response = requests.post(webhook_url, json=payload)
    response.raise_for_status()
    print("✅ 班表與天氣傳送成功！")

# ==========================================
# 2. 抓取班表與天氣邏輯
# ==========================================
def send_tomorrow_schedule():
    print("🚀 正在處理明日班表與天氣...")
    
    # 🔽 請把這裡換成你「連續排班紀錄」試算表的真實 ID 🔽
    SCHEDULE_SHEET_ID = "1kwUv7zErhabxojE3EPec3GSCkoqxoq8s8lufgiYwDtg" 
    
    try:
        sheet = client.open_by_key(SCHEDULE_SHEET_ID).worksheet("每日傳送班表")
        
        # 高效抓取區塊資料
        date_title = sheet.acell('K2').value                 # 明日日期
        schedule_block = sheet.get_values('I3:L8')           # 人員班表
        form_link_block = sheet.get_values('I9:J9')          # 表單名稱與網址
       # 🎯 修正 1：把範圍擴大到 L22，確保絕對不會漏抓底部的網址
        weather_block = sheet.get_values('I10:L22')          
        
        # 組合文字
        message_lines = [f"📅 **{date_title}**"]
        
        # 班表區塊
        for row in schedule_block:
            message_lines.append(" ".join([str(cell) for cell in row if cell]))
            
        message_lines.append("") # 空行
        
        # 異動表單連結區塊
        if form_link_block:
            message_lines.append(" ".join([str(cell) for cell in form_link_block[0] if cell]))
            
        message_lines.append("") # 空行
        
        # 🎯 修正 2：把原本只抓 row[0] 的寫法，改成整列抓取並用空格組合
        # 天氣預報與網頁連結區塊
        for row in weather_block:
            line = " ".join([str(cell) for cell in row if cell])
            if line: # 確保這行有字才加進去
                message_lines.append(line)
        full_message = "\n".join(message_lines)
        
        # 取得專屬的班表 Webhook
        webhook_url = os.environ.get('DISCORD_SCHEDULE_WEBHOOK')
        send_to_discord(webhook_url, full_message)
        
    except Exception as e:
        print(f"❌ 班表處理失敗: {e}")
        raise e

# ==========================================
# 👑 啟動區
# ==========================================
if __name__ == "__main__":
    send_tomorrow_schedule()
