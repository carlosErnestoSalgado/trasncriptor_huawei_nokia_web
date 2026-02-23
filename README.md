# Trasncriptor Huawei Nokia Web

Web application built with **Django** that provides a responsive interface for transcribing Huawei and Nokia related text content.

This project is part of a larger suite of tools, including task management and transcription utilities.

---

## 🧠 Project Overview

This repository contains a Django-based web application that serves as a **responsive frontend and backend** for a transcription system. The app is structured with Django views and templates, and includes an interface for interacting with transcription logic related to Huawei and Nokia textual data.

---

## 🛠️ Technologies Used

- Python  
- Django Web Framework  
- HTML / CSS  
- Responsive Web Design  
- JavaScript (if included in templates)  

---

## 📁 Project Structure
trasncriptor_huawei_nokia_web/  
├── interfacesapp/ # Django app: views, templates, static assets  
├── translaterdjango/ # Django project configuration  
├── manage.py # Django CLI runner  
├── requirements.txt # Python dependencies  
└── README.md # Project documentation  

---

## 📌 Features

- Web interface built with Django
- Responsive UI for transcription tasks
- Backend Django logic ready to extend with APIs
- Easily integrable with third-party transcription services
- Modular project structure

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the repository

```bash
git clone https://github.com/carlosErnestoSalgado/trasncriptor_huawei_nokia_web.git
cd trasncriptor_huawei_nokia_web
```
##2️⃣ Install dependencies

Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```
Install required packages:
```bash
pip install -r requirements.txt
3️⃣ Run the server
python manage.py migrate
python manage.py runserver
```
By default, the app will run on:

http://localhost:8000

Open this URL in your browser to access the web interface.
