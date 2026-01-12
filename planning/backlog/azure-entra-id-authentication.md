# Azure Entra ID Authentication

## Status
Deferred from Phase 4 - to be implemented in Azure deployment phase

## Context
Phase 4 (Search API) is being built without authentication initially to enable faster iteration. Authentication will be added when deploying to Azure AKS.

## Requirements

### App Registration
- Create Azure Entra ID app registration
- Configure redirect URIs for API
- Set up API permissions/scopes

### API Integration
- Add `msal` or `azure-identity` dependency
- Create FastAPI dependency for token validation
- Extract Bearer token from Authorization header
- Validate JWT tokens against Azure Entra ID

### Implementation Pattern
```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def validate_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """Validate Azure Entra ID token."""
    token = credentials.credentials
    # Validate with Azure Entra ID
    # Return decoded token claims
    pass

@router.post("/api/v1/scriptures/search")
async def search_scriptures(
    request: ScriptureSearchRequest,
    user: dict = Depends(validate_token)
):
    # Authenticated endpoint
    pass
```

### Environment Variables
```bash
AZURE_TENANT_ID=xxx
AZURE_CLIENT_ID=xxx
AZURE_CLIENT_SECRET=xxx  # For confidential client flows
```

## Dependencies to Add
```
msal>=1.24
azure-identity>=1.15
python-jose[cryptography]>=3.3  # JWT validation
```

## References
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Azure Entra ID with FastAPI](https://learn.microsoft.com/en-us/azure/active-directory/develop/web-api-quickstart)
- Current auth plan: Private API, may go public later

## Related Phase Documents
- Phase 4: PHASE04-SEARCH_API.md
- Future: Azure deployment phase (to be created)
