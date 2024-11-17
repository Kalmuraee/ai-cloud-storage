from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from kafka import KafkaConsumer, KafkaProducer
from concurrent.futures import ThreadPoolExecutor

from app.api.v1.api import api_router
from app.core.config import settings
from app.services.processor import document_processor

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

# Kafka setup
producer = KafkaProducer(
    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Background task for Kafka consumer
async def kafka_consumer_task():
    consumer = KafkaConsumer(
        'document-processing',
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id='ai-processor-group',
        auto_offset_reset='earliest'
    )

    # Use ThreadPoolExecutor for CPU-bound processing tasks
    executor = ThreadPoolExecutor(max_workers=3)
    loop = asyncio.get_event_loop()

    try:
        for message in consumer:
            try:
                data = message.value
                bucket_name = data.get('bucket_name')
                object_name = data.get('object_name')

                if not bucket_name or not object_name:
                    continue

                # Process document asynchronously
                await document_processor.process_document(bucket_name, object_name)

                # Send success message
                producer.send('processing-status', {
                    'status': 'success',
                    'bucket_name': bucket_name,
                    'object_name': object_name,
                    'message': 'Document processed successfully'
                })

            except Exception as e:
                # Send error message
                producer.send('processing-status', {
                    'status': 'error',
                    'bucket_name': bucket_name,
                    'object_name': object_name,
                    'message': str(e)
                })

    except Exception as e:
        app.logger.error(f"Kafka consumer error: {str(e)}")
    finally:
        consumer.close()
        executor.shutdown()

@app.on_event("startup")
async def startup_event():
    """Start background tasks on application startup."""
    asyncio.create_task(kafka_consumer_task())

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)