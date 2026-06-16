#!/bin/bash
# PTT Auto Sign Docker Runner Script
#
# 說明：PTT 自動簽到的容器進入點與排程器。
# 設計：不依賴系統 cron，改用單一程序的 sleep loop 自我排程，
#       因此可在 alpine（無 Debian cron）等精簡基底上運行，
#       且所有輸出天然落在 PID1 的 stdout/stderr，`docker logs` 直接可見。
#
# 模式：
#   - 測試模式 (TEST_MODE=true)：每分鐘執行一次，共 3 次後結束容器。
#   - 生產模式 + 每日隨機時間 (RANDOM_DAILY_TIME=true)：每天於 9-17 點的
#     隨機時間執行一次，並在每次排程更新時發送 Telegram 通知。
#   - 生產模式 + 固定時間 (RANDOM_DAILY_TIME=false)：啟動時抽一次隨機時間，
#     之後每天於該固定時間執行。

# 初始化環境變數（使用默認值，若未設置）
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

# 簽到工作時段（臺灣時間），用具名常數取代魔術數字。
readonly WORK_HOUR_START=9        # 最早 9 點
readonly WORK_HOUR_SPAN=9         # 9..17（9 + 0..8）
readonly TEST_RUNS=3             # 測試模式執行次數
readonly TEST_INTERVAL=60        # 測試模式每次間隔（秒）
readonly SECONDS_PER_DAY=86400

# =============================================================================
# 日誌輸出函數
# =============================================================================

# 標準日誌輸出
log_message() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] $1"
}

