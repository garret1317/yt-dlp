import base64
import json

from .common import (
    ExtractorError,
    InfoExtractor,
)
from ..utils import traverse_obj


class FMPlaPlaBaseIE(InfoExtractor):
    _GEO_BYPASS = False
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

        token = stream_info.get('token')
        payload = json.loads(base64.b64decode(token.split('.')[1] + "=="))
        if payload.get('sub').startswith('/announce'):
            self.raise_geo_restricted(countries=['JP'])

        return {
            'protocol': 'fmplapla',
            'url': stream_info.get('location'),
            'token': token,
            'ext': 'ogg',
            'live_status': 'is_live',
            'vcodec': 'none',
            'id': station_id,
            **traverse_obj(station_info, {
                'id': 'id',
                'title': 'name',
                'description': 'description',
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


class JCBASimulIE(FMPlaPlaBaseIE):
    _VALID_URL = r'https://www.jcbasimul\.com/(?P<id>[^/]+)'
    _TESTS = [{
        'url': 'https://www.jcbasimul.com/yonezawancvfm',
        'info_dict': {
            'title': 're:^エフエムNCV .+$',
            'id': 'yonezawancvfm',
            'ext': 'ogg',
            'description': '山形県南、置賜地方の情報・魅力がつまったエフエムNCVおきたまGO！米沢市から放送中！',
            'thumbnail': 'md5:93bea02cdf5c38921402434725fba31d',
            'live_status': 'is_live',
            'token': str,
        },
        'params': {'skip_download': True},
    }]

    _origin = 'https://www.jcbasimul.com'
    _api = 'https://api.radimo.smen.biz/api/v1/select_stream?station={station_id}&channel=0&quality=high&burst=5'
