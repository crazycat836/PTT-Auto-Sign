#!/bin/bash
# PTT Auto Sign Docker Runner Script
# 
# 說明：PTT 自動簽到的 Docker 環境配置與運行腳本
# 功能：
#   - 測試模式：每分鐘執行一次，共執行 3 次
#   - 生產模式：每天在隨機時間執行一次，可設定為固定或每日變動


# 初始化環境變數（使用默認值，若未設置）
export EXECUTION_COUNT=${EXECUTION_COUNT:-0}
export TEST_MODE=${TEST_MODE:-false}
export DEBUG_MODE=${DEBUG_MODE:-false}
export RANDOM_DAILY_TIME=${RANDOM_DAILY_TIME:-true}  # 控制是否每天使用不同的隨機時間

# 設置時區
export TZ=${TZ:-Asia/Taipei}

# 設置 Python 環境變數
export PYTHONDONTWRITEBYTECODE=1  # 不產生 .pyc 檔案
export PYTHONUNBUFFERED=1         # 立即輸出，不緩衝
export PYTHONIOENCODING=utf-8     # 使用 UTF-8 編碼
export PYTHONWARNINGS=ignore      # 忽略警告
export PYPTT_DISABLE_LOGS=1       # 停用 PyPtt 內部日誌
export FORCE_COLOR=1              # 強制啟用顏色輸出
export PYTHONCOLORIZE=1           # 啟用彩色輸出
export TERM=xterm-256color        # 終端類型

# =============================================================================
# 日誌輸出函數
# =============================================================================

# 標準日誌輸出
log_message() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local message="[${timestamp}] $1"
    echo "$message"
}

# 調試日誌輸出（僅在 DEBUG_MODE=true 時顯示）
log_debug() {
    if [ "$DEBUG_MODE" = "true" ]; then
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        local message="[DEBUG] [${timestamp}] $1"
        echo "$message"
    fi
}

# =============================================================================
# 核心功能函數
# =============================================================================

# 驗證必要的環境變數
check_environment() {
    log_debug "檢查環境變數..."
    local missing_vars=0
    local error_message=""

    # 檢查必要的參數
    [ -z "$PTT_USERNAME" ] && { error_message="$error_message PTT_USERNAME"; missing_vars=$((missing_vars + 1)); }
    [ -z "$PTT_PASSWORD" ] && { error_message="$error_message PTT_PASSWORD"; missing_vars=$((missing_vars + 1)); }
    [ -z "$TELEGRAM_BOT_TOKEN" ] && { error_message="$error_message TELEGRAM_BOT_TOKEN"; missing_vars=$((missing_vars + 1)); }
    [ -z "$TELEGRAM_CHAT_ID" ] && { error_message="$error_message TELEGRAM_CHAT_ID"; missing_vars=$((missing_vars + 1)); }

    if [ $missing_vars -gt 0 ]; then
        log_message "錯誤: 缺少必要的環境變數:$error_message"
        return 1
    fi

    log_debug "環境檢查完成，所有必要的變數都已設置"
    return 0
}

