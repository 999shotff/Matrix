// Set this to your deployed Render backend URL once it's live,
// e.g. "https://matrix-backend.onrender.com"
// The prototype currently runs on fake local data — this file is the hook
// point for when we wire real fetch() calls to /api/uploads, /api/settings/test,
// and /api/generate in the next pass.
window.MATRIX_API_BASE_URL = "http://localhost:8080";
