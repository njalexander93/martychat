# MartyChat

MartyChat is an AI-powered chatbot designed to assist users with **academic-based answers to psychology questions**. It provides reliable, well-researched responses to psychology-related queries.

---

## 🚀 Project Overview

MartyChat consists of:
1. **FastAPI Backend** (Python 3.12.3)
   - Processes user queries and generates responses.
   - Integrates with OpenAI & Pinecone for AI-powered responses.
   - Supports WebSockets for real-time conversations.

2. **Next.js Frontend** (React)
   - Provides an intuitive UI for chatting with MartyChat.
   - Connects to the backend for dynamic interactions.

3. **Deployment Plan**
   - Hosted on **AWS** (backend & AI model).
   - Frontend can be deployed via **Vercel, AWS Amplify, or S3 + CloudFront**.
   - AI model deployment options include **SageMaker, ECS, or EC2**.

---

## 🛠️ Setup Instructions

### 1️⃣ Clone the Repository
```sh
git clone https://github.com/yourusername/martychat.git
cd martychat
```

### 2️⃣ Set Up Backend (FastAPI)
#### Install Python Dependencies
```sh
python3 -m venv venv
source venv/bin/activate  # (On Windows use `venv\Scripts\activate`)
pip install -r requirements.txt
```

#### Run FastAPI
```sh
uvicorn backend.main:app --reload
```
- The API will be available at **http://127.0.0.1:8000/**.

---

### 3️⃣ Set Up Frontend (Next.js)
#### Install Node.js & Dependencies
Make sure Node.js is installed, then run:
```sh
cd frontend
npm install
npm run dev
```
- The frontend will be available at **http://localhost:3000/**.

---

## 📂 Project Structure

```
martychat/
│── backend/             # FastAPI Backend
│   ├── main.py          # FastAPI app entry point
│   ├── models/          # AI model-related files
│   ├── api/             # API routes
│   ├── utils/           # Helper functions
│
│── frontend/            # Next.js Frontend
│   ├── pages/           # Page-based routing
│   ├── components/      # Reusable UI components
│   ├── public/          # Static assets
│
│── venv/                # Python virtual environment (ignored)
│── requirements.txt     # Backend dependencies
│── .gitignore           # Ignored files
│── README.md            # Project documentation
```

---

## 📌 Key Technologies Used
### 🔹 **Backend (FastAPI)**
- **FastAPI** for API and real-time interactions.
- **Uvicorn** for server execution.
- **OpenAI API** for psychology-related responses.
- **Pinecone** for efficient vector search.
- **WebSockets** for real-time chat.
- **GraphQL (Strawberry-GraphQL)** for structured queries.

### 🔹 **Frontend (Next.js)**
- **React + Next.js** for UI.
- **TailwindCSS** for styling.
- **Fetch API / Axios** for API communication.

---

## ✅ To-Do List
- [ ] Implement user authentication (Sign-in & Registration).
- [ ] Develop chatbot selection page.
- [ ] Implement real-time chat UI.
- [ ] Deploy to AWS.

---

## 🚨 Private Repository Notice
This is a **closed-source private project**. **Unauthorized distribution or public sharing is prohibited.**
