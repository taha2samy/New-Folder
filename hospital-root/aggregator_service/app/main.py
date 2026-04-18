"""GraphQL Aggregator Entrypoint."""

import uvicorn
import grpc
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
import strawberry
import contextlib

from app.core.config import settings
from app.graphql.resolvers import Query, Mutation, init_clients
from app.core.auth_handler import get_context
from app.grpc_clients.patient_client import PatientClient
from app.grpc_clients.clinical_client import ClinicalClient
from app.grpc_clients.pharmacy_client import PharmacyClient

schema = strawberry.Schema(query=Query, mutation=Mutation)

# Global Connections
patient_channel = None
clinical_channel = None
pharmacy_channel = None

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    global patient_channel, clinical_channel, pharmacy_channel
    
    # Init gRPC Connection Pooling
    patient_channel = grpc.aio.insecure_channel(settings.PATIENT_SERVICE_ADDR)
    clinical_channel = grpc.aio.insecure_channel(settings.CLINICAL_SERVICE_ADDR)
    pharmacy_channel = grpc.aio.insecure_channel(settings.PHARMACY_SERVICE_ADDR)
    
    init_clients(
        PatientClient(patient_channel),
        ClinicalClient(clinical_channel),
        PharmacyClient(pharmacy_channel)
    )
    
    yield
    
    await patient_channel.close()
    await clinical_channel.close()
    await pharmacy_channel.close()

app = FastAPI(lifespan=lifespan)

graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context
)

app.include_router(graphql_app, prefix="/graphql")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
