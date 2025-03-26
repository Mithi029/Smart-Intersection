import asyncio
from gmqtt import Client as MQTTClient

# Broker details
BROKER = 'broker.hivemq.com'
PORT = 1883
TOPIC = 'test/asyncio/publisher'
CLIENT_ID = 'first_rsu_client'

# Create the MQTT client
client = MQTTClient(CLIENT_ID)


# Define the on_connect callback
def on_connect(client, flags, rc, properties):
    print("Connected to the MQTT broker!")


client.on_connect = on_connect


# Async function to publish messages
async def publish_messages():
    # Connect to the broker
    await client.connect(BROKER, PORT)

    # Publish 5 messages with a delay
    for i in range(5):
        message = f"Message {i + 1} from publisher"
        client.publish(TOPIC, message)
        print(f"Published: {message}")
        await asyncio.sleep(2)  # Wait for 2 seconds between messages

    # Disconnect after publishing
    await client.disconnect()


# Run the asyncio loop
asyncio.run(publish_messages())
