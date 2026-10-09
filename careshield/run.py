import uvicorn
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print("=" * 60)
    print("🛡️  NexByte CareShield | Customer Care AI Poison Defense Gateway")
    print(f"🌐  Web Portal Dashboard: http://localhost:{port}")
    print(f"📘  OpenAPI Specifications: http://localhost:{port}/docs")
    print("=" * 60)
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
