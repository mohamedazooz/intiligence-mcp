import httpx,sys
try:
 r=httpx.get('http://localhost:8000/health',timeout=5); print(r.status_code)
except Exception as e: print('FAIL',e); sys.exit(1)

