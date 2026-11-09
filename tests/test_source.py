"""Offline adversarial regression fixtures. No live credentials or requests."""
import copy
from email.message import Message
import io
import json
import os
from pathlib import Path
import plistlib
import ssl
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock
import urllib.error
import urllib.request
import zipfile
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import build_source as b
import verify_source as v
import publish_cnb_release as cnb


class Response(io.BytesIO):
    def __init__(self, body, status=206, **headers):
        super().__init__(body)
        self.status = status
        self.headers = Message()
        for k, value in headers.items():
            self.headers[k.replace('_', '-')] = value


class NetworkTests(unittest.TestCase):
    def test_tls_default_unchanged(self):
        ctx = ssl._create_default_https_context()
        self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(ctx.check_hostname)

    def test_token_only_github_api(self):
        for url in ['https://gh-proxy.com/https://api.github.com/x', 'http://api.github.com/x',
                    'https://api.github.com.evil/x', 'https://user@api.github.com/x',
                    'https://api.github.com:444/x']:
            with self.subTest(url=url), patch.dict(os.environ, {'GITHUB_TOKEN': 'DUMMY'}), patch.object(b, 'open_url') as opened:
                with self.assertRaises(ValueError):
                    b.gh_json(url)
                opened.assert_not_called()

    def test_api_no_proxy_on_failure(self):
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'DUMMY'}), patch.object(b, 'open_url', side_effect=OSError('offline')) as opened:
            with self.assertRaises(OSError):
                b.gh_json('https://api.github.com/repos/example/example/releases')
            self.assertEqual(opened.call_count, 1)
            self.assertEqual(opened.call_args.args[0].get_header('Authorization'), 'Bearer DUMMY')

    def test_authenticated_redirects_refused(self):
        req = urllib.request.Request('https://api.github.com/x', headers={'Authorization': 'Bearer DUMMY'})
        for url in ['https://api.github.com/y', 'https://evil.example/y', 'http://api.github.com/y']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                b.SafeRedirect().redirect_request(req, None, 302, 'found', {}, url)

    def test_unsigned_redirect_strips_cookie(self):
        req = urllib.request.Request('https://github.com/x', headers={'Cookie': 'dummy'})
        new = b.SafeRedirect().redirect_request(req, None, 302, 'found', {}, 'https://release-assets.githubusercontent.com/y')
        self.assertFalse(new.has_header('Cookie'))

    def test_range_success(self):
        with patch.object(b, 'open_url', return_value=Response(b'abc', Content_Range='bytes 2-4/10')):
            self.assertEqual(b.fetch_ranged('https://github.com/a', 2, 4), b'abc')

    def test_probe_falls_back_to_the_api_asset_when_download_route_fails(self):
        # 2026-11-09 实测：releases/download 整段 504，同一时刻 API 资源端点仍能
        # 302 到可用 CDN。兜底必须只在瞬时故障时启用，且只解析一次签名地址。
        calls = []
        def resolve(api_url):
            calls.append(api_url)
            return 'https://release-assets.githubusercontent.com/x'
        gate = urllib.error.HTTPError('https://github.com/x', 504, 'gateway timeout', None, None)
        tried = []
        def fake_ranged(url, start, end):
            tried.append(url)
            if url.startswith('https://github.com/'):
                raise gate
            return b'ok'
        source = b._ProbeTransport('https://github.com/x', 'https://api.github.com/repos/o/r/releases/assets/1', resolve=resolve)
        with patch.object(b, 'remote_total', side_effect=gate),              patch.object(b, 'fetch_ranged', side_effect=fake_ranged):
            self.assertEqual(source.ranged(0, 1), b'ok')
            self.assertEqual(source.ranged(2, 3), b'ok')
        self.assertEqual(len(calls), 1)
        self.assertEqual(tried[-1], 'https://release-assets.githubusercontent.com/x')

    def test_probe_does_not_fall_back_on_contract_errors(self):
        def resolve(api_url):
            raise AssertionError('must not resolve')
        source = b._ProbeTransport('https://github.com/x', 'https://api.github.com/repos/o/r/releases/assets/1', resolve=resolve)
        with patch.object(b, 'fetch_ranged', side_effect=ValueError('Server did not honor byte range')):
            with self.assertRaises(ValueError):
                source.ranged(0, 1)

    def test_probe_without_api_url_keeps_failing(self):
        gate = urllib.error.HTTPError('https://github.com/x', 504, 'gateway timeout', None, None)
        source = b._ProbeTransport('https://github.com/x')
        with patch.object(b, 'remote_total', side_effect=gate):
            with self.assertRaises(urllib.error.HTTPError):
                source.total()

    def test_signed_asset_url_rejects_non_api_hosts(self):
        with self.assertRaises(ValueError):
            b.signed_asset_url('https://example.test/releases/assets/1')

    def test_transient_failures_are_retried(self):
        # 2026-11-09 实测：Release 资源刚上传后部分边缘节点返回 504，
        # 探测失败会让该应用退回上一次的数据。重试必须能吃掉这种抖动。
        calls = []
        def flaky():
            calls.append(1)
            if len(calls) < 3:
                raise urllib.error.HTTPError('https://github.com/x', 504, 'gateway timeout', None, None)
            return b'ok'
        slept = []
        self.assertEqual(b.retry_transient(flaky, sleep=slept.append), b'ok')
        self.assertEqual(len(calls), 3)
        self.assertEqual(slept, [5, 15])

    def test_contract_failures_are_not_retried(self):
        calls = []
        def broken():
            calls.append(1)
            raise ValueError('Server did not honor byte range')
        with self.assertRaises(ValueError):
            b.retry_transient(broken, sleep=lambda _s: None)
        self.assertEqual(len(calls), 1)

    def test_retries_give_up_and_raise_the_last_error(self):
        calls = []
        def always():
            calls.append(1)
            raise urllib.error.HTTPError('https://github.com/x', 503, 'unavailable', None, None)
        with self.assertRaises(urllib.error.HTTPError):
            b.retry_transient(always, attempts=3, sleep=lambda _s: None)
        self.assertEqual(len(calls), 3)

    def test_range_rejects_wrong_status_bounds_and_body(self):
        responses = [Response(b'abc', status=200, Content_Range='bytes 2-4/10'),
                     Response(b'abc', Content_Range='bytes 0-2/10'),
                     Response(b'abc', Content_Range='bytes 2-4/*'),
                     Response(b'abc', Content_Range='bytes 2-4/4'),
                     Response(b'ab', Content_Range='bytes 2-4/10'),
                     Response(b'abcd', Content_Range='bytes 2-4/10'),
                     Response(b'abc', Content_Range='bytes 2-4/10', Content_Encoding='gzip'),
                     Response(b'abc', Content_Range=f'bytes 2-4/{b.MAX_IPA+1}')]
        for response in responses:
            with self.subTest(response=response.headers), patch.object(b, 'open_url', return_value=response), self.assertRaises(ValueError):
                b.fetch('https://github.com/a', 2, 4)

    def test_range_request_bound(self):
        with patch.object(b, 'open_url') as opened:
            for start, end in [(-1, 1), (2, 1), (0, b.MAX_RESPONSE), (b.MAX_IPA, b.MAX_IPA)]:
                with self.assertRaises(ValueError):
                    b.fetch('https://github.com/a', start, end)
            opened.assert_not_called()

    def test_json_size_bound(self):
        with patch.object(b, 'MAX_RESPONSE', 3), patch.object(b, 'open_url', return_value=Response(b'[12345]', status=200)), self.assertRaises(ValueError):
            b.gh_json('https://api.github.com/x')

    def test_cnb_host_and_redirect_boundary(self):
        for url in ['http://api.cnb.cool/x', 'https://other.example/x', 'https://x@api.cnb.cool/x']:
            with self.assertRaises(ValueError):
                cnb._api('POST', url, 'DUMMY')
        with self.assertRaises(ValueError):
            cnb.NoAuthRedirect().redirect_request(None, None, 302, '', {}, 'https://evil.example')

    def test_cnb_upload_no_http(self):
        with tempfile.NamedTemporaryFile() as f, self.assertRaises(ValueError):
            cnb._put_file('http://example.com/upload', f.name)


