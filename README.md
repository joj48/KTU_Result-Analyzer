# KTU Result Analyzer

![TypeScript](https://img.shields.io/badge/TypeScript-2d79c7?style=for-the-badge&logo=typescript&logoColor=white)
![Python](https://img.shields.io/badge/Python-3572A5?style=for-the-badge&logo=python&logoColor=white)
![Other](https://img.shields.io/badge/Other-7f7f7f?style=for-the-badge)

Smart result analysis system that automates university result parsing, department-wise storage, insightful visualization, and interactive reporting. Includes an AI-powered chatbot to assist users with result-related queries and site navigation.

---

## Table of Contents

- [Features](#features)
- [System Architecture](#system-architecture)
- [Frontend Setup](#frontend-setup)
- [Backend Setup](#backend-setup)
- [Tech Stack](#technologies-used)
- [Authors](#authors)
- [License](#license)

---

## Features

- 📄 **Automated Result Parsing:** Upload official university result PDFs. The backend extracts and structures student data using advanced PDF parsing and batch detection logic.
- 📁 **Department-wise Storage:** All data is organized and stored department-wise for streamlined analysis and retrieval.
- 📊 **Insights and Visualization:** The frontend provides rich visualizations and dashboards for batch, department, and student analytics.
- 🤖 **AI Chatbot:** An integrated AI assistant answers user queries about results, CGPA/SGPA calculations, department performance, and more.
- 🏆 **Ranking and Analytics:** Automatically generates student rankings, pass percentages, and department averages.
- 🔒 **Modern Authentication:** Google OAuth and JWT-based protected routes ensure security.
- 📑 **Report Generation:** One-click generation of department-wise CSVs and clean academic reports for further review or archival.
- ⚡ **Streamlit Analysis App:** Separate analytic UI for power-users, using Streamlit for rich report views.

---

## System Architecture

- **Backend:**  
  - *FastAPI* REST server handles all data, authentication, and analysis features.
  - PDF parser and data pipeline extract, validate, clean, and enrich uploaded results.
  - MongoDB as primary database.
  - Streamlit-based report analyzer for instant offline/online result analysis and data export.

- **Frontend:**  
  - *React* + *Vite* app for user-facing dashboard.
  - Integrated Tailwind CSS for modern UI design.
  - Dynamic routing and JWT-protected pages.
  - Visualizes charts and tables using libraries like Recharts.
  - AI-powered Q&A assistant (using shadcn/ui components).

---

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```


---

## Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
- Environment variables can be defined in `Api.env`
- MongoDB (local or cloud) must be accessible for data operations.
- For analysis or report reviews, launch Streamlit analytic UI (`streamlit run app/core/app.py`).

---

## Technologies Used

- **Languages:** TypeScript (frontend), Python (backend)
- **Frameworks:** React, FastAPI, Streamlit
- **Database:** MongoDB
- **Others:** Tailwind CSS, Vite, JWT (Auth), Google OAuth, Recharts, shadcn/ui
- **AI & PDF:** OpenAI integration (for chatbot, if enabled), pdfplumber for PDF parsing

---

## Authors 

**Authors:**
- Jojan Joji
- Aravind R Krishnan
- Akhil Abusalih
- Shobal P Santhosh

**Mentor:**  
Ms. Divya V. L.

> *This is an academic project submitted as part of our coursework at Carmel College of Engineering and Technology, Alappuzha, Kerala. We acknowledge the guidance of our mentor, Ms. Divya VL, and the open-source tools/frameworks on which this project was built.*

---

## License

This project uses the MIT license where applicable. Please consult the `frontend/src/Attributions.md` for third-party asset licenses.

---

## Attributions

UI components are from [shadcn/ui](https://ui.shadcn.com/)

---

**For more info and contribution guidelines, see the respective `/frontend` and `/backend` folders.**
