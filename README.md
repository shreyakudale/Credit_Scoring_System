# 🤖 AI-Powered Credit Scoring System  
![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-black?logo=flask)
![MySQL](https://img.shields.io/badge/MySQL-Database-orange?logo=mysql)
![LightGBM](https://img.shields.io/badge/LightGBM-ML-green)
![SHAP](https://img.shields.io/badge/SHAP-Explainable%20AI-red)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-purple?logo=bootstrap)
![Chart.js](https://img.shields.io/badge/Chart.js-Visualization-orange?logo=chartdotjs)
![Plotly](https://img.shields.io/badge/Plotly-Graphs-lightgrey?logo=plotly)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

> 🎯 **Intelligent Credit Risk Assessment with Explainable AI**  
A full-stack fintech application that predicts credit scores and default risk using machine learning models with transparency and visualization.

---

## 🚀 Project Overview

The **AI-Powered Credit Scoring System** is a web-based fintech application designed to automate credit score prediction and default risk classification.

It integrates machine learning with full-stack development by combining a Flask backend, MySQL database, and interactive visualization tools.

The system not only predicts credit risk but also explains the decision using SHAP (Explainable AI), making it transparent and suitable for real-world financial analysis.

---

## ✨ Key Features

 🔢 Predict customer credit scores  
 ⚠ Classify default risk (Low / Medium / High)  
 🌳 High-performance LightGBM model  
 🔍 SHAP-based feature contribution explanation  
 🗄 Store predictions in MySQL database  
 📊 Interactive charts and dashboards  
 📜 Historical customer prediction tracking  


## 📊 Functional Capabilities

 Accept customer financial and demographic inputs  
 Perform real-time ML prediction  
 Generate explainability graphs  
 Visualize performance metrics  
 Maintain prediction history  


## 🛠️ Tech Stack

### 👨‍💻 Backend
 🐍 Python 3.x  
 🌶 Flask  

### 🎨 Frontend
 🌐 HTML5  
 🎨 CSS3  
 💎 Bootstrap 5  
 🧩 Jinja2 Templates  

### 🗄 Database
 🐬 MySQL  

### 🤖 Machine Learning
 🌳 LightGBM  
 📚 Scikit-learn  
 🔍 SHAP  

### 📊 Data Processing
 🧮 NumPy  
 🧾 Pandas  

### 📈 Visualization
 📊 Chart.js  
 📉 Plotly  


## 🧠 System Architecture

```text
User (Browser)
        │
        ▼
Frontend (HTML + Bootstrap + Jinja2)
        │  Customer Data Input
        ▼
Flask Backend (Python)
        │
        ├── Data Preprocessing (Pandas / NumPy)
        ├── ML Model (LightGBM)
        ├── Explainability Engine (SHAP)
        └── Store Results (MySQL)
        ▼
Result Dashboard (Credit Score + Risk + SHAP Graphs)
