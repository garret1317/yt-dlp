import time

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    update_url_query,
    urlhandle_detect_ext,
    traverse_obj
)

class PlanetRadioLiveIE(InfoExtractor):
    _VALID_URL = r'https?://(?:planetradio\.co\.uk|radioplay\.(dk|no|fi|se)|soundis\.(ro|gr))/(?P<id>[\w|-]+)/(?:player|spiller|afspiller|spelare)/?$'
    IE_DESC = "planetradio.co.uk, radioplay.dk, radioplay.no, radioplay.fi, soundis.ro, soundis.gr"
    _TESTS = [{
        'url': 'https://planetradio.co.uk/kiss/player/',
        'info_dict': {
            'id': 'kiss',
            'ext': 'm4a',
            'title': 're:^KISS.+$',
            'description': 'The Beat Of The UK',
            'live_status': 'is_live',
            'tags': ['Pop', 'Urban'],
        }
    }, {
        'url': 'https://radioplay.no/radio-rock/spiller/',
        'info_dict': {
            'id': 'radio-rock',
            'ext': 'mp3',
            'title': 're:^Radio Rock.+$',
            'description': 'Ekte Rock',
            'live_status': 'is_live',
        },
    }, {
        'url': 'https://radioplay.dk/nova/afspiller/',
        'info_dict': {
            'id': 'nova',
            'ext': 'm4a',
            'tags': ['Pop'],
            'description': 'Lyden af i dag',
            'title': 're:^NOVA.+$',
            'live_status': 'is_live',
        },
    }, {
        'url': 'https://radioplay.fi/basso/player/',
        'info_dict': {
            'id': 'basso',
            'ext': 'm4a',
            'description': 'Basso elää ja hengittää musiikkia',
            'title': 're:^Basso.+$',
            'live_status': 'is_live',
        },
    }, {
        'url': 'https://soundis.ro/kissfm/player/',
        'info_dict': {
            'id': 'kissfm',
            'ext': 'm4a',
            'tags': ['Pop'],
            'live_status': 'is_live',
            'title': 're:^Kiss FM.+$',
            'description': '# 1 Hit Radio',
        },
    }, {
        'url': 'https://soundis.gr/ant1radio/player/',
        'info_dict': {
            'id': 'ant1radio',
            'ext': 'm4a',
            'live_status': 'is_live',
            'tags': ['Pop'],
            'description': 'Τα καλύτερα τραγούδια παίζουν εδώ',
            'title': 're:^Ant1 Radio.+$',
        },
    }, {
        'url': 'https://radioplay.se/rockklassiker/spelare/',
        'info_dict': {
            'id': 'rockklassiker',
            'ext': 'mp3',
            'live_status': 'is_live',
            'description': 'Det bästa från 70- 80- & 90-talen',
            'title': 're:^Rockklassiker.+$',
        },
    }, {
        # premium only
        'url': 'https://planetradio.co.uk/avant-garde/player/',
        'info_dict': {
            'id': 'avant-garde',
            'ext': 'm4a',
            'live_status': 'is_live',
            'title': 're:^Avant Garde.+$',
            'tags': ['Jazz, Blues & Soul'],
            'description': 'md5:032a49aeee56cda5644df47f5a1afdd0',
        },
    }]

    def _real_extract(self, url):
        station_id = self._match_id(url)
        meta = self._download_json(f'https://listenapi.planetradio.co.uk/api9.2/initdadi/{station_id}', station_id)

        streams = meta['stationStreams']
        formats = []

        seen_urls = []

        for stream in streams:
            url = stream['streamUrl']
            if url in seen_urls:
                pass
            else:
                seen_urls.append(url)
                url = update_url_query(url, {'aw_0_1st.skey': int(time.time())})
                # something to do with the advertising provider - aw = https://www.adswizz.com/
                # source: api has a lot of keys about Adswizz
                stream_type = stream.get('streamType')
                info = {
                    'vcodec': 'none',
                #    'quality': -1
                }

                format_id = f'{stream_type}-{stream["streamQuality"]}'
                quality = -1

                if stream_type == 'hls':
                    info = {**info, **self._extract_m3u8_formats(url, station_id)[0]}
                else:
                    info['url'] = url
                    info['tbr'] = stream.get('streamBitRate')
                    info['abr'] = info.get('tbr')

                if not determine_ext(url, default_ext=False):
                    urlh = self._request_webpage(url, station_id, note='Determining source extension')
                    ext = urlhandle_detect_ext(urlh)
                    if ext == 'aac':
                        ext = 'm4a'
                    info['ext'] = ext
                elif stream_type == 'adts':
                    info['ext'] = 'm4a'
                elif stream_type == 'mp3':
                    info['ext'] = 'mp3'
    #                quality -= 1

                if stream.get('streamPremium'):
                    info['format_note'] = 'Premium'
                    info['preference'] = 1
                    format_id += "-premium"

                if stream['streamQuality'] == 'lq':
                    quality -= 1

                info['format_id'] = format_id
                info['quality'] = quality

#                if info.get('acodec') == None:
#                    info['acodec'] = info['ext']

                formats.append(info)

        return {
            'id': station_id,
            'title': meta['stationName'],
            'tags': meta.get('stationGenreTags'),
            'description': meta.get('positioningStatementDescription') or meta.get('stationStrapline'),
            'is_live': True,
            'formats': formats,
        }


class PlanetRadioOnDemandIE(InfoExtractor):
    _VALID_URL = r'https?://(?:planetradio\.co\.uk|radioplay\.(dk|no|fi)|soundis\.(ro|gr))/(?P<station>[\w|-]+)/player/(?P<episode>\d+)/?$'
    _TESTS = [{
        'url': 'https://planetradio.co.uk/kiss/player/209567378/',
        'info_dict': {
            'id': '209567378',
            'ext': 'm4a',
            'description': 'md5:2f37a637e11c42e298876ce57febaf04',
            'duration': 7200,
            'title': 'Dance: DJ S.K.T.',
            'thumbnail': 'md5:2077890fdfba85e33000bd498f321874',
        }
    }]

    def _get_format_dict(self, url):
        info = {
            'url': url,
            'vcodec': 'none',
            'ext': url.split(".")[-1],  # determine_ext gives 'php'
            'preference': -1,
        }
        info['acodec'] = info['ext']
        if info['ext'] == 'mp3':
            info['preference'] -= 1
        return info

    def _find_episode(self, episode_id, station_meta):
        for date, episodes in station_meta.items():
            for ep in episodes:
                if ep['episodeid'] == int(episode_id):
                    return ep

    def _real_extract(self, url):
        station, episode = self._match_valid_url(url).group('station', 'episode')

        formats = []
        station_meta = self._download_json(f'https://listenapi.planetradio.co.uk/api9.2/listenagaindadi/{station}', station)
        episode_meta = self._find_episode(episode, station_meta)

        formats.append(self._get_format_dict(episode_meta.get('mediaurl')))
        formats.append(self._get_format_dict(episode_meta.get('mediaurl_mp3')))

        return {
            'id': episode,
            'duration': episode_meta['duration'],
            'title': episode_meta['title'],
            'description': episode_meta.get('shortdesc'),
            'thumbnails': [{
                'url': episode_meta.get('imageurl'),
                'id': 'imageurl',
                'preference': -2,
                }, {
                'url': episode_meta.get('imageurl_square'),
                'id': 'imageurl_square',
                'preference': -1,
                }],
            'formats': formats,
        }