# 執行 PTT 登入和通知
run_ptt_login() {
    local send_notification=${1:-true}
    
    log_debug "開始執行 PTT 登入..."
    
    cd /app
    
    # 查找 Python 路徑
    PYTHON_PATH=$(which python || which python3)
    if [ -z "$PYTHON_PATH" ]; then
        log_message "錯誤: 找不到 Python 可執行檔，無法執行 PTT 登入"
        return 1
    fi
    
    # 設置通知功能
    if [ "$send_notification" = "false" ]; then
        log_debug "已暫時停用通知功能（用於測試）"
        export DISABLE_NOTIFICATIONS=true
    else
        log_debug "已啟用通知功能"
        unset DISABLE_NOTIFICATIONS
    fi
    
    # 執行 PTT 自動簽到程式
    local output
    local status
    
    log_debug "執行命令: $PYTHON_PATH -m pttautosign.main --test-login"
    output=$($PYTHON_PATH -m pttautosign.main --test-login 2>&1)
    status=$?
    
    # 顯示程式輸出
    if [ "$DEBUG_MODE" = "true" ]; then
        log_debug "PTT 程式完整輸出:"
        echo "$output"
    else
        log_message "PTT 程式執行完成，狀態碼: $status"
    fi
    
    # 提取登入統計
    successful_logins=$(echo "$output" | grep -o "登入成功：[0-9]*" | grep -o "[0-9]*" || echo "0")
    failed_logins=$(echo "$output" | grep -o "登入失敗：[0-9]*" | grep -o "[0-9]*" || echo "0")
    total_accounts=$((successful_logins + failed_logins))
    
    # 顯示結果摘要
    log_message "登入測試完成: 總共 $total_accounts 個帳號, 成功 $successful_logins, 失敗 $failed_logins"
    
    # 增加執行計數並顯示
    EXECUTION_COUNT=$((EXECUTION_COUNT + 1))
    log_message "已完成第 $EXECUTION_COUNT 次 PTT 登入任務"
    
    # 測試模式特殊處理：檢查是否達到執行次數上限
    if [ "$TEST_MODE" = "true" ] && [ $EXECUTION_COUNT -ge 3 ]; then
        log_message "✅ 已完成所有 3 次測試模式執行！正在停止 cron 任務..."
        rm -f /etc/cron.d/ptt-auto-sign
        service cron reload >/dev/null 2>&1 || true
        log_message "已成功停止 cron 任務，測試完成"
    fi
    
    # 回傳結果
    if [ $status -eq 0 ]; then
        log_message "PTT 自動簽到任務執行成功"
        return 0
    else
        log_message "PTT 自動簽到任務執行失敗，錯誤碼: $status"
        return $status
    fi
}

# 驗證 PTT 憑證
verify_credentials() {
    log_message "正在驗證 PTT 憑證..."
    
    # 禁用通知 - 只測試登入
    run_ptt_login false
    
    # 獲取結果狀態
    local status=$?
    
    if [ $status -eq 0 ]; then
        log_message "✅ 驗證成功！PTT 登入憑證有效"
        return 0
    else
        log_message "❌ 驗證失敗！請檢查您的 PTT 帳號密碼"
        return 1
    fi
}

# 產生隨機執行時間
generate_random_time() {
    RANDOM_MINUTE=$((RANDOM % 60))
    RANDOM_HOUR=$((RANDOM % 9 + 9))  # 9-17 (9 AM to 5 PM)
    log_message "已產生新的隨機執行時間：每天 $RANDOM_HOUR:$RANDOM_MINUTE (臺灣時間)"
    return 0
}

