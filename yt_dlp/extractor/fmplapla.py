from .common import (
    ExtractorError,
    InfoExtractor,
)
from ..utils import traverse_obj


class FMPlaPlaBaseIE(InfoExtractor):

    _origin = None
    _api = None

    def _real_extract(self, url):
        station_id = self._match_id(url)
        webpage = self._download_webpage(url, station_id)
        station_info = traverse_obj(self._search_nextjs_data(webpage, station_id), ('props', 'pageProps', 'station'))
        if not station_info:
            raise ExtractorError("No such station", expected=True, video_id=station_id)
        thumbnails = []
        for index, size in enumerate(['favicon', 'logo_url', 'icon', 'large_icon', 'artwork']):
            url = station_info.get(size)
            if url:
                thumbnails.append({
                    'id': size,
                    'preference': index,
                    'url': station_info.get(size)
                })

        stream_info = self._download_json(self._api.format(station_id=station_id), station_id,
                                          headers={"Origin": self._origin}, data=b'',
                                          note='Getting stream token')
        return {
            'protocol': 'fmplapla',
            'url': stream_info.get('location'),
            'token': stream_info.get('token'),
            'ext': 'ogg',
            'live_status': 'is_live',
            'vcodec': 'none',
            'id': station_id,
            **traverse_obj(station_info, {
                'id': 'id',
                'title': 'name',
            }),
            'thumbnails': thumbnails,
        }


class FMPlaPlaIE(FMPlaPlaBaseIE):
    _VALID_URL = r'https://fmplapla\.com/(?P<id>[^/]+)'
    _TESTS = [{
        'url': 'https://fmplapla.com/fmnishitokyo',
        'info_dict': {
            'title': 're:^エフエム西東京 .+$',
            'id': 'fmnishitokyo',
            'ext': 'ogg',
            'thumbnail': 'https://fmplapla.com/fmnishitokyo/img/artwork.png',
            'live_status': 'is_live',
            'token': str,
        },
        'params': {'skip_download': True},
    }]

    _origin = 'https://fmplapla.com'
    _api = 'https://fmplapla.com/api/select_stream?station={station_id}&burst=5'
