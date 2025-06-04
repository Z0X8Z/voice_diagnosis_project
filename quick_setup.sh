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
        echo "🔄 正在删除旧环境..."
        # 添加环境停用逻辑，避免删除当前激活的环境
        source $(conda info --base)/etc/profile.d/conda.sh
        conda deactivate
        conda env remove -n voice_diagnosis_env -y
        echo "📦 创建新Python环境..."
        conda create -n voice_diagnosis_env python=3.10 -y
        echo "✅ Python环境创建成功"
    else
        echo "📝 使用现有环境"
        source $(conda info --base)/etc/profile.d/conda.sh
        conda activate voice_diagnosis_env
        cd backend
        # 使用更可靠的安装方法，避免依赖安装失败问题
        echo "🔧 使用优化的依赖安装方案..."
        pip install pyyaml==6.0.1
        pip install -r requirements.txt --no-deps
        pip install exceptiongroup tomli
        echo "✅ 后端依赖安装成功"
        echo "🗄️  配置数据库..."
        python scripts/setup_env.py --auto-mysql
        echo "✅ 数据库配置成功"
        echo "🔄 初始化数据库..."
        python scripts/init_mysql_db.py
        echo "✅ 数据库初始化成功"
        cd ../frontend
        if [ -d "node_modules" ]; then
            echo "⚠️  发现现有node_modules，是否清理重装？(y/N)"
            read -r response
            if [[ "$response" =~ ^[Yy]$ ]]; then
                rm -rf node_modules package-lock.json
            fi
        fi
        npm install
        echo "✅ 前端依赖安装成功"
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
        exit 0
    fi
else
    echo "📦 创建新Python环境..."
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
# 使用更可靠的安装方法，避免依赖安装失败问题
echo "🔧 使用优化的依赖安装方案..."
pip install pyyaml==6.0.1
pip install -r requirements.txt --no-deps
pip install exceptiongroup tomli
echo "✅ 后端依赖安装成功"

# 设置数据库
echo "🗄️  配置数据库..."
python scripts/setup_env.py --auto-mysql
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