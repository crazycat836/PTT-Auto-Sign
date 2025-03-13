#!/bin/bash

# 設置顏色輸出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 設置 Python 環境變數以防止 __pycache__ 創建
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1

# 定義數據目錄
CRON_DATA_DIR=/app/data

# 檢查系統架構的函數
check_architecture() {
    local arch=$(uname -m)
    local os=$(uname -s)
    
    echo -e "${GREEN}系統資訊:${NC}"
    echo "作業系統: $os"
    echo "架構: $arch"
    
    case "$arch" in
        "x86_64")
            echo "運行於 AMD64/x86_64 架構"
            ;;
        "arm64" | "aarch64")
            echo "運行於 ARM64 架構"
            ;;
        *)
            echo -e "${YELLOW}警告: 運行於不支援的架構: $arch${NC}"
            ;;
    esac
    echo "-------------------"
}

# 建置並推送 Docker 映像檔的函數
build_and_push_docker() {
    echo -e "${YELLOW}正在建置並推送 Docker 映像檔...${NC}"
    echo "這將為 AMD64 和 ARM64 架構建置映像檔"
    
    # 檢查是否安裝了 Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}錯誤: 未安裝 Docker${NC}"
        exit 1
    fi
    
    # 建置並推送多架構映像檔
    if docker buildx build --platform linux/amd64,linux/arm64 -t crazycat836/pttautosign:latest -f docker/Dockerfile --push .; then
        echo -e "${GREEN}成功建置並推送 Docker 映像檔${NC}"
        echo "映像檔: crazycat836/pttautosign:latest"
    else
        echo -e "${RED}錯誤: 建置並推送 Docker 映像檔失敗${NC}"
        exit 1
    fi
}

# 運行 Python 測試的函數 (快速版)
run_python_test() {
    echo -e "${YELLOW}正在本地運行 PTT 自動簽到...${NC}"
    
    # 檢查是否安裝了 Poetry
    if ! command -v poetry &> /dev/null; then
        echo -e "${RED}未安裝 Poetry。請先安裝它。${NC}"
        echo "您可以使用以下命令安裝:"
        echo "curl -sSL https://install.python-poetry.org | python3 -"
        exit 1
    fi

    # 檢查 .env 文件是否存在
    if [ ! -f .env ]; then
        echo -e "${RED}找不到 .env 文件。請先創建它。${NC}"
        echo "您可以從 .env.example 複製:"
        echo "cp .env.example .env"
        exit 1
    fi

    # 安裝依賴
    echo -e "\n${GREEN}正在安裝依賴...${NC}"
    poetry install

    # 運行腳本
    echo -e "\n${GREEN}正在執行 PTT 自動簽到...${NC}"
    poetry run python -B pttautosign.py
    
    # 檢查運行結果
    if [ $? -eq 0 ]; then
        echo -e "\n${GREEN}執行成功!${NC}"
    else
        echo -e "\n${RED}執行失敗!${NC}"
        exit 1
    fi
}

