# telegram_bot/sse_client.py
import asyncio
import json
import logging
from typing import Callable, Awaitable, Optional

import aiohttp
from aiohttp import ClientSession, ClientError

logger = logging.getLogger(__name__)

class SSEClient:
    """
    Асинхронный клиент для Server-Sent Events (SSE).
    Подключается к указанному URL и вызывает обработчик для каждого полученного события.
    """

    def __init__(
        self,
        url: str,
        on_event: Callable[[dict], Awaitable[None]],
        *,
        reconnect_delay: int = 5,
        max_retries: Optional[int] = None,
        session: Optional[ClientSession] = None,
        headers: Optional[dict] = None,
    ):
        """
        :param url: URL SSE-потока (например, http://localhost:5000/api/stream)
        :param on_event: Асинхронная функция, вызываемая для каждого события (получает dict с данными)
        :param reconnect_delay: Задержка перед переподключением при разрыве (секунд)
        :param max_retries: Максимальное число попыток переподключения (None – бесконечно)
        :param session: Опциональная aiohttp сессия (если не передана, создаётся внутренняя)
        :param headers: Дополнительные HTTP-заголовки
        """
        self.url = url
        self.on_event = on_event
        self.reconnect_delay = reconnect_delay
        self.max_retries = max_retries
        self._session = session
        self._own_session = session is None
        self._headers = headers or {}
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._retry_count = 0

    async def start(self):
        """Запускает прослушивание SSE-потока (в фоновой задаче)."""
        if self._running:
            logger.warning("SSEClient уже запущен")
            return
        self._running = True
        self._retry_count = 0
        self._task = asyncio.create_task(self._run())

    async def stop(self):
        """Останавливает прослушивание."""
        if not self._running:
            return
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("SSEClient остановлен")

    async def _run(self):
        """Основной цикл подключения и чтения потока."""
        while self._running:
            try:
                await self._connect_and_listen()
            except asyncio.CancelledError:
                logger.debug("Задача SSE клиента отменена")
                break
            except Exception as e:
                logger.exception("Необработанная ошибка в SSE клиенте: %s", e)

            if not self._running:
                break

            self._retry_count += 1
            if self.max_retries is not None and self._retry_count > self.max_retries:
                logger.error("Превышено максимальное число попыток переподключения (%s)", self.max_retries)
                break

            logger.info("Переподключение через %s секунд...", self.reconnect_delay)
            await asyncio.sleep(self.reconnect_delay)

    async def _connect_and_listen(self):
        """Устанавливает соединение и читает события."""
        session = self._session if not self._own_session else None
        if session is None and self._own_session:
            session = aiohttp.ClientSession()

        try:
            # Используем переданную сессию или создаём временную
            if session is None:
                async with aiohttp.ClientSession() as temp_session:
                    await self._listen(temp_session)
            else:
                await self._listen(session)
        except ClientError as e:
            logger.warning("Ошибка соединения с SSE: %s", e)
            raise  # Пробрасываем для обработки в цикле переподключения
        finally:
            if self._own_session and session:
                await session.close()

    async def _listen(self, session: ClientSession):
        """Читает поток SSE и парсит события."""
        async with session.get(self.url, headers=self._headers) as resp:
            if resp.status != 200:
                logger.error("SSE endpoint вернул статус %s", resp.status)
                # Можно пробросить исключение, чтобы вызвать переподключение
                resp.raise_for_status()

            logger.info("SSE соединение установлено, начинаем приём событий")
            self._retry_count = 0  # сбрасываем счётчик при успешном подключении

            # Читаем построчно (поток SSE — это текст/plain с пустыми строками-разделителями)
            async for line in resp.content.iter_any():
                # aiohttp возвращает байты, декодируем
                # В SSE данные могут приходить кусками, поэтому накапливаем буфер
                # Но для простоты будем считать, что каждое событие помещается в один chunk.
                # Если нужна надёжная обработка, лучше использовать накопление.
                data = line.decode('utf-8').strip()
                if not data:
                    continue

                # Парсим строку формата "field: value"
                # Обычно события имеют поле "data: ..."
                if data.startswith('data:'):
                    json_str = data[5:].strip()
                    try:
                        event_data = json.loads(json_str)
                        # Вызываем обработчик
                        await self.on_event(event_data)
                    except json.JSONDecodeError:
                        logger.error("Не удалось распарсить JSON из SSE: %s", json_str)
                # Можно также обрабатывать поля event:, id:, retry: если нужно

    @property
    def is_running(self) -> bool:
        return self._running