# 調試日誌輸出（僅在 DEBUG_MODE=true 時顯示）
log_debug() {
    if [ "$DEBUG_MODE" = "true" ]; then
        local timestamp
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        echo "[DEBUG] [${timestamp}] $1"
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

    cd /app || return 1

    # 查找 Python 路徑
    PYTHON_PATH=$(command -v python || command -v python3)
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

# =============================================================================
# 排程器（取代 cron）
# =============================================================================

# 產生隨機執行時間，結果寫入 RANDOM_HOUR / RANDOM_MINUTE。
generate_random_time() {
    RANDOM_MINUTE=$((RANDOM % 60))
    RANDOM_HOUR=$((RANDOM % WORK_HOUR_SPAN + WORK_HOUR_START))  # 9-17 (9 AM to 5 PM)
    log_message "已產生新的隨機執行時間：每天 ${RANDOM_HOUR}:$(printf '%02d' "$RANDOM_MINUTE") (臺灣時間)"
}

# 計算距離下一個 HH:MM 的秒數。
#   $1 = 目標小時, $2 = 目標分鐘, $3 = force_tomorrow(0/1)
# 只用 date +%H/%M/%S（busybox 也支援），避免依賴 GNU date -d 解析。
# Asia/Taipei 無日光節約，因此每日固定 86400 秒。
seconds_until() {
    local target_hour=$1 target_minute=$2 force_tomorrow=${3:-0}
    local now_h now_m now_s now_sod target_sod delay

    now_h=$(date +%H); now_m=$(date +%M); now_s=$(date +%S)
    # 10# 前綴避免 08/09 被當成八進位。
    now_sod=$((10#$now_h * 3600 + 10#$now_m * 60 + 10#$now_s))
    target_sod=$((target_hour * 3600 + target_minute * 60))

    delay=$((target_sod - now_sod))
    # 已過今天的目標時間，或要求排到明天 → 加一天。
    if [ "$force_tomorrow" = "1" ] || [ $delay -le 0 ]; then
        delay=$((delay + SECONDS_PER_DAY))
    fi
    echo "$delay"
}

# 排程更新時透過 Telegram 通知下次簽到時間（沿用既有 TelegramBot 模組）。
notify_schedule_update() {
    local hour=$1 minute=$2

    [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ] || return 0

    export NEW_HOUR="$hour"
    export NEW_MINUTE="$(printf '%02d' "$minute")"
    export NEW_TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

    cd /app && python - <<'PYTHON'
import os
import sys

from pttautosign.utils.config import TelegramConfig
from pttautosign.utils.telegram import TelegramBot

token = os.environ["TELEGRAM_BOT_TOKEN"]
chat_id = os.environ["TELEGRAM_CHAT_ID"]
hour = os.environ.get("NEW_HOUR", "")
minute = os.environ.get("NEW_MINUTE", "")
timestamp = os.environ.get("NEW_TIMESTAMP", "")
date_tag = timestamp.split()[0].replace("-", "") if timestamp else ""

message = (
    "✅ PTT 自動簽到時間已更新\n\n"
    f"📅 下次簽到時間：{hour}:{minute} (臺灣時間)\n"
    f"🕒 更新於：{timestamp}\n"
    f"#ptt #{date_tag}"
)

config = TelegramConfig(token=token, chat_id=chat_id)
bot = TelegramBot(config)
sys.exit(0 if bot.send_message(message) else 1)
PYTHON
    local result=$?
    unset NEW_HOUR NEW_MINUTE NEW_TIMESTAMP

    if [ $result -ne 0 ]; then
        log_message "⚠️ 排程更新通知發送失敗（不影響簽到排程）"
    fi
    return 0
}

# 睡到指定秒數後再執行；秒數為 0 時直接返回。
sleep_seconds() {
    local seconds=$1
    [ "$seconds" -gt 0 ] && sleep "$seconds"
}

# 測試模式：每分鐘執行一次，共 TEST_RUNS 次後結束。
run_test_schedule() {
    log_message "測試模式：每分鐘執行一次，共 ${TEST_RUNS} 次"
    local i=1
    while [ $i -le $TEST_RUNS ]; do
        log_message "測試執行第 ${i} / ${TEST_RUNS} 次"
        run_ptt_login true
        [ $i -lt $TEST_RUNS ] && sleep "$TEST_INTERVAL"
        i=$((i + 1))
    done
    log_message "✅ 已完成 ${TEST_RUNS} 次測試執行，容器即將結束"
}

# 生產模式：固定時間，每天於同一隨機時間執行。
run_fixed_schedule() {
    generate_random_time
    local fixed_hour=$RANDOM_HOUR fixed_minute=$RANDOM_MINUTE
    log_message "生產模式（固定時間）：每天 ${fixed_hour}:$(printf '%02d' "$fixed_minute") 執行（臺灣時間）"

    local first=1 delay
    while true; do
        delay=$(seconds_until "$fixed_hour" "$fixed_minute" "$([ $first -eq 1 ] && echo 0 || echo 1)")
        first=0
        log_message "下次簽到在 ${fixed_hour}:$(printf '%02d' "$fixed_minute")（約 ${delay} 秒後）"
        sleep_seconds "$delay"
        run_ptt_login true
    done
}

# 生產模式：每日隨機時間，每次執行後重新抽時間並通知。
run_random_daily_schedule() {
    log_message "生產模式（每日隨機時間）：容器將持續運行"

    local first=1 delay
    while true; do
        generate_random_time
        notify_schedule_update "$RANDOM_HOUR" "$RANDOM_MINUTE"
        # 首次依今天/明天最近一次排程；之後一律排到隔天，確保每天僅一次。
        delay=$(seconds_until "$RANDOM_HOUR" "$RANDOM_MINUTE" "$([ $first -eq 1 ] && echo 0 || echo 1)")
        first=0
        log_message "下次簽到在 ${RANDOM_HOUR}:$(printf '%02d' "$RANDOM_MINUTE")（約 ${delay} 秒後）"
        sleep_seconds "$delay"
        run_ptt_login true
    done
}

# 排程分派
run_scheduler() {
    if [ "$TEST_MODE" = "true" ]; then
        run_test_schedule
        return 0
    fi

    if [ "$RANDOM_DAILY_TIME" = "true" ]; then
        run_random_daily_schedule
    else
        run_fixed_schedule
    fi
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
    echo "  --run-ptt-login  立即執行一次簽到（供 docker exec 手動觸發）"
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

    # 收到停止訊號時乾淨退出（docker stop 送 SIGTERM 給 PID1）。
    trap 'log_message "收到停止訊號，正在結束容器..."; exit 0' TERM INT

    # 顯示啟動標誌和設定
    log_message "====================================="
    log_message "      PTT 自動簽到 Docker 容器       "
    log_message "====================================="
    log_message "啟動時間: $(date) (${TZ})"
    log_message "運行模式: $([ "$TEST_MODE" = "true" ] && echo "測試模式" || echo "生產模式")"
    log_message "調試模式: $([ "$DEBUG_MODE" = "true" ] && echo "開啟" || echo "關閉")"
    log_message "每日隨機時間: $([ "$RANDOM_DAILY_TIME" = "true" ] && echo "啟用" || echo "停用")"

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

    # 進入排程器（依模式持續運行或在測試完成後結束）
    run_scheduler
}

# 執行主函數，傳遞所有命令行參數
main "$@"
