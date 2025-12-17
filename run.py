"""
Main entry point untuk menjalankan aplikasi Last Mile Delivery Optimization
Jalankan dengan: python run.py
"""

import uvicorn
import os

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    
    print("=" * 60)
    print("🚀 Starting Last Mile Delivery Optimization API")
    print("=" * 60)
    print(f"📍 Server: http://localhost:{port}")
    print(f"📄 API Docs: http://localhost:{port}/docs")
    print(f"🎨 Web UI: http://localhost:{port}/ui")
    print("=" * 60)
    
    uvicorn.run(
        "last_mile.app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
