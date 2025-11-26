#!/usr/bin/env python
"""Script para executar a aplicação."""
import uvicorn

if __name__ == "__main__":
    import os
    from app.config import settings
    
    port = int(os.getenv("PORT", settings.PORT))
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=reload,
    )

