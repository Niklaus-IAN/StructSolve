# StructSolve - Slope Deflection Method Calculator

A full-stack structural analysis application implementing the Slope Deflection Method for continuous beam analysis.

## 🚀 Live Demo

- **Frontend**: [Coming soon - Deploy to Render.com]
- **Backend API**: [Coming soon - Deploy to Render.com]
- **API Documentation**: [Coming soon]/docs

## 📋 Features

- ✅ **Accurate Slope Deflection Analysis**: Python backend with NumPy for precise calculations
- ✅ **Modern UI**: React frontend with beautiful glassmorphism design
- ✅ **Interactive Visualizations**: Real-time Shear Force and Bending Moment diagrams
- ✅ **Multiple Load Types**: UDL, Point loads, and more
- ✅ **Support Types**: Fixed, Pinned, and Roller supports
- ✅ **Continuous Beams**: Handles multi-span beams correctly
- ✅ **RESTful API**: FastAPI backend with Swagger documentation

## 🏗️ Architecture

### Backend (Python/FastAPI)
- **Slope Deflection Solver**: Implements textbook method with matrix operations
- **NumPy**: Accurate linear algebra solver
- **Pydantic**: Type-safe request/response models
- **FastAPI**: Modern async API framework

### Frontend (React/TypeScript)
- **React 19**: Modern UI components
- **TypeScript**: Type-safe frontend code
- **Chart.js**: Interactive diagram visualization
- **Tailwind CSS**: Beautiful, responsive design
- **Express**: Production server

## 🛠️ Local Development

### Prerequisites
- Python 3.11+
- Node.js 20+
- npm

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will run on http://localhost:8000
API docs available at http://localhost:8000/docs

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will run on http://localhost:5000

## 📦 Deployment

This project is configured for deployment on [Render.com](https://render.com).

### Deploy to Render

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Create Render Account**: Sign up at https://render.com

3. **Deploy via Blueprint**:
   - Go to Render Dashboard
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render will auto-detect `render.yaml` and deploy both services

4. **Set Environment Variable**:
   - After backend deploys, copy its URL
   - Go to frontend service settings
   - Add environment variable:
     - Key: `VITE_API_URL`
     - Value: `https://your-backend-url.onrender.com`

5. **Redeploy Frontend**: Trigger manual deploy to apply environment variable

### Environment Variables

#### Frontend
- `VITE_API_URL`: Backend API URL (e.g., `https://structsolve-backend.onrender.com`)

#### Backend
- `PORT`: Automatically set by Render (default: 8000)

## 📚 Project Structure

```
structuralanalysis/
├── backend/                    # Python FastAPI Backend
│   ├── main.py                # API endpoints
│   ├── solver.py              # Slope Deflection solver (327 lines)
│   ├── models.py              # Pydantic models
│   └── requirements.txt       # Python dependencies
│
├── frontend/                   # React Frontend
│   ├── client/                # React application
│   │   ├── src/
│   │   │   ├── App.tsx        # Main component
│   │   │   ├── lib/
│   │   │   │   ├── solver.ts  # API client
│   │   │   │   └── types.ts   # TypeScript types
│   │   │   └── components/    # UI components
│   │   └── vite-env.d.ts      # Vite type definitions
│   ├── server/                # Express server
│   │   └── index.ts
│   └── package.json
│
├── render.yaml                 # Render.com deployment config
└── README.md
```

## 🧮 How It Works

### Slope Deflection Method

The calculator implements the classic Slope Deflection Method for structural analysis:

1. **Calculate Fixed End Moments (FEMs)** for each load type
2. **Assemble stiffness matrix** using: `M_ij = (2EI/L)(2θ_i + θ_j) + FEM_ij`
3. **Apply boundary conditions** (zero rotation at fixed supports)
4. **Solve for unknown rotations** using NumPy's linear solver
5. **Calculate final moments and shears** from rotations
6. **Compute support reactions** from equilibrium

### API Flow

```
User Input → React UI → solver.ts → FastAPI Backend → NumPy Solver → Results → Chart.js Diagrams
```

## 🎓 For Coursework

This project demonstrates:
- **Full-stack development** (Python backend + React frontend)
- **Structural engineering** (Slope Deflection Method implementation)
- **Software engineering** (RESTful API, type safety, error handling)
- **Modern web technologies** (FastAPI, React, TypeScript, Tailwind)

## 📄 License

MIT

## 👤 Author

Created for structural analysis coursework.

---

**Note**: Free tier on Render.com has a "cold start" delay (~30-60 seconds) after 15 minutes of inactivity. This is normal and acceptable for educational/demo purposes.
