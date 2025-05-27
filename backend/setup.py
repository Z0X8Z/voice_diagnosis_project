from setuptools import setup, find_packages

setup(
    name="voice-analysis-backend",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "pymysql",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
        "python-multipart",
        "pydantic",
    ],
    python_requires=">=3.8",
) 