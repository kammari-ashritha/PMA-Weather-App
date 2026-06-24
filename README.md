# Aurora Weather App
**Built by Kammari Ashritha | PM Accelerator AI Engineer Internship 2026**

It is a robust, full-stack weather application designed to provide intuitive and accurate meteorological data. 

##  Features

* **Live Weather Data**: Delivers real-time current weather alongside a 5-day forecast powered by the OpenWeatherMap API.
* **Smart Location**: Includes GPS auto-detection to instantly find your current location.
* **Search Management**: Features full CRUD functionality, allowing you to save, view, edit, and delete your weather searches.
* **Data Export**: Offers the ability to export saved searches seamlessly as JSON or CSV files.
* **Responsive UI**: Designed to work flawlessly across desktop, tablet, and mobile interfaces.
* **Robust Error Handling**: Includes graceful fallbacks and alerts for invalid city inputs and API failures.

##  Tech Stack

* **Frontend**: Built with React 18, Vite, and Axios.
* **Backend**: Powered by Django 4.2 and Django REST Framework.
* **Database**: Managed with MongoDB via PyMongo.
* **API**: Integrated with OpenWeatherMap.

##  Quick Start (Local Setup)

### Prerequisites
Ensure you have the following installed on your machine:
* Node.js (v18+)
* Python (3.10+)
* MongoDB Community Server
* Git

### 1. Clone the Repository
\`\`\`bash
git clone https://github.com/kammari-ashritha/PMA-Weather-App.git

cd PMA-Weather-App
\`\`\`

### 2. Backend Setup
Open a terminal in the `backend` folder:

\`\`\`bash
cd backend

python -m venv venv

# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt

\`\`\`
Create a `.env` file in the backend directory and add your OpenWeatherMap API key:

\`\`\`env

OPENWEATHER_API_KEY=your_api_key_here

GOOGLE_CLIENT_ID=your_client_id_here

MONGODB_URI=mongodb://localhost:27017/

MONGODB_DB=weather_app

DJANGO_SECRET_KEY=aurora-weather-secret-key-2026-pma

DEBUG=True
\`\`\`

Run the backend server:

\`\`\`bash

python manage.py runserver
\`\`\`

### 3. Frontend Setup
Open a second terminal in the `frontend` folder:

\`\`\`bash

cd frontend

npm install

npm run dev
\`\`\`

Navigate to `http://localhost:5173` in your browser to view the app!
