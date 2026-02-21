# AI-Powered Credit Scoring System

## Project Overview
This project implements an AI-powered credit scoring system using Flask web interface and MySQL database. It predicts credit scores and default risk using machine learning models, with explainability features.

## Tech Stack
- **Frontend**: HTML5, CSS3, Bootstrap 5, Jinja2 Templates
- **Backend**: Flask (Python 3.x)
- **Database**: MySQL
- **AI/ML**: LightGBM, Scikit-learn, SHAP
- **Data Processing**: Pandas, NumPy
- **Visualization**: Chart.js, Plotly

## Setup Instructions
1. Install dependencies: `pip install -r requirements.txt`
2. Set up MySQL database and run `database/schema.sql`
3. Configure database connection in `config/db_config.py`
4. Train the model using `model/train_model.py`
5. Run the application: `python app.py`

## Usage
- Access the web interface to input customer data and get credit scores.
- View prediction explanations and historical data.