# 更新 cron 任務時間
update_cron_time() {
    log_debug "更新 cron 任務排程時間..."
    
    # 產生新的隨機時間
    generate_random_time
    
    # 更新 cron 任務設定檔
    cat > /etc/cron.d/ptt-auto-sign << EOL
# PTT Auto Sign production crontab
# 執行時間: $RANDOM_HOUR:$RANDOM_MINUTE (Taiwan time)
$RANDOM_MINUTE $RANDOM_HOUR * * * root /app/scripts/cron_wrapper.sh

# 每天午夜更新執行時間 (如果啟用了隨機每日時間)
0 0 * * * root [ "$RANDOM_DAILY_TIME" = "true" ] && /app/scripts/daily_time_updater.sh

# Empty line required for cron.d files
EOL
    chmod 0644 /etc/cron.d/ptt-auto-sign
    
    # 創建每日更新時間的腳本，使用 telegram.py 發送通知
    cat > /app/scripts/daily_time_updater.sh << EOL
#!/bin/bash
# 每日更新 cron 任務時間的腳本
# 功能：自動產生新的隨機執行時間並發送通知

# 產生新的隨機時間
RANDOM_MINUTE=\$((RANDOM % 60))
RANDOM_HOUR=\$((RANDOM % 9 + 9))  # 9-17 (9 AM to 5 PM)

# 更新 cron 設定檔
sed -i "s/^[0-9]\\+ [0-9]\\+ \\* \\* \\* root \\/app\\/scripts\\/cron_wrapper.sh/\$RANDOM_MINUTE \$RANDOM_HOUR \\* \\* \\* root \\/app\\/scripts\\/cron_wrapper.sh/" /etc/cron.d/ptt-auto-sign

# 重新載入 cron 設定
service cron reload >/dev/null 2>&1 || true

# 記錄變更
TIMESTAMP=\$(date '+%Y-%m-%d %H:%M:%S')
echo "[\$TIMESTAMP] 已更新 PTT 自動簽到時間為 \$RANDOM_HOUR:\$RANDOM_MINUTE (臺灣時間)"

# 使用 Python 調用 telegram.py 發送通知
if [ ! -z "\$TELEGRAM_BOT_TOKEN" ] && [ ! -z "\$TELEGRAM_CHAT_ID" ]; then
    # 建立 Python 腳本
    cat > /tmp/telegram_notify.py << PYTHON
#!/usr/bin/env python3
from pttautosign.utils.telegram import TelegramBot
from pttautosign.utils.config import TelegramConfig
import sys
import datetime

# 時間資訊
hour = "\$RANDOM_HOUR"
minute = "\$RANDOM_MINUTE"
timestamp = "\$TIMESTAMP"

# 產生日期標籤 (如 #20250422 格式)
date_tag = timestamp.split()[0].replace('-', '')

# 準備通知訊息 (使用中文格式)
message = f"✅ PTT 自動簽到時間已更新\\n\\n📅 下次簽到時間：{hour}:{minute} (臺灣時間)\\n🕒 更新於：{timestamp}\\n#ptt #{date_tag}"

# 建立 Telegram 配置
config = TelegramConfig(
    token="\$TELEGRAM_BOT_TOKEN",
    chat_id="\$TELEGRAM_CHAT_ID"
)

# 建立 Telegram 機器人並發送訊息
bot = TelegramBot(config)
success = bot.send_message(message)

# 回報結果
if success:
    print("[\$TIMESTAMP] Telegram 通知已成功發送")
    sys.exit(0)
else:
    print("[\$TIMESTAMP] Telegram 通知發送失敗")
    sys.exit(1)
PYTHON

    # 執行 Python 腳本
    cd /app && PYTHONPATH=/app python /tmp/telegram_notify.py
    RESULT=\$?
    
    # 清理臨時腳本
    rm -f /tmp/telegram_notify.py
    
    # 如果發送失敗，嘗試使用備用方法 (curl)
    if [ \$RESULT -ne 0 ]; then
        echo "[\$TIMESTAMP] 嘗試使用備用方法發送通知..."
        
        # 準備通知訊息 (使用中文格式)
        DATE_TAG=\$(echo \$TIMESTAMP | cut -d' ' -f1 | tr -d '-')
        MESSAGE="✅ PTT 自動簽到時間已更新\\n\\n📅 下次簽到時間：\$RANDOM_HOUR:\$RANDOM_MINUTE (臺灣時間)\\n🕒 更新於：\$TIMESTAMP\\n#ptt #\$DATE_TAG"
        
        # 發送到 Telegram
        curl -s -X POST "https://api.telegram.org/bot\$TELEGRAM_BOT_TOKEN/sendMessage" \
            -d chat_id="\$TELEGRAM_CHAT_ID" \
            -d text="\$MESSAGE" \
            -d parse_mode="HTML" \
            -d disable_notification=false >/dev/null
        
        if [ \$? -eq 0 ]; then
            echo "[\$TIMESTAMP] Telegram 通知已通過備用方法成功發送"
        else
            echo "[\$TIMESTAMP] 所有通知方法均失敗"
        fi
    fi
fi
EOL
    chmod +x /app/scripts/daily_time_updater.sh
    
    log_debug "cron 任務排程時間已成功更新"
    return 0
}

