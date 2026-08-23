<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:F59E0B,100:10B981&height=220&section=header&text=Cash%20Management%20App&fontSize=44&fontColor=ffffff&animation=fadeIn&fontAlignY=35&desc=Track.%20Collaborate.%20Stay%20Accountable.&descAlignY=55&descSize=20" width="100%"/>

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&pause=1000&color=F59E0B&center=true&vCenter=true&width=650&lines=Multi-user+project-based+cash+tracking;AJAX-powered+categories+%26+audit+logs;Email+notifications+via+Gmail+SMTP;Built+with+Django+by+Mohammad+Sakib" alt="Typing SVG" />

<br/>

[![Stars](https://img.shields.io/github/stars/nawabsakib5/Cash-Management-Django-App?style=for-the-badge&color=F59E0B&labelColor=1a1a2e)](https://github.com/nawabsakib5/Cash-Management-Django-App/stargazers)
[![Forks](https://img.shields.io/github/forks/nawabsakib5/Cash-Management-Django-App?style=for-the-badge&color=10B981&labelColor=1a1a2e)](https://github.com/nawabsakib5/Cash-Management-Django-App/network/members)
[![Last Commit](https://img.shields.io/github/last-commit/nawabsakib5/Cash-Management-Django-App?style=for-the-badge&color=3B82F6&labelColor=1a1a2e)](https://github.com/nawabsakib5/Cash-Management-Django-App/commits/main)
[![License](https://img.shields.io/badge/license-Unlicensed-999999?style=for-the-badge&labelColor=1a1a2e)](#-license)

</div>

---

## 💰 About The Project

**Cash Management App** is a multi-user Django application for tracking shared finances across collaborative projects. Multiple users can join a project, log transactions under organized categories, and keep a fully auditable trail of every change — with email alerts keeping everyone in the loop. Built with a clean, **dark-themed UI** for comfortable day-to-day use.

<div align="center">
<img src="https://skillicons.dev/icons?i=python,django,sqlite,javascript,html,css,bootstrap,git,github&theme=dark" />
</div>

---

## 📚 Table of Contents

- [✨ Features](#-features)
- [🏗️ Architecture](#️-architecture)
- [📁 Project Structure](#-project-structure)
- [🛠️ Tech Stack](#️-tech-stack)
- [🚀 Getting Started](#-getting-started)
- [⚙️ Environment Variables](#️-environment-variables)
- [🗺️ Roadmap](#️-roadmap)
- [👤 Author](#-author)

---

## ✨ Features

<table>
<tr>
<td width="50%" valign="top">

### 👥 Multi-User Collaboration
Custom user model (`CustomUser`) with project-based access — invite users to collaborate on shared cash records.

### 📊 Per-Project Transaction Tracking
Every project keeps its own isolated ledger of income and expenses.

### 🔽 Dynamic Category Dropdowns
AJAX-powered category → sub-category selection that updates in real time as you fill a transaction form.

</td>
<td width="50%" valign="top">

### 📜 Audit Logging
Every create, update, and delete action is logged — full accountability, no silent edits.

### 📧 Email Notifications
Automatic alerts via **Gmail SMTP** when transactions or project changes happen.

### 🌙 Dark-Themed UI
A clean, modern, eye-friendly interface for daily financial tracking.

</td>
</tr>
</table>

---

## 🏗️ Architecture

```mermaid
flowchart LR
    U["👤 User"] --> Auth["🔐 CustomUser Auth"]
    Auth --> Proj["📁 Project"]
    Proj --> Team["👥 Collaborators"]
    Proj --> Txn["💵 Transactions"]
    Txn --> Cat["🗂️ Category"]
    Cat --> Sub["🔽 Sub-Category (AJAX)"]
    Txn --> Log["📜 Audit Log"]
    Txn --> Mail["📧 Gmail SMTP\nNotification"]
    Mail --> Team
```

---

## 📁 Project Structure

```text
Cash-Management-Django-App/
├── cashApp/              # Core app — models, views, forms, AJAX endpoints
│   ├── models.py         # CustomUser, Project, Transaction, Category, AuditLog
│   ├── views.py          # Project & transaction views
│   └── templates/        # Dark-themed UI templates
├── cashProject/          # Django project settings & root URL config
├── .gitignore
├── manage.py              # Django's command-line utility
└── requirements.txt        # Project dependencies
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | ![Python](https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white) ![Django](https://img.shields.io/badge/-Django-092E20?style=flat-square&logo=django&logoColor=white) |
| **Database** | ![SQLite](https://img.shields.io/badge/-SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white) |
| **Frontend** | ![HTML5](https://img.shields.io/badge/-HTML5-E34F26?style=flat-square&logo=html5&logoColor=white) ![CSS3](https://img.shields.io/badge/-CSS3-1572B6?style=flat-square&logo=css3&logoColor=white) ![JavaScript](https://img.shields.io/badge/-JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black) |
| **Notifications** | ![Gmail](https://img.shields.io/badge/-Gmail%20SMTP-EA4335?style=flat-square&logo=gmail&logoColor=white) |

---

## 🚀 Getting Started

### ✅ Prerequisites
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![Git](https://img.shields.io/badge/Git-Required-F05032?style=flat-square&logo=git&logoColor=white)

### 📦 Installation

```bash
# 1. Clone the repository
git clone https://github.com/nawabsakib5/Cash-Management-Django-App.git
cd Cash-Management-Django-App

# 2. Create & activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply migrations
python manage.py migrate

# 5. Create a superuser
python manage.py createsuperuser

# 6. Run the development server
python manage.py runserver
```

Visit **`http://127.0.0.1:8000/`** to start tracking. 🎉

---

## ⚙️ Environment Variables

Create a `.env` file in the project root for email notifications:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-gmail-address@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
```

> 💡 Use a Gmail **App Password**, not your regular Gmail password, for SMTP auth.

---

## 🗺️ Roadmap

- [ ] 📈 Charts & analytics dashboard per project
- [ ] 📤 Export transactions to CSV / Excel
- [ ] 🔔 In-app notifications alongside email
- [ ] 📱 Mobile-responsive redesign
- [ ] 🧾 Recurring transaction support

---

## 👤 Author

<div align="center">

<img src="https://github.com/nawabsakib5.png" width="100" style="border-radius:50%"/>

**Mohammad Sakib**

[![GitHub](https://img.shields.io/badge/GitHub-nawabsakib5-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/nawabsakib5)

</div>

---

## 📄 License

This project is currently **licensed**. Reach out to the author for usage permissions.

<div align="center">
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:10B981,100:F59E0B&height=100&section=footer" width="100%"/>
</div>