class ArchiveTests(unittest.TestCase):
    def archive(self, compression=zipfile.ZIP_DEFLATED, value=None):
        out = io.BytesIO()
        value = value if value is not None else {'CFBundleIdentifier': 'test.app', 'CFBundleShortVersionString': '1.0',
                     'CFBundleVersion': '1', 'MinimumOSVersion': '15.0'}
        with zipfile.ZipFile(out, 'w', compression=compression) as z:
            z.writestr('Payload/Test.app/Info.plist', plistlib.dumps(value))
        return out.getvalue()

    def probe(self, data):
        with patch.object(b, 'remote_total', return_value=len(data)), patch.object(b, 'fetch_ranged', side_effect=lambda url,start,end: data[start:end+1]):
            return b.probe_ipa('https://github.com/a')

    def test_real_zip_stored_and_deflate(self):
        for method in [zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED]:
            self.assertEqual(self.probe(self.archive(method))['bundleIdentifier'], 'test.app')

    def test_required_plist_values(self):
        with self.assertRaises(ValueError):
            self.probe(self.archive(value={'CFBundleIdentifier': ''}))

    def test_truncated_eocd(self):
        with self.assertRaises((ValueError, RuntimeError)):
            self.probe(self.archive()[:-5])

    def test_central_directory_size_bounds(self):
        data = bytearray(self.archive())
        struct.pack_into('<I', data, data.rfind(b'PK\x05\x06')+12, b.MAX_RESPONSE+1)
        with self.assertRaises(ValueError):
            self.probe(bytes(data))

    def test_crc_rejected(self):
        data = bytearray(self.archive())
        pos = data.find(b'PK\x01\x02')
        struct.pack_into('<I', data, pos+16, 0)
        with self.assertRaises(ValueError):
            self.probe(bytes(data))

    def test_unsupported_compression(self):
        with self.assertRaises(ValueError):
            b.inflate_plist(b'abc', 99, 3)

    def test_decompression_bomb(self):
        raw = b'A' * (b.MAX_PLIST + 1)
        encoder = zlib.compressobj(wbits=-15)
        comp = encoder.compress(raw) + encoder.flush()
        with self.assertRaises(ValueError):
            b.inflate_plist(comp, 8, b.MAX_PLIST)

    def test_compressed_size_mismatch(self):
        with self.assertRaises(ValueError):
            b.inflate_plist(b'abc', 0, 4)