# 設置 cron 任務
setup_cron_job() {
    log_message "正在設置自動執行排程..."
    
    # 檢查是否在 Docker 容器內
    if [ ! -f "/.dockerenv" ] && [ ! -d "/app" ]; then
        log_message "警告: 不在 Docker 容器內，跳過 cron 設置"
        return 0
    fi
    
    # 查找 Python 可執行檔的完整路徑
    PYTHON_PATH=$(which python)
    if [ -z "$PYTHON_PATH" ]; then
        PYTHON_PATH=$(which python3)
    fi
    
    if [ -z "$PYTHON_PATH" ]; then
        log_message "錯誤: 找不到 Python 可執行檔，無法設置 cron 任務"
        return 1
    fi
    
    log_debug "Python 路徑: $PYTHON_PATH"
    
    # 創建 cron 的 wrapper 腳本來管理執行計數
    cat > /app/scripts/cron_wrapper.sh << EOL
#!/bin/bash
# cron 任務包裝腳本
# 功能：管理執行次數，傳遞環境變數，記錄執行時間

# 讀取當前執行計數或初始化為0
EXECUTION_COUNT=\${EXECUTION_COUNT:-0}

# 執行主腳本
cd /app && echo "=== Cron 任務開始執行於 \$(date) ==="
PYTHONPATH=/app TEST_MODE=$TEST_MODE DEBUG_MODE=$DEBUG_MODE PTT_USERNAME=$PTT_USERNAME PTT_PASSWORD=$PTT_PASSWORD TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID EXECUTION_COUNT=\$EXECUTION_COUNT PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin /app/scripts/docker_runner.sh --run-ptt-login
RESULT=\$?

# 增加執行計數
EXECUTION_COUNT=\$((EXECUTION_COUNT + 1))

# 寫入更新後的執行計數到下一次的 cron 環境
if [ "$TEST_MODE" = "true" ] && [ \$EXECUTION_COUNT -lt 3 ]; then
    # 更新 cron 環境變數
    sed -i "s/EXECUTION_COUNT=[0-9]*/EXECUTION_COUNT=\$EXECUTION_COUNT/" /etc/cron.d/ptt-auto-sign
fi

echo "=== Cron 任務執行完成於 \$(date) ==="
exit \$RESULT
EOL
    chmod +x /app/scripts/cron_wrapper.sh
    
    if [ "$TEST_MODE" = "true" ]; then
        # 測試模式：每分鐘執行一次，共3次
        log_message "設置測試模式排程：每分鐘執行一次，共3次"
        
        # 創建 crontab 文件
        cat > /etc/cron.d/ptt-auto-sign << EOL
# PTT 自動簽到測試模式 (每分鐘執行一次，共3次)
* * * * * root EXECUTION_COUNT=$EXECUTION_COUNT /app/scripts/cron_wrapper.sh

# 空行是必須的
EOL
        chmod 0644 /etc/cron.d/ptt-auto-sign
        
        log_message "測試模式排程已設置完成"
    else
        # 生產模式：每天隨機時間執行，並根據設定決定是否每天更新時間
        if [ "$RANDOM_DAILY_TIME" = "true" ]; then
            log_message "設置生產模式排程 (每天隨機時間，自動更新)"
            update_cron_time
        else
            # 固定隨機時間模式
            RANDOM_MINUTE=$((RANDOM % 60))
            RANDOM_HOUR=$((RANDOM % 9 + 9))  # 9-17 (9 AM to 5 PM)
            
            log_message "設置生產模式排程：固定在每天 $RANDOM_HOUR:$RANDOM_MINUTE 執行（臺灣時間）"
            
            # 創建 crontab 文件
            cat > /etc/cron.d/ptt-auto-sign << EOL
# PTT 自動簽到生產模式 (每天固定時間執行)
# 執行時間: $RANDOM_HOUR:$RANDOM_MINUTE (Taiwan time)
$RANDOM_MINUTE $RANDOM_HOUR * * * root /app/scripts/cron_wrapper.sh

# 空行是必須的
EOL
            chmod 0644 /etc/cron.d/ptt-auto-sign
            
            log_message "生產模式排程已設置完成，執行時間固定"
        fi
    fi
    
    # 啟動 cron 服務
    log_debug "重新啟動 cron 服務..."
    service cron restart >/dev/null 2>&1 || true
    
    # 檢查 cron 服務狀態
    if service cron status >/dev/null 2>&1; then
        log_message "✅ cron 服務已成功啟動"
        return 0
    else
        log_message "❌ cron 服務啟動失敗"
        return 1
    fi
}

