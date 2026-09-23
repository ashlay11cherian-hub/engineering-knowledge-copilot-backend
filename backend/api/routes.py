from fastapi import APIRouter, HTTPException, Query

from backend.models.api_models import (
    QueryRequest,
    QueryResponse,
    RepositorySummary,
    UserSummary,
)
from backend.services.demo_service import (
    get_demo_repositories,
    get_demo_users,
)
from backend.services.query_service import (
    execute_demo_query,
)
from backend.services.repository_catalog_service import (
    get_repository_catalog,
)



from backend.models.activity_models import (
    ActivityEvent,
)
from backend.services.activity_service import (
    get_activity_events,
)


router = APIRouter(prefix="/api")


@router.get(
    "/users",
    response_model=list[UserSummary],
)
def list_users():
    return get_demo_users()


@router.get(
    "/repositories",
    response_model=list[RepositorySummary],
)
def list_repositories():
    return get_repository_catalog()


@router.post(
    "/query",
    response_model=QueryResponse,
)
def query_knowledge(
    request: QueryRequest,
):

    try:
        return execute_demo_query(
            user_id=request.user_id,
            repository_id=request.repository_id,
            query=request.query,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="Knowledge service is not ready.",
        )


@router.get(
    "/activity",
    response_model=list[ActivityEvent],
)
def list_activity(
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
):
    return get_activity_events(
        limit=limit,
    )
