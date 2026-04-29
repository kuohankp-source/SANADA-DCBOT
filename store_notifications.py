import os
import json
import gspread
import requests
from google.oauth2.service_account import Credentials
from tenacity import retry, stop_after_attempt, wait_exponential

# ==========================================
# 0. 系統登入與驗證
# ==========================================
scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds_json = json.loads(os.environ['GCP_CREDENTIALS'])
creds = Credentials.from_service_account_info(creds_json, scopes=scopes)
client = gspread.authorize(creds)

# ==========================================
# 1. 🏪 總部中控台：三家店鋪的表單設定
# ==========================================
STORES = [
    {
        "name": "北屯店",
        "webhook_env": "DISCORD_WEBHOOK_BEITUN",
        "task_b": { # 客訂單資訊 (已根據新截圖填入正確ID與多重範圍)
            "sheet_id": "1t1LCxJAB4BcRZTTwP2NAfcSRneZnCGjaaemntl9LlYo",
            "tab_name": "待聯絡待取貨清單",
            "ranges": ["G1:G20", "J1:J4"] # 👈 支援多個不連續範圍自動往下接
        },
        "task_c": { # 詢問單狀態 (已根據新截圖填入正確ID與範圍)
            "sheet_id": "1d18sp0XxTYKOuD8jigcjfnBW72H6wON-Cgrh4F219Ss",
            "tab_name": "維修單/詢問單分類",
            "ranges": ["F1:F20"]
        }
    },
    {
        "name": "中友店",
        "webhook_env": "DISCORD_WEBHOOK_ZHONGYOU",
        "task_b": { 
            "sheet_id": "18jJjQd0H_jE1V7cIoWYexpHF3lCwXS3q5lclrKWBKUc", # 👈 請填入
            "tab_name": "待聯絡待取貨清單",
            "ranges": ["G1:G20", "J1:J4"] # 假設三店排版相同
        },
        "task_c": { 
            "sheet_id": "1ZmrfnDfGq3Oe7-P4RaXxKXSRjHg7UH0PVVYICFD1xWE", # 👈 請填入
            "tab_name": "維修單/詢問單分類",
            "ranges": ["F1:F20"]
        }
    },
    {
        "name": "松竹店",
        "webhook_env": "DISCORD_WEBHOOK_SONGZHU",
        "task_b": { 
            "sheet_id": "1rOD8yHz1fFSYxloPU5e0xN8aPd3bTcQZOvnTGe9JcBQ", # 👈 請填入
            "tab_name": "待聯絡待取貨清單",
            "ranges": ["G1:G20", "J1:J4"] # 假設三店排版相同
        },
        "task_c": { 
            "sheet_id": "16mGAGKU3YCo5YpYGWyzLNinNUSanBqEm0ygXyRKdnTU", # 👈 請填入
            "tab_name": "維修單/詢問單分類",
            "ranges": ["F1:F20"]
        }
    }
]

# ==========================================
# 2. Discord 發送專員 (自帶防禦與重試機制)
# ==========================================
@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=60))
def send_to_discord(webhook_url, msg, store_name, task_name):
    if not webhook_url:
        print(f"⚠️ 找不到 {store_name} 的 Webhook。")
        return
    if not msg.strip():
        print(f"⚠️ {store_name} 的 {task_name} 沒有內容，略過發送。")
        return
        
    payload = {'content': msg}
    response = requests.post(webhook_url, json=payload)
    response.raise_for_status()
    print(f"✅ {store_name} [{task_name}] 傳送成功！")

# ==========================================
# 3. 核心處理引擎：支援多範圍抓取與換行排版
# ==========================================
def fetch_and_format(sheet_id, tab_name, range_list):
    try:
        sheet = client.open_by_key(sheet_id).worksheet(tab_name)
        message_lines = []
        
        # 依序讀取清單中的每一個範圍 (例如先讀 G1:G20，再讀 J1:J4)
        for r in range_list:
            raw_data = sheet.get_values(r)
            for row in raw_data:
                # 將儲存格內容轉為文字，若為空則保留空行以對齊 GAS 格式
                line_text = " ".join([str(cell).strip() for cell in row])
                message_lines.append(line_text)
                
        return "\n".join(message_lines)
    except Exception as e:
        print(f"❌ 讀取表單失敗 ({tab_name}): {e}")
        return ""

def process_store_notifications():
    for store in STORES:
        print(f"\n🚀 正在處理【{store['name']}】的通知任務...")
        webhook_url = os.environ.get(store['webhook_env'])
        
        # --- 處理 Task B: 客訂單資訊 ---
        msg_b = fetch_and_format(store['task_b']['sheet_id'], store['task_b']['tab_name'], store['task_b']['ranges'])
        send_to_discord(webhook_url, msg_b, store['name'], "客訂單資訊")
        
        # --- 處理 Task C: 詢問單狀態 ---
        msg_c = fetch_and_format(store['task_c']['sheet_id'], store['task_c']['tab_name'], store['task_c']['ranges'])
        send_to_discord(webhook_url, msg_c, store['name'], "詢問單狀態")

if __name__ == "__main__":
    process_store_notifications()
