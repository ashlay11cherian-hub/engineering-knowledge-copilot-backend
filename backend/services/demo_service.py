from backend.models.api_models import (
    RepositorySummary,
    UserSummary,
)


DEMO_USERS = [
    UserSummary(
        user_id="alex",
        name="Alex",
        role="engineer",
        assigned_programs=["GEN3-WLC"],
        clearance="internal",
    ),
    UserSummary(
        user_id="sarah",
        name="Sarah",
        role="program_manager",
        assigned_programs=[
            "GEN3-WLC",
            "TELEMATICS-X",
        ],
        clearance="confidential",
    ),
    UserSummary(
        user_id="chris",
        name="Chris",
        role="hr",
        assigned_programs=["ALL_PROGRAMS"],
        clearance="restricted",
    ),
    UserSummary(
        user_id="maya",
        name="Maya",
        role="engineer",
        assigned_programs=["WEARABLE-ORBIT"],
        clearance="internal",
    ),
    UserSummary(
        user_id="daniel",
        name="Daniel",
        role="program_manager",
        assigned_programs=[
            "WEARABLE-ORBIT",
            "SMARTGLASS-NOVA",
            "EARBUDS-PULSE",
            "SMARTHOME-HALO",
        ],
        clearance="confidential",
    ),
    UserSummary(
        user_id="priya",
        name="Priya",
        role="engineer",
        assigned_programs=["SMARTHOME-HALO"],
        clearance="internal",
    ),
    UserSummary(
        user_id="evan",
        name="Evan",
        role="executive",
        assigned_programs=["ALL_PROGRAMS"],
        clearance="highly_restricted",
    ),
]


DEMO_REPOSITORIES = [
    RepositorySummary(
        repository_id="demo-engineering-repository",
        name="Engineering Knowledge Demo",
        provider="local_demo",
        status="connected",
        document_count=9,
        last_sync=None,
    )
]


def get_demo_users():
    return DEMO_USERS


def get_demo_repositories():
    return DEMO_REPOSITORIES
