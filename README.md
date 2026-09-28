# رسالة — Task 2 Starter

Starter repository for Task 2 of the project:
- First web interface
- 30+ language architecture
- AI translation service adapter
- Shared GitHub workflow

## Project architecture

Frontend:
- Next.js 14
- TypeScript
- CSS
- Designed to be extended with Three.js + Cesium

Backend:
- FastAPI
- Python
- Translation adapter
- Ready for later LlamaIndex + ChromaDB integration

## Important translation note

The project brief asks for 30+ languages. NLLB-200 supports 200 languages, so it is technically suitable for multilingual coverage.

However, the `facebook/nllb-200-distilled-600M` model is currently listed as CC-BY-NC and its model card describes it as a research model, not a production deployment model. The code therefore keeps translation behind an adapter so the team can replace it with an approved production/commercial model if required.

## Run frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

## Run backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## GitHub teamwork

Use:
- `main` = stable version
- `feature/frontend` = UI work
- `feature/translation` = multilingual/AI work
- `feature/backend` = API work

Each teammate works on her own branch and opens a Pull Request to `main`.
