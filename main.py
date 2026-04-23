import os
import json
import gspread
import requests
from google.oauth2.service_account import Credentials
from tenacity import retry, stop_after_attempt, wait_exponential

# --- 系統設定區 ---
# 請將這裡替換成你中友店試算表的實際 ID (網址 /d/ 和 /edit 中間那一串)
SHEET_ID = '1XkLKExA8nP8XBBIkFQYh9f09_5RaEGJqN1UPOK_tED8' 
SHEET_NAME = '中友真田交接投櫃登錄(連續)'

# --- 1. 驗證並連線 Google 試算表 ---
scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds_json = json.loads(os.environ['GCP_CREDENTIALS'])
creds = Credentials.from_service_account_info(creds_json, scopes=scopes)
client = gspread.authorize(creds)

# --- 2. 讀取試算表資料 ---
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# Python 的 gspread 可以一次抓取整塊區域，不需一行一行寫
# get_values 返回二維陣列: [['值N2', '值O2'], ['值N3', '值O3']...]
data_range = sheet.get_values('N2:O12')

# 將陣列組合成字串，每列用逗號或空格隔開，每行用換行符號隔開
message_lines = []
for row in data_range:
    # 過濾掉空白儲存格並組合成單行文字
    line = " ".join([str(cell) for cell in row if cell])
    message_lines.append(line)

message = "\n".join(message_lines)

# --- 3. 發送到 Discord 邏輯 (內建強大重試機制) ---
WEBHOOK_URL = os.environ['DISCORD_WEBHOOK']

# @retry 裝飾器：遇到錯誤時自動重試，最多 5 次。
# wait_exponential：每次重試的等待時間會自動拉長 (例如 4秒, 8秒, 16秒...)，完美破解 429 流量限制
@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=60))
def send_to_discord(msg):
    payload = {'content': msg}
    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
    
    # 如果 HTTP 狀態碼不是 200 或 204，主動拋出錯誤以觸發 retry 機制
    response.raise_for_status() 
    print("✅ 交接單傳送成功！")

if __name__ == "__main__":
    try:
        send_to_discord(message)
    except Exception as e:
        print(f"🚨 達到最大重試次數，傳送徹底失敗: {e}")
        # 故意引發錯誤，讓 GitHub Actions 知道任務失敗
        # GitHub 預設會在任務失敗時，發送 Email 通知給 Repository 擁有者 (你)！
        # 所以不需要像 GAS 那樣另外寫 MailApp.sendEmail。
        raise e
