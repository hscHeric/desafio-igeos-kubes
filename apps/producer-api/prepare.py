"""Cria o tópico, sem alterar um tópico existente. Execute antes das APIs."""
import asyncio

from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import TopicAlreadyExistsError, for_code

from config import Settings


async def prepare():
    settings = Settings()
    for attempt in range(1, 6):
        admin = AIOKafkaAdminClient(bootstrap_servers=settings.brokers, request_timeout_ms=5000)
        try:
            async with asyncio.timeout(10):
                await admin.start()
                response = await admin.create_topics([NewTopic(settings.topic, num_partitions=1, replication_factor=1)])
                for topic in response.to_object()["topic_errors"]:
                    if topic["error_code"] not in (0, TopicAlreadyExistsError.errno):
                        raise for_code(topic["error_code"])()
            print(f"Tópico pronto: {settings.topic}")
            return
        except Exception as error:
            print(f"Preparação Kafka: tentativa {attempt}/5; {type(error).__name__}")
            if attempt == 5:
                raise SystemExit("Não foi possível preparar o tópico.") from None
            await asyncio.sleep(2)
        finally:
            await admin.close()


if __name__ == "__main__":
    asyncio.run(prepare())
