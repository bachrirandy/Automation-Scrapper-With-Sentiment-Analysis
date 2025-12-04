# 📰 Automation-Scrapper-With-Sentiment-Analysis

**Web App for Automated News Data Scraping with Sentiment Analysis**

This application enables **automated online news article scraping**, text preprocessing, **sentiment analysis** (positive / neutral / negative), and storing results into a database supporting real-time public perception evaluation or data-driven case studies.

---

## 🚀 Key Features

* **Automated Scraping:** Retrieves news articles from online sources (Web Scraping).
* **Text Preprocessing:** Performs text cleaning and normalization for analysis.
* **Text Vectorization:** Transforms text into numerical features using **TF-IDF**.
* **Sentiment Analysis:** Classifies text sentiment using a **Machine Learning Model (Multinomial Naive Bayes)** with results (Positive / Neutral / Negative).
* **Web Interface:** A **Flask**-based web interface for user interaction and result display.
* **Data Storage:** Stores scraping and analysis results into a local database.
* **Automation/Scheduler:** The system can perform scraping and analysis tasks periodically (**scheduled job**).

## 🧰 Technology Stack

| Category | Technology | Description |
| :--- | :--- | :--- |
| **Language** | Python 3.x | Main language for development. |
| **Web Scraping** | `requests`, `BeautifulSoup`, `Selenium` | Libraries for web data retrieval. |
| **Machine Learning** | `scikit-learn` | Library for TF-IDF Vectorizer and the **Multinomial Naive Bayes** model. |
| **Web Framework** | Flask | Python micro-framework for the web application. |
| **Database** | MySQL | Local storage for analysis results. |
| **Automation** | *Native Scheduler* / *Job Runner* | For running periodic scraping tasks. |
| **Front-end** | HTML, CSS | For the web interface display. |

---

## 🧑‍💻 Local Installation & Running Guide

### 1. Clone Repository

```bash
git clone [https://github.com/](https://github.com/)<username>/Automation-Scrapper-With-Sentiment-Analysis.git
cd Automation-Scrapper-With-Sentiment-Analysis
```
### 2. Setup Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```
### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
### 4. Train Model
```bash
python train_and_save_model.py
```
### 5. Run Web Application
```bash
python app.py
```
The application will be available at the URL displayed in the console (typically **http://127.0.0.1:5000**).
