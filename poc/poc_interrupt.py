import asyncio


# Globales Event
interrupt_event = asyncio.Event()

async def clock():
    while True:
        await asyncio.sleep(1)
        print('Clock')


class MyClass:
    def __init__(self):
        self._queue = asyncio.Queue()

    async def compute_action(self):
        while not self._queue.empty():
            await self._queue.get()

        done, pending = await asyncio.wait([
            asyncio.create_task(self._queue.get()),
            asyncio.create_task(clock()),
            asyncio.create_task(interrupt_event.wait())
        ], return_when=asyncio.FIRST_COMPLETED)

        if interrupt_event.is_set():
            print("Interrupted")
            interrupt_event.clear()
            result = None
        else:
            result = done.pop().result()

        for task in pending:
            task.cancel()

        return result


async def set_event_after_delay(event, delay):
    await asyncio.sleep(delay)
    event.set()


async def add_to_queue_after_delay(queue, item, delay):
    await asyncio.sleep(delay)
    await queue.put(item)


async def main():
    my_class1 = MyClass()

    for i in [3, 5, 2]:
        print(f"Interrupt nach {i} Sekunden:")

        # Simuliere das Setzen des Events
        task1 = asyncio.create_task(set_event_after_delay(interrupt_event, i))

        # Simuliere das Hinzufügen eines Eintrags zur Queue
        # noinspection PyProtectedMember
        task2 = asyncio.create_task(add_to_queue_after_delay(my_class1._queue, f"Daten {i}", 4))

        # Starte compute_action
        result = await my_class1.compute_action()
        print(f"Ergebnis: {result}\n")

        task1.cancel()
        task2.cancel()

    # Zeigt, dass die Uhr nicht weiterläuft
    await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main(), debug=True)

