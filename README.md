# 💸 CashManager — Smart Financial Workspace

CashManager is a premium, high-performance web application designed to track financial transactions, manage project-wise budgets, and streamline ledger syncs. Built with **Django 6.0.6 (Python 3.12+)** and styled with an ultra-modern, dark-themed SaaS dashboard interface, it serves as a robust control center for individuals, teams, and system administrators.

---

## ✨ Key Features

### 📊 Real-Time Financial Dashboard
* **Dynamic Indicators:** Instantly view Total Income, Total Expenses, and Net Balance (BDT) across different project scopes.
* **Vibrant Charts:** Integrated bar and doughnut charts analyzing transaction trends and financial health.
* **Light/Dark Toggle:** Seamlessly switch between dark-mode and light-mode states instantly.

### 📥 Real-Time Google Sheets Sync
* **Automatic Logging:** Standard transaction entries are instantly synced to your connected Google Sheet.
* **Dynamic Tab-Creation:** Creating a new project automatically provisions a dedicated new tab (worksheet) inside your Google Spreadsheet, writing precise entry timestamps and purposes on the fly.

### 📂 Custom CSV Sheet Importer (No-Code Workspace)
* **Custom Headers Parsing:** Upload *any* custom CSV file with arbitrary columns.
* **Dynamic Form & Table Generator:** The app analyzes the uploaded headers and dynamically generates matching data tables and data-entry forms for that specific project scope.

### 🔐 Granular Access Control & Permissions
* **Admin Permission Matrix:** Administrators can allocate specific access levels to regular users per project:
  * `View Only`: User can read data but cannot write new rows.
  * `Edit Access`: User can view and input dataset entries.
  * `Hidden (Restricted)`: Hides the project completely from the user's dashboard and blocks all access.

### 📑 Activity & Audit Logging
* **Secured Timeline:** A chronological timeline of all administrator and user actions across the platform.
* **Terminal-style IPs:** Audited logs map actor details, target models, and secure monospace IP indicators.

### 📁 One-Click Data Export
* **Ledger Downloads:** Instantly download any project dataset as an offline BDT CSV spreadsheet.

---

## 🛠️ Local Installation & Setup

### Prerequisites
* Python 3.12+
* Pip package manager
* Virtual environment (`virtualenv`)

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/nawabsakib5/Cash-Management-Django-App.git
   cd Cash-Management-Django-App