# 監控容器運行
monitor_container() {
    log_message "容器已成功啟動並進入監控模式"
    
    # 顯示運行模式資訊
    if [ "$TEST_MODE" = "true" ]; then
        log_message "測試模式：容器將使用 cron 執行 3 次測試後自動停止"
    else
        if [ "$RANDOM_DAILY_TIME" = "true" ]; then
            log_message "生產模式：容器將持續運行，每天使用不同的隨機時間執行簽到"
        else
            log_message "生產模式：容器將持續運行，每天固定時間執行簽到"
        fi
    fi
    
    # 環境檢查
    if [ ! -f "/.dockerenv" ] && [ ! -d "/app" ]; then
        log_message "不在 Docker 容器內，即將退出"
        return 0
    fi
    
    # 保持容器運行
    log_message "容器監控已啟動，按 Ctrl+C 可停止容器"
    while true; do
        sleep 60
    done
}

# =============================================================================
# 輔助函數
# =============================================================================

# 顯示用法說明
show_usage() {
    echo "PTT 自動簽到 Docker 運行腳本"
    echo ""
    echo "用法: $0 [選項]"
    echo ""
    echo "選項:"
    echo "  -h, --help       顯示此幫助信息"
    echo ""
    echo "環境變數:"
    echo "  PTT_USERNAME       PTT 帳號"
    echo "  PTT_PASSWORD       PTT 密碼"
    echo "  TELEGRAM_BOT_TOKEN Telegram 機器人 Token"
    echo "  TELEGRAM_CHAT_ID   Telegram 聊天 ID"
    echo "  TEST_MODE          測試模式 (true/false)"
    echo "  DEBUG_MODE         調試模式 (true/false)"
    echo "  RANDOM_DAILY_TIME  每天使用隨機時間 (true/false)"
    echo ""
}

# 處理命令行參數
process_args() {
    # 顯示環境配置（調試模式）
    if [ "$DEBUG_MODE" = "true" ]; then
        log_debug "環境配置詳情:"
        log_debug "- TEST_MODE=$TEST_MODE"
        log_debug "- DEBUG_MODE=$DEBUG_MODE"
        log_debug "- RANDOM_DAILY_TIME=$RANDOM_DAILY_TIME"
    fi
    
    # 處理輸入參數
    while [[ $# -gt 0 ]]; do
        case $1 in
            --run-ptt-login)
                log_debug "正在執行 PTT 登入操作 (TEST_MODE=${TEST_MODE})"
                run_ptt_login true
                exit $?
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                # 略過未知選項
                shift
                ;;
        esac
    done
}

# =============================================================================
# 主程序
# =============================================================================

main() {
    # 處理命令行參數
    process_args "$@"
    
    # 顯示啟動標誌和設定
    log_message "====================================="
    log_message "      PTT 自動簽到 Docker 容器       "
    log_message "====================================="
    log_message "啟動時間: $(date) (${TZ})"
    log_message "運行模式: $([ "$TEST_MODE" = "true" ] && echo "測試模式" || echo "生產模式")"
    log_message "調試模式: $([ "$DEBUG_MODE" = "true" ] && echo "開啟" || echo "關閉")"
    log_message "每日隨機時間: $([ "$RANDOM_DAILY_TIME" = "true" ] && echo "啟用" || echo "停用")"
    
    # 記錄環境變數詳情（調試模式）
    log_debug "環境變數詳細設置:"
    log_debug "- TEST_MODE=$TEST_MODE"
    log_debug "- DEBUG_MODE=$DEBUG_MODE"
    log_debug "- RANDOM_DAILY_TIME=$RANDOM_DAILY_TIME"
    
    # 檢查環境變數
    if ! check_environment; then
        log_message "環境檢查失敗，程式即將退出"
        exit 1
    fi
    
    # 驗證 PTT 憑證
    log_message "正在驗證 PTT 登入憑證..."
    if ! verify_credentials; then
        log_message "憑證驗證失敗，程式即將退出"
        exit 1
    fi
    
    # 設置 cron 任務
    if ! setup_cron_job; then
        log_message "cron 任務設置失敗，程式即將退出"
        exit 1
    fi
    
    # 監控容器
    monitor_container
}

# 執行主函數，傳遞所有命令行參數
main "$@" 