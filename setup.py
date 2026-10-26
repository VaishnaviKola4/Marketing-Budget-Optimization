from setuptools import setup, find_packages

setup(
    name="marketing-budget-optimizer",
    version="1.0.0",
    description="AI-Driven Marketing Budget Optimization and Inefficient Spend Intelligence Engine",
    author="Marketing Budget Optimizer Engineering Team",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "scipy>=1.10.0",
        "scikit-learn>=1.2.0",
        "pydantic>=2.0.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.22.0",
        "streamlit>=1.25.0",
        "plotly>=5.15.0",
        "python-dateutil>=2.8.0"
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "httpx>=0.24.0"
        ]
    },
    entry_points={
        "console_scripts": [
            "mbo-api=marketing_budget_optimizer.api.app:app",
        ],
    },
)

