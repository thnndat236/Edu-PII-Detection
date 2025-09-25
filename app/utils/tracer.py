from core.config import settings
# Opentelemetry imports
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource


def setup_tracing():
    try:
        # Create resource with service information
        resource = Resource.create({
            "service.name": settings.OTEL_SERVICE_NAME,
            "service.version": "1.0.0",
            "service.instance.id": settings.JAEGER_HOSTNAME
        })

        # Set up tracer provider with resource
        trace.set_tracer_provider(TracerProvider(resource=resource))
        tracer = trace.get_tracer(__name__)

        # Use the collector's OTLP gRPC endpoint (port 4317) where to export the traces to (the collector)
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.JAEGER_COLLECTOR_ENDPOINT,
            insecure=(settings.JAEGER_COLLECTOR_INSECURE.lower() == 'true')
        )

        # Add the exporter to the tracer provider with error handling
        span_processor = BatchSpanProcessor(
            otlp_exporter,
            max_queue_size=2048,
            schedule_delay_millis=5000,
            max_export_batch_size=512,
            export_timeout_millis=30000
        )

        trace.get_tracer_provider().add_span_processor(span_processor)

        return tracer
    
    except Exception as e:
        print(f"Failed to setting tracing: {str(e)}")
        import traceback
        traceback.print_exc()
        return trace.NoOpTracer()
    

def remove_tracing():
    trace.get_tracer_provider().shutdown()