# 運行本地 Docker 測試的函數
run_local_test() {
    echo -e "${YELLOW}====================================${NC}"
    echo -e "${YELLOW}    PTT 自動簽到 Docker 測試       ${NC}"
    echo -e "${YELLOW}====================================${NC}"

    # 檢查 Docker 是否安裝
    echo -e "\n${GREEN}檢查 Docker 環境...${NC}"
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}錯誤: Docker 未安裝${NC}"
        echo "請先安裝 Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    echo "Docker 已安裝"
    
    # 檢查 .env 文件是否存在
    if [ ! -f .env ]; then
        echo -e "${RED}錯誤: .env 文件不存在${NC}"
        echo "請從 .env.example 複製並修改:"
        echo "cp .env.example .env"
        exit 1
    fi
    echo ".env 文件已存在"

    # 檢查 Dockerfile 是否存在
    if [ ! -f docker/Dockerfile ]; then
        echo -e "${RED}錯誤: Dockerfile 不存在於 docker/ 目錄${NC}"
        exit 1
    fi
    echo "Dockerfile 已存在"

    # 建置本地 Docker 映像檔
    echo -e "\n${GREEN}正在建置本地 Docker 映像檔...${NC}"
    if docker build -t pttautosign:local -f docker/Dockerfile .; then
        echo -e "${GREEN}Docker 映像檔建置成功!${NC}"
    else
        echo -e "${RED}Docker 映像檔建置失敗!${NC}"
        exit 1
    fi

    # 檢查是否有舊的容器
    CONTAINER_ID=$(docker ps -a --filter "name=pttautosign-test" -q)
    if [ ! -z "$CONTAINER_ID" ]; then
        echo -e "\n${YELLOW}發現舊的測試容器，正在移除...${NC}"
        docker rm -f $CONTAINER_ID
    fi

    # 運行 Docker 容器
    echo -e "\n${GREEN}正在運行 Docker 容器...${NC}"
    docker run --name pttautosign-test -d \
        --env-file .env \
        -e PYTHONWARNINGS="ignore::SyntaxWarning" \
        -e LOG_LEVEL="INFO" \
        pttautosign:local
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}容器已成功啟動!${NC}"
        echo -e "\n${YELLOW}容器日誌:${NC}"
        sleep 2  # 等待容器啟動
        docker logs pttautosign-test
        
        echo -e "\n${GREEN}測試完成! 容器正在後台運行。${NC}"
        echo -e "您可以使用以下命令查看容器日誌:"
        echo -e "  docker logs pttautosign-test"
        echo -e "您可以使用以下命令停止並移除容器:"
        echo -e "  docker rm -f pttautosign-test"
    else
        echo -e "${RED}容器啟動失敗!${NC}"
        exit 1
    fi
}

# 檢查是否在 Docker 中運行
if [ -f /.dockerenv ]; then
    # 在 Docker 中運行
    echo -e "${YELLOW}=====================================${NC}"
    echo -e "${YELLOW}   在 Docker 中運行 PTT 自動簽到    ${NC}"
    echo -e "${YELLOW}=====================================${NC}"
    
    # 記錄執行時間
    echo "執行時間: $(date)" >> "$CRON_DATA_DIR/execution.log"
    echo -e "${GREEN}執行時間: $(date)${NC}"
    
    # 更新健康檢查文件
    touch "$CRON_DATA_DIR/healthcheck"
    
    # 運行腳本
    echo -e "${GREEN}正在執行 PTT 自動簽到任務...${NC}"
    cd /app && python3 -B pttautosign.py
    
    # 記錄完成情況
    if [ $? -eq 0 ]; then
        echo "任務在 $(date) 成功完成" >> "$CRON_DATA_DIR/execution.log"
        echo -e "${GREEN}任務成功完成${NC}"
    else
        echo "任務在 $(date) 失敗" >> "$CRON_DATA_DIR/execution.log"
        echo -e "${RED}任務失敗${NC}"
    fi
    
    echo "Container will now stay running to allow scheduled tasks to execute..."
else
    # 在本地運行
    echo -e "${YELLOW}====================================${NC}"
    echo -e "${YELLOW}      PTT 自動簽到管理工具        ${NC}"
    echo -e "${YELLOW}====================================${NC}"
    
    # 顯示系統架構信息
    check_architecture
    
    # 顯示選單
    echo -e "${GREEN}請選擇一個選項:${NC}"
    echo "1) 本地執行 - 在本地環境執行簽到程式"
    echo "2) Docker 測試 - 建置並測試 Docker 容器"
    echo "3) 發布 Docker - 建置並發布多架構 Docker 映像檔"
    echo "4) 退出程式"
    
    # 讀取用戶輸入
    read -p "請輸入選項 (1-4): " choice
    
    # 處理用戶選擇
    case $choice in
        1)
            run_python_test
            ;;
        2)
            run_local_test
            ;;
        3)
            build_and_push_docker
            ;;
        4)
            echo -e "${YELLOW}正在退出...${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}無效選項${NC}"
            exit 1
            ;;
    esac
fi 