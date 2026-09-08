"""DRF renderer so EventSource Accept: text/event-stream is not rejected with 406."""

from rest_framework.renderers import BaseRenderer


class ServerSentEventRenderer(BaseRenderer):
    media_type = 'text/event-stream'
    format = 'event-stream'
    charset = None
    render_style = 'binary'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data
