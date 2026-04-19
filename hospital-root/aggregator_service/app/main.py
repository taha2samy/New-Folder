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
from app.grpc_clients.laboratory_client import LaboratoryClient
from app.grpc_clients.master_data_client import MasterDataClient
from app.grpc_clients.billing_client import BillingClient

schema = strawberry.Schema(query=Query, mutation=Mutation)

# Global gRPC channel references — managed via the FastAPI lifespan.
patient_channel    = None
clinical_channel   = None
pharmacy_channel   = None
laboratory_channel = None
master_data_channel= None
billing_channel    = None

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    global patient_channel, clinical_channel, pharmacy_channel, laboratory_channel, master_data_channel, billing_channel

    # Open persistent gRPC connection pools to all downstream services.
    patient_channel    = grpc.aio.insecure_channel(settings.PATIENT_SERVICE_ADDR)
    clinical_channel   = grpc.aio.insecure_channel(settings.CLINICAL_SERVICE_ADDR)
    pharmacy_channel   = grpc.aio.insecure_channel(settings.PHARMACY_SERVICE_ADDR)
    laboratory_channel = grpc.aio.insecure_channel(settings.LABORATORY_SERVICE_ADDR)
    master_data_channel= grpc.aio.insecure_channel(settings.MASTER_DATA_SERVICE_ADDR)
    billing_channel    = grpc.aio.insecure_channel(settings.BILLING_SERVICE_ADDR)

    init_clients(
        PatientClient(patient_channel),
        ClinicalClient(clinical_channel),
        PharmacyClient(pharmacy_channel),
        LaboratoryClient(laboratory_channel),
        MasterDataClient(master_data_channel),
        BillingClient(billing_channel),
    )

    yield

    await patient_channel.close()
    await clinical_channel.close()
    await pharmacy_channel.close()
    await laboratory_channel.close()
    await master_data_channel.close()
    await billing_channel.close()

app = FastAPI(lifespan=lifespan)

graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context
)

app.include_router(graphql_app, prefix="/graphql")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
