@echo off
chcp 65001 >nul

REM 声肺康智能分析系统 - Windows快速部署脚本

echo 🎯 声肺康智能分析系统 - 快速部署脚本 (Windows版本)
echo ===============================================

REM 检查conda是否安装
where conda >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 未检测到conda，请先安装Anaconda或Miniconda
    echo 📥 下载地址: https://www.anaconda.com/products/distribution
    pause
    exit /b 1
)

echo ✅ 检测到conda
conda --version

REM 检查Node.js是否安装
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 未检测到Node.js，请先安装Node.js
    echo 📥 下载地址: https://nodejs.org/
    pause
    exit /b 1
)

echo ✅ 检测到Node.js
node --version
npm --version

REM 创建conda环境
echo 🐍 创建Python环境...
conda env list | findstr "voice_diagnosis_env" >nul
if %errorlevel% equ 0 (
    echo ⚠️  环境voice_diagnosis_env已存在，是否删除重建？[y/N]
    set /p response=
    if /i "%response%"=="y" (
        echo 🔄 正在删除旧环境...
        conda env remove -n voice_diagnosis_env -y
        echo 📦 创建新Python环境...
        conda create -n voice_diagnosis_env python=3.10 -y
        echo ✅ Python环境创建成功
    ) else (
        echo 📝 使用现有环境
    )
) else (
    echo 📦 创建新Python环境...
    conda create -n voice_diagnosis_env python=3.10 -y
    echo ✅ Python环境创建成功
)

REM 激活环境
echo 🔧 激活Python环境...
call conda activate voice_diagnosis_env

REM 安装后端依赖
echo 📦 安装后端依赖...
cd backend
REM 使用更可靠的安装方法，避免依赖安装失败问题
echo 🔧 使用优化的依赖安装方案...
pip install pyyaml==6.0.1
pip install -r requirements.txt --no-deps
pip install exceptiongroup tomli
if %errorlevel% neq 0 (
    echo ❌ 后端依赖安装失败
    pause
    exit /b 1
)
echo ✅ 后端依赖安装成功

REM 设置数据库
echo 🗄️  配置数据库...
python scripts/setup_env.py --auto-mysql
echo ✅ 数据库配置成功

REM 初始化数据库
echo 🔄 初始化数据库...
python scripts/init_mysql_db.py
echo ✅ 数据库初始化成功

REM 安装前端依赖
echo 🌐 安装前端依赖...
cd ..\frontend

REM 检查是否存在node_modules
if exist "node_modules" (
    echo ⚠️  发现现有node_modules，是否清理重装？[y/N]
    set /p response=
    if /i "%response%"=="y" (
        rmdir /s /q node_modules
        if exist "package-lock.json" del package-lock.json
    )
)

npm install
if %errorlevel% neq 0 (
    echo ❌ 前端依赖安装失败
    pause
    exit /b 1
)
echo ✅ 前端依赖安装成功

REM 返回项目根目录
cd ..

echo.
echo 🎉 部署完成！
echo ===============
echo.
echo 💡 启动方法：
echo.
echo 1️⃣  启动后端服务（在第一个命令提示符窗口）：
echo    conda activate voice_diagnosis_env
echo    cd %cd%\backend
echo    python main.py
echo.
echo 2️⃣  启动前端服务（在第二个命令提示符窗口）：
echo    cd %cd%\frontend
echo    npm run dev
echo.
echo 3️⃣  访问系统：
echo    前端地址: http://localhost:5173
echo    后端API: http://127.0.0.1:8000/docs
echo.
echo 📚 详细文档: %cd%\docs
echo.
echo 🆘 如遇问题，请查看部署指南或提交GitHub Issue
echo.
pause 