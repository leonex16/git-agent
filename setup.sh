#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🤖 Setting up git-agent environment...${NC}"

# 1. Check/Install uv
echo -e "\n${BLUE}[1/4] Checking 'uv' package manager...${NC}"
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}📦 'uv' not found. Installing...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Attempt to source env for current session
    if [ -f "$HOME/.local/bin/env" ]; then
        source "$HOME/.local/bin/env"
    elif [ -f "$HOME/.cargo/env" ]; then
        source "$HOME/.cargo/env"
    fi
else
    echo -e "${GREEN}✅ uv is already installed${NC}"
fi

# 2. Check/Install Ollama
echo -e "\n${BLUE}[2/4] Checking Ollama...${NC}"
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}🦙 Ollama not found. Installing...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install ollama
        else
            echo -e "${RED}❌ Homebrew not found. Please install Ollama manually from https://ollama.com${NC}"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl -fsSL https://ollama.com/install.sh | sh
    else
        echo -e "${RED}❌ Unsupported OS. Please install Ollama manually.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Ollama is already installed${NC}"
fi

# 3. Ensure Ollama is running and pull models
echo -e "\n${BLUE}[3/4] Checking Ollama Service & Models...${NC}"
if ! pgrep -x "ollama" > /dev/null && ! pgrep -f "ollama serve" > /dev/null; then
    echo -e "${YELLOW}🔄 Starting Ollama background service...${NC}"
    ollama serve > /dev/null 2>&1 &
    sleep 5 
fi

MODELS=("qwen2.5-coder:7b" "mistral-nemo:12b" "qwen3:8b")
for model in "${MODELS[@]}"; do
    echo -e "   ⬇️  Pulling model: ${YELLOW}${model}${NC}..."
    ollama pull "$model"
done
