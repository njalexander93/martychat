# <img src="assets/png/MartyChat_Full-833x200.png" height="100px" alt="MartyChat Logo">

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

## Prerequisites

- **Node.js** (version 14.x or later)
- **Python** (version 3.12.3)
- **git**
- **AWS Account** with necessary permissions to access AWS services

## 🛠️ Setup Instructions

### 1️⃣ Clone the Repository

```sh
git clone https://github.com/\<your_username\>/martychat.git
cd martychat
```

###

### 2️⃣ AWS API Setup

#### AWS CLI Setup

_Note_: If you do not have an AWS account associated with this project, please reach out to admin@martychat.com to get an account.

To access the AWS API, you need to set up your AWS crendentials. Follow these steps:

1. Install the AWS CLI.

```sh
pip install awscli
```

2. Configure AWS CLI

```sh
aws configure
```

3. You will be prompted to enter your AWS Access Key ID, Secret Access Key, region, and output format.

```sh
AWS Access Key ID: <access_key_id>
AWS Secret Access Key: <secret_access_key>
Default region name: <region_of_the_application>
Default output format: json
```

4. Check your AWS identity to confirm the account has been connected to the CLI

```sh
aws sts get-caller-identity
```

Expected output:

```sh
{
    "UserId": "XXXXXXXXXXXXXXXXXXX",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/YourUserName"
}
```

#### Setup AWS SAM (for local development)

MartyChat's backend supports local development of AWS Lambda functions using AWS Serverless Application Model (AWS SAM).
The user can use this to test lambda functions on their local system

1. Ensure you have AWS SAM CLI installed:

```sh
wget https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip
unzip aws-sam-cli-linux-x86_64.zip -d sam-installation
sudo ./sam-installation/install
sam --version
```

2. Ensure you have Docker installed:

```sh
sudo apt update
sudo apt install docker.io -y
sudo usermod -aG docker $USER
newgrp docker
```

3. Build the SAM application

```sh
cd backend/sam
sam build
```

4. Start the local API:

```sh
sam local start-api
```

Your lambda function will be accessible at `http://127.0.0.1:3000/<lambda-function>`. To invoke a lambda function manually use,

```sh
sam local invoke <Lambda Function in sam/template.yaml>
```

### 3️⃣ Set Up Backend (FastAPI)

#### Install Python Dependencies

```sh
python3 -m venv venv
source venv/bin/activate  # (On Windows use `venv\Scripts\activate`)
pip install -r requirements.txt
```

#### Set Up Environment Variables

Create a .env file in the `backend` directory and add your environment-specific variables.

#### Run FastAPI

```sh
uvicorn backend.main:app --reload
```

- The API will be available at **http://127.0.0.1:8000/**.

### 4️⃣ Set Up Frontend (Next.js)

#### Install Node.js & Dependencies

Make sure Node.js is installed, then run:

```sh
cd frontend
npm install
npm run dev
```

- The frontend will be available at **http://localhost:3000/**.

### 5️⃣ Rebuild for Production (if needed)

```sh
npm run build
```

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
│   ├── app/             # Application directory
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

This is a **closed-source private project**. Unauthorized distribution or public sharing is prohibited.
