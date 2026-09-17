from rest_framework.renderers import BaseRenderer


class ServerSentEventRenderer(BaseRenderer):
    """Niestandardowy renderer DRF dla strumienia zdarzeń Server-Sent Events (text/event-stream)."""

    media_type: str = 'text/event-stream'
    format: str = 'event-stream'
    charset: str | None = None
    render_style: str = 'binary'

    def render(
        self,
        data: object,
        accepted_media_type: str | None = None,
        renderer_context: dict[str, object] | None = None,
    ) -> object:
        """Zwraca dane strumieniowe bez modyfikacji.

        Args:
            data (object): Dane strumienia wejściowego.
            accepted_media_type (str | None): Zaakceptowany typ mediów HTTP.
            renderer_context (dict[str, object] | None): Kontekst renderera DRF.

        Returns:
            object: Przekazane dane w postaci niezmienionej.

        Raises:
            TypeError: Gdy accepted_media_type lub renderer_context ma niepoprawny typ.
        """
        if accepted_media_type is not None and not isinstance(accepted_media_type, str):
            raise TypeError("accepted_media_type musi być typu str lub None.")
        if renderer_context is not None and not isinstance(renderer_context, dict):
            raise TypeError("renderer_context musi być typu dict lub None.")
        return data


