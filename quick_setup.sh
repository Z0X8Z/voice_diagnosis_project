#!/bin/bash

# 声肺康智能分析系统 - 快速部署脚本
# 适用于macOS和Linux系统

set -e  # 遇到错误时停止执行

echo "🎯 声肺康智能分析系统 - 快速部署脚本"
echo "======================================="

# 检查操作系统
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo "📱 检测到操作系统: $MACHINE"

# 检查是否安装了conda
if ! command -v conda &> /dev/null; then
    echo "❌ 未检测到conda，请先安装Anaconda或Miniconda"
    echo "📥 下载地址: https://www.anaconda.com/products/distribution"
    exit 1
fi

echo "✅ 检测到conda: $(conda --version)"

# 检查是否安装了node和npm
if ! command -v node &> /dev/null; then
    echo "❌ 未检测到Node.js，请先安装Node.js"
    echo "📥 下载地址: https://nodejs.org/"
    exit 1
fi

echo "✅ 检测到Node.js: $(node --version)"
echo "✅ 检测到npm: $(npm --version)"

# 创建conda环境
echo "🐍 创建Python环境..."
if conda env list | grep -q "voice_diagnosis_env"; then
    echo "⚠️  环境voice_diagnosis_env已存在，是否删除重建？(y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        conda env remove -n voice_diagnosis_env -y
    else
        echo "📝 使用现有环境"
    fi
fi

if ! conda env list | grep -q "voice_diagnosis_env"; then
    conda create -n voice_diagnosis_env python=3.10 -y
    echo "✅ Python环境创建成功"
fi

# 激活环境
echo "🔧 激活Python环境..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate voice_diagnosis_env

# 安装后端依赖
echo "📦 安装后端依赖..."
cd backend
pip install -r requirements.txt
echo "✅ 后端依赖安装成功"

# 设置数据库
echo "🗄️  配置数据库..."
python scripts/setup_env.py --auto-sqlite
echo "✅ 数据库配置成功"

# 初始化数据库
echo "🔄 初始化数据库..."
python scripts/init_mysql_db.py
echo "✅ 数据库初始化成功"

# 安装前端依赖
echo "🌐 安装前端依赖..."
cd ../frontend

# 检查是否存在node_modules
if [ -d "node_modules" ]; then
    echo "⚠️  发现现有node_modules，是否清理重装？(y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        rm -rf node_modules package-lock.json
    fi
fi

npm install
echo "✅ 前端依赖安装成功"

# 创建前端环境配置
echo "⚙️  配置前端环境..."
echo "VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1" > .env
echo "✅ 前端环境配置成功"

# 返回项目根目录
cd ..

echo ""
echo "🎉 部署完成！"
echo "==============="
echo ""
echo "💡 启动方法："
echo ""
echo "1️⃣  启动后端服务（在第一个终端窗口）："
echo "   conda activate voice_diagnosis_env"
echo "   cd $(pwd)/backend"
echo "   python main.py"
echo ""
echo "2️⃣  启动前端服务（在第二个终端窗口）："
echo "   cd $(pwd)/frontend"
echo "   npm run dev"
echo ""
echo "3️⃣  访问系统："
echo "   前端地址: http://localhost:5173"
echo "   后端API: http://127.0.0.1:8000/docs"
echo ""
echo "📚 详细文档: $(pwd)/DEPLOYMENT_GUIDE.md"
echo ""
echo "🆘 如遇问题，请查看部署指南或提交GitHub Issue"
echo "" 