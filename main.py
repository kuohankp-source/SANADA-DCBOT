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
        
        # 🎯 松竹店專屬範圍設定
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
        
        # 🎯 北屯店專屬範圍設定 (配合你原本的程式，只讀 11 行)
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
        "webhook_env": "DISCORD_WEBHOOK_SANADA",
        
        # 🎯 中友店專屬範圍設定 (配合你原本的程式，只讀 11行)
         "read_range": "N2:O12",          # 讀取 11 行
        "backup_range": "A39:B49",       # 備份貼上的範圍
        "clear_ranges": ['D2', 'C24', 'I2', 'H24', 'N2', 'M24', 'B4:B10', 'G4:G10', 'L4:L10', 'B15:B21', 'G15:G21', 'L15:L21']
    },
]