class CacheAndOrderingTests(unittest.TestCase):
    def test_asset_identity_invalidation(self):
        info = {'bundleIdentifier': 'test.app', 'size': 100}
        asset = {'id': 1, 'updated_at': '2026-10-01T01:00:00Z', 'size': 100, 'digest': 'sha256:abc'}
        with tempfile.TemporaryDirectory() as tmp, patch.object(b, 'CACHE_DIR', tmp), patch.object(b, 'probe_ipa', return_value=info) as probe:
            b._save('probes.json', {'https://github.com/a': info})
            b.probe_cached('https://github.com/a', asset=asset)
            b.probe_cached('https://github.com/a', asset=asset)
            self.assertEqual(probe.call_count, 1)
            for field, value in [('id', 2), ('updated_at', '2026-10-02T01:00:00Z'), ('digest', 'sha256:xyz')]:
                changed = dict(asset, **{field: value})
                b.probe_cached('https://github.com/a', asset=changed)
            self.assertEqual(probe.call_count, 4)
            b.probe_cached('https://github.com/a', force=True, asset=changed)
            self.assertEqual(probe.call_count, 5)

    def test_size_mismatch_not_cached(self):
        with patch.object(b, '_load', return_value={}), patch.object(b, '_save') as save, patch.object(b, 'probe_ipa', return_value={'size': 99}), self.assertRaises(ValueError):
            b.probe_cached('https://github.com/a', asset={'size': 100})
        save.assert_not_called()

    def test_missing_identity_never_reused(self):
        with patch.object(b, '_load', return_value={}), patch.object(b, '_save') as save, patch.object(b, 'probe_ipa', return_value={'size': 100}) as probe:
            b.probe_cached('https://github.com/a')
            b.probe_cached('https://github.com/a')
            self.assertEqual(probe.call_count, 2)
            save.assert_not_called()

    def test_full_timestamp_and_build_sort(self):
        early = {'version': '1', 'date': '2026-10-01', 'publishedAt': '2026-10-01T01:00:00Z', 'buildVersion': '99'}
        late = dict(early, publishedAt='2026-10-01T02:00:00Z', buildVersion='2')
        self.assertEqual(b.sort_versions([early, late]), [late, early])
        self.assertEqual(b.sort_versions([dict(early, buildVersion='2'), early])[0], early)

    def test_collect_sorts_api_records(self):
        asset = {'name': 'a.ipa'}
        old = {'published_at': '2026-01-01T00:00:00Z', 'assets': [asset]}
        new = dict(old, published_at='2026-02-01T00:00:00Z')
        stable, _ = b.collect([old, new], {'asset': lambda _: True}, 1)
        self.assertEqual(stable[0][0], new)

    def test_release_cache_preserves_identity_timestamp(self):
        r = {'tag': 'v1', 'pre': False, 'draft': False, 'date': '2026-10-01',
             'published_at': '2026-10-01T12:34:56Z', 'ipas': [{'name': 'a.ipa', 'size': 100, 'url': 'https://github.com/a',
             'id': 1, 'updated_at': '2026-10-02T12:00:00Z', 'digest': 'sha256:x'}]}
        converted = b.normalize_cached(r)
        self.assertEqual(converted['published_at'], r['published_at'])
        self.assertEqual(converted['assets'][0]['id'], 1)


