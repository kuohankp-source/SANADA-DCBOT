import os
import json
import gspread
import requests
from google.oauth2.service_account import Credentials
from tenacity import retry, stop_after_attempt, wait_exponential

# ==========================================
# 0. 系統登入與驗證 (共用一把鑰匙)
# ==========================================
scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds_json = json.loads(os.environ['GCP_CREDENTIALS'])
creds = Credentials.from_service_account_info(creds_json, scopes=scopes)
client = gspread.authorize(creds)

# ==========================================
# 1. 🏪 總部中控台：三家店鋪的專屬設定與範圍
# ==========================================
STORES = [
    {
        "name": "松竹店",
        "continuous_id": "1Bz-2K7aS74W338Q941-mL28RLURZ5ke6yp8tIv5ju9c", 
        "daily_id": "1nJJ5fqS4rCHdkdVgsYt9x_0GW2bgbeMD-VTZdM1wUDY",      
        "continuous_tab": "松竹真田交接投櫃登錄(連續)",
        "daily_tab": "2-2交接、投櫃登錄",
        "webhook_env": "DISCORD_WEBHOOK_SONGZHU",
        
        "read_range": "N2:O12",          # 讀取 11 行
        "backup_range": "A39:B49",       # 備份貼上的範圍
        "clear_ranges": ['D2', 'C24', 'I2', 'H24', 'N2', 'M24', 'B4:B10', 'G4:G10', 'L4:L10', 'B15:B21', 'G15:G21', 'L15:L21']
    },
    {
        "name": "北屯店",
        "continuous_id": "1c3kBcRWu7_-u6tDMksfTj-CTuCTJ8RQfxh24x3QZfI4",
        "daily_id": "18QVWtmI1JiIfxbCH6LRpGbfQiZtMSSuyWFB0FBtzOTg",
        "continuous_tab": "北屯戴上交接投櫃登錄(連續)",
        "daily_tab": "2-2交接、投櫃登錄",
        "webhook_env": "DISCORD_WEBHOOK_BEITUN",
        
        "read_range": "N2:O12",          # 讀取 11 行
        "backup_range": "A39:B49",       # 備份貼上的範圍
        "clear_ranges": ['D2', 'C24', 'I2', 'H24', 'N2', 'M24', 'B4:B10', 'G4:G10', 'L4:L10', 'B15:B21', 'G15:G21', 'L15:L21']
    },
    {
        "name": "中友店",
        "continuous_id": "1XkLKExA8nP8XBBIkFQYh9f09_5RaEGJqN1UPOK_tED8",
        "daily_id": "1Un-o2cTi7fpyN7uz3juml5XeFvU4zKSp_Qi2urWv6fc",
        "continuous_tab": "中友真田交接投櫃登錄(連續)",
        "daily_tab": "2-2交接、投櫃登錄",
        "webhook_env": "DISCORD_WEBHOOK_ZHONGYOU", # 已對齊 YAML 設定
        
         "read_range": "N2:O12",         # 讀取 11 行
        "backup_range": "A39:B49",       # 備份貼上的範圍
        "clear_ranges": ['D2', 'C24', 'I2', 'H24', 'N2', 'M24', 'B4:B10', 'G4:G10', 'L4:L10', 'B15:B21', 'G15:G21', 'L15:L21']
    }
]

# ==========================================
# 2. Discord 發送專員 (自帶防禦與重試機制)
# ==========================================
@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=60))
def send_to_discord(webhook_url, msg, store_name):
    if not webhook_url:
        print(f"⚠️ 找不到 {store_name} 的 Webhook，請檢查 GitHub Secrets 設定。")
        return
    
    payload = {'content': msg}
    response = requests.post(webhook_url, json=payload)
    response.raise_for_status()
    print(f"✅ {store_name} 交接單 Discord 傳送成功！")

# ==========================================
# 3. 核心處理引擎：讀取 ➔ 發送 ➔ 備份 ➔ 清空
# ==========================================
def process_handover(store):
    print(f"\n🚀 正在啟動【{store['name']}】的每日處理程序...")
    
    try:
        ss_continuous = client.open_by_key(store['continuous_id'])
        ss_daily = client.open_by_key(store['daily_id'])
        
        sheet_continuous = ss_continuous.worksheet(store['continuous_tab'])
        sheet_daily = ss_daily.worksheet(store['daily_tab'])
        
        # --- A. 讀取交接內容與組合訊息 ---
        raw_data = sheet_continuous.get_values(store['read_range'])
        message_lines = []
        for row in raw_data:
            # 使用逗號連接，完美還原 GAS 的顯示格式
            message_lines.append(",".join([str(cell) for cell in row if cell]))
        message = "\n".join(message_lines)
        
        # --- B. 啟動 Discord 傳送專員 ---
        webhook_url = os.environ.get(store['webhook_env'])
        send_to_discord(webhook_url, message, store['name'])
        
        # --- C. 在當日表進行本地備援 ---
        print(f"   ↳ 正在執行 {store['name']} 本地備份...")
        sheet_daily.batch_clear(['A38:C50'])
        sheet_daily.update_acell('A38', '【昨日交接紀錄備份】')
        sheet_daily.update(values=raw_data, range_name=store['backup_range'])
        
        # --- D. 執行當日表的每日清除動作 ---
        print(f"   ↳ 正在重置 {store['name']} 每日表單...")
        sheet_daily.batch_clear(store['clear_ranges'])
        
        print(f"🎉 【{store['name']}】所有任務圓滿完成！")
        
    except Exception as e:
        print(f"🚨 嚴重警告：【{store['name']}】處理失敗，原因：{e}")
        continue # 👈 改成 continue！讓程式跳過這家店的後續動作，直接繼續處理「下一家店」！

# ==========================================
# 👑 啟動區：讓三家店排隊執行
# ==========================================
if __name__ == "__main__":
    for store in STORES:
        process_handover(store)
