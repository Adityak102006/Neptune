# 🔱 Neptune — Local Image Similarity Search

Neptune is a desktop app that lets you search for visually similar images in your local folders — like Google Lens, but for your own files. Drop in a query image and instantly find matches ranked by visual similarity.

**Built with** React · FastAPI · PyTorch (MobileNetV2)

---

## ✨ Features

- 🔍 **Visual Search** — Find similar images using deep learning embeddings
- 📁 **Local & Private** — Everything runs on your machine; no data leaves your PC
- ⚡ **Fast Indexing** — Powered by MobileNetV2 feature extraction
- 🖼️ **Drag & Drop** — Drop a query image or click to browse
- 🌑 **Modern UI** — Clean dark-themed interface

---

## 🚀 Quick Start (Windows)

### Prerequisites

- [Python 3.10+](https://python.org) — check "Add Python to PATH" during install
- [Node.js 18+](https://nodejs.org)

### Run

1. **Clone the repo**
   ```bash
   git clone https://github.com/Adityak102006/Neptune.git
   cd Neptune
   ```

2. **Double-click `Neptune.bat`**

That's it! The launcher will automatically:
- Create a Python virtual environment
- Install all dependencies
- Build the frontend
- Start the server and open your browser

---

## 🛠️ Manual Setup

If you prefer to set things up manually:

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate       # Windows

# 2. Install Python dependencies
pip install -r backend/requirements.txt

# 3. Build the frontend
cd frontend
npm install
npm run build
cd ..

# 4. Start the server
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Then open **http://localhost:8000** in your browser.

---

## 💻 Development Mode

For development with hot-reload on the frontend:

```bash
# Terminal 1 — Backend
venv\Scripts\activate
python -m uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Frontend (with API proxy)
cd frontend
npm run dev
```

The Vite dev server (port 5173) proxies `/api` requests to the backend.

---

## 📂 Project Structure

```
Neptune/
├── backend/
│   ├── main.py          # FastAPI routes + static file serving
│   ├── model.py         # MobileNetV2 image embedder
│   ├── indexer.py       # In-memory similarity index
│   └── requirements.txt
├── frontend/
│   ├── src/App.jsx      # React UI
│   └── ...
├── Neptune.bat          # One-click Windows launcher
└── README.md
```

---

## 🔧 How It Works

1. **Index** — Point Neptune at a folder. It scans all images and extracts 1280-dim feature vectors using MobileNetV2.
2. **Search** — Upload a query image. Neptune computes its embedding and ranks all indexed images by cosine similarity.
3. **Results** — View the top matches with similarity scores, click to enlarge.

---

## 📄 License

MIT