class SchemaTests(unittest.TestCase):
    def setUp(self):
        stable = {'version': '6.3.0', 'buildVersion': '6.3.99', 'buildNumber': '6.3.99', 'date': '2026-10-13',
                  'downloadURL': 'https://github.com/test/app/releases/download/v6.3.0/app.ipa', 'size': 100, 'minOSVersion': '15.0', 'releaseTag': 'v6.3.0'}
        beta = dict(stable, buildVersion='6.3.31', buildNumber='6.3.31', date='2026-10-09', releaseTag='v6.3.0-beta01',
                    downloadURL='https://github.com/test/app/releases/download/v6.3.0-beta01/app.ipa')
        app = {'name': 'Test', 'bundleIdentifier': 'test.app', 'developerName': 'Test', 'localizedDescription': 'Test app',
               'iconURL': 'https://github.com/test.png', 'tintColor': '#123456', 'category': 'books',
               'releaseChannels': [{'track': 'stable', 'releases': [stable]}, {'track': 'nightly', 'releases': [beta]}],
               'versions': [copy.deepcopy(stable), copy.deepcopy(beta)]}
        self.source = {'name': 'Test', 'identifier': 'test.source', 'apps': [app]}

    def test_current_source_valid(self):
        source = json.loads((Path(__file__).resolve().parents[1] / 'apps.json').read_text())
        self.assertEqual(v.validate(source, 9), [])

    def test_required_release_fields(self):
        for field in ['version', 'minOSVersion', 'downloadURL']:
            for value in [None, '', 3, [], {}]:
                with self.subTest(field=field, value=value):
                    source = copy.deepcopy(self.source)
                    source['apps'][0]['releaseChannels'][0]['releases'][0][field] = value
                    self.assertTrue(v.validate(source))

    def test_dates_urls_size_and_tracks(self):
        for field, value in [('date', '2026-02-30'), ('downloadURL', 'https://'), ('downloadURL', 'https://x@evil.example/a'),
                             ('downloadURL', 'http://github.com/a'), ('size', True), ('size', 0), ('size', '10')]:
            with self.subTest(field=field, value=value):
                source = copy.deepcopy(self.source)
                source['apps'][0]['versions'][0][field] = value
                self.assertTrue(v.validate(source))
        self.source['apps'][0]['releaseChannels'].append(copy.deepcopy(self.source['apps'][0]['releaseChannels'][0]))
        self.assertTrue(v.validate(self.source))

    def test_payload_mismatch(self):
        for field, value in [('size', 123), ('buildVersion', '999'), ('downloadURL', 'https://example.com/other.ipa')]:
            source = copy.deepcopy(self.source)
            source['apps'][0]['versions'][0][field] = value
            self.assertTrue(v.validate(source))

    def test_malformed_containers_fail_cleanly(self):
        for source in [None, [], {'apps': {}}, {'apps': [None]}, {'apps': [{'releaseChannels': [None], 'versions': [None]}]}]:
            self.assertTrue(v.validate(source))

    def test_stable_same_version_as_beta_no_badge(self):
        app = self.source['apps'][0]
        self.assertEqual(app['versions'][0]['version'], app['releaseChannels'][1]['releases'][0]['version'])
        self.assertNotEqual(b.release_identity(app['versions'][0]), b.release_identity(app['releaseChannels'][1]['releases'][0]))
        self.assertFalse(app.get('beta'))
        app['beta'] = True
        self.assertTrue(v.validate(self.source))

    def test_beta_first_gets_badge(self):
        app = self.source['apps'][0]
        beta = app['releaseChannels'][1]['releases'][0]
        beta['date'] = '2099-01-01'
        app['versions'] = b.sort_versions([copy.deepcopy(r) for c in app['releaseChannels'] for r in c['releases']])
        app['beta'] = True
        self.assertEqual(v.validate(self.source), [])


if __name__ == '__main__':
    unittest.main()
