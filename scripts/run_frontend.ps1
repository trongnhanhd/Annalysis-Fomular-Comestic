# Run from the project root in a SECOND PowerShell terminal.
Set-Location frontend
if (!(Test-Path "node_modules")) { npm install }
$env:RND_API_INTERNAL_URL="http://127.0.0.1:8000"
npm run dev
