"""DNS pinning transport and SSRF hardening tests."""
from __future__ import annotations

import io
import socket
import ssl
import unittest
from unittest import mock
import urllib.parse

from respected_brain.maintenance.ingestion.url_safety import (
    is_private_or_reserved_ip,
    resolve_safe_addresses,
    validate_safe_url,
)
from respected_brain.maintenance.ingestion.defuddle import (
    fetch_and_clean_url,
    safe_fetch_url,
)
from pathlib import Path
from respected_brain.maintenance.ingestion.defuddle import _DeadlineReader
from respected_brain.providers.runner import Invocation
from respected_brain.providers.runner import _run_process_tree
import os
import subprocess
import sys
import tempfile
import threading
import time


class DnsPinningAndTransportSecurityTest(unittest.TestCase):
    def test_mixed_ipv4_ipv6_dns_response_is_rejected(self):
        """When DNS returns a mixed set of public IPv4 and private/loopback IPv6, it must fail-closed."""
        fake_addrinfo = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80)),
            (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("::1", 80, 0, 0)),
        ]
        with mock.patch("socket.getaddrinfo", return_value=fake_addrinfo):
            safe, ips, reason = resolve_safe_addresses("example.com", 80)
            self.assertFalse(safe)
            self.assertEqual(ips, [])
            self.assertIn("özel/yerel", reason.lower())

    def test_dns_rebinding_pins_verified_ip_and_does_not_re_resolve(self):
        """DNS resolution occurs once; the transport connects strictly to the pinned IP without re-querying DNS."""
        calls = []

        def mock_getaddrinfo(host, port, *args, **kwargs):
            calls.append(host)
            if len(calls) == 1:
                return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]
            # If transport re-resolves DNS, return private IP to simulate rebinding attack
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port))]

        connected_addresses = []

        def mock_create_connection(address, timeout=None, *args, **kwargs):
            connected_addresses.append(address)
            # Create a mock socket
            sock = mock.MagicMock(spec=socket.socket)
            sock.makefile.return_value = io.BytesIO(b"HTTP/1.1 200 OK\r\nContent-Length: 13\r\n\r\nHello World\n")
            return sock

        with mock.patch("socket.getaddrinfo", side_effect=mock_getaddrinfo), \
             mock.patch("socket.create_connection", side_effect=mock_create_connection):
            ok, content, headers = safe_fetch_url("http://example.com/test", timeout=5)
            self.assertTrue(ok)
            self.assertEqual(content, b"Hello World\n")
            # Must connect directly to 93.184.216.34 and never to 127.0.0.1
            self.assertEqual(connected_addresses, [("93.184.216.34", 80)])
            # getaddrinfo must have been called exactly once by the safe resolver
            self.assertEqual(len(calls), 1)

    def test_redirect_to_metadata_or_private_is_rejected(self):
        """Redirect to 169.254.169.254 or private IP must be aborted immediately."""
        def mock_getaddrinfo(host, port, *args, **kwargs):
            if host == "public-site.com":
                return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", port))]

        def mock_create_connection(address, timeout=None, *args, **kwargs):
            sock = mock.MagicMock(spec=socket.socket)
            # Return redirect to cloud metadata
            sock.makefile.return_value = io.BytesIO(
                b"HTTP/1.1 302 Found\r\nLocation: http://169.254.169.254/latest/meta-data/\r\nContent-Length: 0\r\n\r\n"
            )
            return sock

        with mock.patch("socket.getaddrinfo", side_effect=mock_getaddrinfo), \
             mock.patch("socket.create_connection", side_effect=mock_create_connection):
            ok, err_or_content, _ = safe_fetch_url("http://public-site.com/redirect", timeout=5)
            self.assertFalse(ok)
            self.assertIn("özel/yerel", err_or_content.lower())

    def test_tls_hostname_and_sni_and_host_header_preserved(self):
        """HTTPS transport connects to pinned IP but validates TLS against actual URL hostname."""
        wrapped_hostnames = []
        sent_requests = []

        class MockSSLSocket:
            def __init__(self, raw_sock):
                self.raw_sock = raw_sock
            def sendall(self, data):
                sent_requests.append(data)
            def send(self, data):
                sent_requests.append(data)
                return len(data)
            def makefile(self, *args, **kwargs):
                return io.BytesIO(b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nValid")
            def close(self):
                pass

        mock_context = mock.MagicMock(spec=ssl.SSLContext)
        mock_context.check_hostname = True
        mock_context.verify_mode = ssl.CERT_REQUIRED

        def mock_wrap_socket(sock, server_hostname=None):
            wrapped_hostnames.append(server_hostname)
            return MockSSLSocket(sock)

        mock_context.wrap_socket.side_effect = mock_wrap_socket

        with mock.patch("socket.getaddrinfo", return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]), \
             mock.patch("socket.create_connection", return_value=mock.MagicMock(spec=socket.socket)), \
             mock.patch("ssl.create_default_context", return_value=mock_context):
            ok, content, _ = safe_fetch_url("https://secure.example.com/api", timeout=5, ssl_context=mock_context)
            self.assertTrue(ok)
            self.assertEqual(content, b"Valid")
            # Verify server_hostname (SNI) is the actual URL hostname
            self.assertEqual(wrapped_hostnames, ["secure.example.com"])

    def test_environment_proxy_cannot_bypass_safe_transport(self):
        """Setting HTTP_PROXY or HTTPS_PROXY in environment must not alter direct pinned connection."""
        connected_addresses = []

        def mock_create_connection(address, timeout=None, *args, **kwargs):
            connected_addresses.append(address)
            sock = mock.MagicMock(spec=socket.socket)
            sock.makefile.return_value = io.BytesIO(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK")
            return sock

        with mock.patch.dict("os.environ", {"HTTP_PROXY": "http://evil-proxy:8080", "HTTPS_PROXY": "http://evil-proxy:8080"}), \
             mock.patch("socket.getaddrinfo", return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80))]), \
             mock.patch("socket.create_connection", side_effect=mock_create_connection):
            ok, content, _ = safe_fetch_url("http://example.com/test", timeout=5)
            self.assertTrue(ok)
            # The connection went directly to the verified pinned IP, completely ignoring the proxy
            self.assertEqual(connected_addresses, [("93.184.216.34", 80)])

    def test_excessive_redirects_fail_closed(self):
        """Redirect loop or exceeding max_redirects must fail-closed."""
        def mock_create_connection(address, timeout=None, *args, **kwargs):
            sock = mock.MagicMock(spec=socket.socket)
            sock.makefile.return_value = io.BytesIO(
                b"HTTP/1.1 302 Found\r\nLocation: http://example.com/loop\r\nContent-Length: 0\r\n\r\n"
            )
            return sock

        with mock.patch("socket.getaddrinfo", return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80))]), \
             mock.patch("socket.create_connection", side_effect=mock_create_connection):
            ok, err, _ = safe_fetch_url("http://example.com/loop", timeout=5, max_redirects=3)
            self.assertFalse(ok)
            self.assertIn("yönlendirme", err.lower())

    def test_byte_limit_enforced_during_stream_read(self):
        """Responses exceeding max_bytes must abort and not buffer oversized content."""
        def mock_create_connection(address, timeout=None, *args, **kwargs):
            sock = mock.MagicMock(spec=socket.socket)
            large_body = b"A" * 2000
            sock.makefile.return_value = io.BytesIO(
                b"HTTP/1.1 200 OK\r\nContent-Length: 2000\r\n\r\n" + large_body
            )
            return sock

        with mock.patch("socket.getaddrinfo", return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80))]), \
             mock.patch("socket.create_connection", side_effect=mock_create_connection):
            ok, err, _ = safe_fetch_url("http://example.com/large", timeout=5, max_bytes=500)
            self.assertFalse(ok)
            self.assertIn("boyut", err.lower())

    def test_slow_stream_overall_deadline_enforced(self):
        """A slow streaming response whose cumulative read duration exceeds overall deadline must abort."""
        elapsed = [0.0]

        class SlowResponse:
            status = 200
            def __init__(self, sock):
                self.chunks = [b"chunk1", b"chunk2", b"chunk3", b""]
            def begin(self):
                pass
            def getheaders(self):
                return []
            def read(self, size):
                elapsed[0] += 4.0
                return self.chunks.pop(0)

        with mock.patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("93.184.216.34", 80))]), \
             mock.patch("socket.create_connection", return_value=mock.MagicMock()), \
             mock.patch("http.client.HTTPResponse", SlowResponse), \
             mock.patch("time.monotonic", side_effect=lambda: elapsed[0]):
            success, err, _ = safe_fetch_url("http://example.com/slow", timeout=5)
            self.assertFalse(success)
            self.assertIn("zaman aşımı", err.lower())

    def test_insecure_caller_ssl_context_rejected(self):
        """Caller-supplied SSL context with CERT_NONE or check_hostname=False must be rejected fail-closed."""
        bad_context = mock.MagicMock(spec=ssl.SSLContext)
        bad_context.verify_mode = ssl.CERT_NONE
        bad_context.check_hostname = False

        with mock.patch("socket.getaddrinfo", return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]), \
             mock.patch("socket.create_connection", return_value=mock.MagicMock()):
            ok, err, _ = safe_fetch_url("https://example.com/api", timeout=5, ssl_context=bad_context)
            self.assertFalse(ok)
            self.assertIn("güvenli olmayan ssl", err.lower())

    def test_host_header_ipv6_and_custom_port(self):
        """IPv6 literal addresses must be formatted as [addr] in Host header, and non-80/443 ports must be rejected."""
        # Non-standard port 8443 must be rejected by URL safety
        ok_unsafe, err_unsafe, _ = safe_fetch_url("https://[2606:2800:220:1:248:1893:25c8:1946]:8443/test", timeout=5)
        self.assertFalse(ok_unsafe)
        self.assertIn("güvensiz port", err_unsafe.lower())

        # Standard port 443 with IPv6 literal must produce [addr] Host header
        sent_data = []

        class MockSocket:
            def sendall(self, data):
                sent_data.append(data)
            def settimeout(self, timeout):
                pass
            def close(self):
                pass

        class MockResponse:
            status = 200
            def begin(self):
                pass
            def getheaders(self):
                return []
            def read(self, size):
                return b""

        with mock.patch("socket.getaddrinfo", return_value=[(socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("2606:2800:220:1:248:1893:25c8:1946", 443, 0, 0))]), \
             mock.patch("socket.create_connection", return_value=MockSocket()), \
             mock.patch("ssl.create_default_context", return_value=mock.MagicMock(wrap_socket=lambda s, server_hostname: s)), \
             mock.patch("http.client.HTTPResponse", lambda s: MockResponse()):
            ok, _, _ = safe_fetch_url("https://[2606:2800:220:1:248:1893:25c8:1946]/test", timeout=5)
            self.assertTrue(ok)
            raw_req = b"".join(sent_data).decode("iso-8859-1")
            self.assertIn("Host: [2606:2800:220:1:248:1893:25c8:1946]", raw_req)


class HttpDeadlineTest(unittest.TestCase):
    def test_status_and_chunk_lines_stop_near_deadline(self):
        for prefix in (
            b'HTTP/1.1 2',
            b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n1',
            b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n1\r\nA\r\n0\r\nX',
        ):
            with self.subTest(prefix=prefix):
                server, client = socket.socketpair(); stop = threading.Event()
                def serve():
                    try:
                        server.sendall(prefix)
                        while not stop.wait(.01): server.sendall(b' ')
                    except OSError: pass
                    finally: server.close()
                threading.Thread(target=serve,daemon=True).start(); started = time.monotonic()
                addresses = [(socket.AF_INET,socket.SOCK_STREAM,6,'',('93.184.216.34',80))]
                outcomes = []
                def fetch():
                    with mock.patch('socket.create_connection',return_value=client), mock.patch('socket.getaddrinfo',return_value=addresses):
                        outcomes.append(safe_fetch_url('http://example.test/x',timeout=.05))
                worker = threading.Thread(target=fetch,daemon=True); worker.start(); worker.join(.25)
                completed = not worker.is_alive(); stop.set(); client.close(); worker.join(.25)
                self.assertTrue(completed,'transport exceeded watchdog after stale socket timeout renewal')
                ok, result, _ = outcomes[0]; elapsed = time.monotonic()-started
                self.assertFalse(ok); self.assertLessEqual(elapsed,.12,result)

    def test_underlying_completion_after_deadline_is_rejected(self):
        class SlowStream:
            def readinto(self, buffer):
                time.sleep(0.04)
                buffer[0] = 1
                return 1
        reader = _DeadlineReader(SlowStream(), time.monotonic() + 0.01)
        with self.assertRaises(TimeoutError):
            reader.readinto(bytearray(1))


class ResolverCapacityTest(unittest.TestCase):
    def test_bounded_daemon_workers(self):
        release = threading.Event()
        def block(*args,**kwargs):
            release.wait(2); return [(socket.AF_INET,socket.SOCK_STREAM,6,'',('93.184.216.34',80))]
        with mock.patch('socket.getaddrinfo',side_effect=block):
            threads = [threading.Thread(target=lambda i=i:safe_fetch_url(f'http://h{i}.example.test/',timeout=.12),daemon=True) for i in range(5)]
            for thread in threads: thread.start()
            time.sleep(.08); workers = [item for item in threading.enumerate() if item.name.startswith('respected-brain-resolver')]
            self.assertEqual(len(workers),2); release.set()
            for thread in threads: thread.join(1)

    def test_slow_resolver_does_not_block_process_shutdown(self):
        code = (
            "import socket,sys,threading,time\n"
            "entered=threading.Event()\n"
            "def blocked(*args,**kwargs):\n"
            "    entered.set();time.sleep(5);return []\n"
            "socket.getaddrinfo=blocked\n"
            "from respected_brain.maintenance.ingestion.defuddle import safe_fetch_url\n"
            "threading.Thread(target=lambda:safe_fetch_url('http://slow.example.test/',timeout=.05),daemon=True).start()\n"
            "assert entered.wait(5),'resolver did not start'\n"
            "print('resolver-blocked',flush=True)\n"
            "sys.stdin.readline()\n"
            "sys.exit(0)\n"
        )
        process = subprocess.Popen([sys.executable, "-c", code], cwd=Path.cwd(),
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            ready = []
            reader = threading.Thread(target=lambda: ready.append(process.stdout.readline()), daemon=True)
            reader.start()
            reader.join(10)
            self.assertFalse(reader.is_alive(), 'resolver readiness timed out')
            self.assertEqual(ready, ['resolver-blocked\n'])
            # Measure exit with DNS blocked; interpreter/import startup is outside this contract.
            started = time.monotonic()
            output, errors = process.communicate(input='\n', timeout=2)
            self.assertEqual(process.returncode, 0, errors)
            self.assertLess(time.monotonic() - started, 1.5)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
            for stream in (process.stdin, process.stdout, process.stderr):
                stream.close()

    def test_nonzero_exit_is_returned_without_hiding_output(self):
        invocation = Invocation(
            [sys.executable, "-c", "import sys;print('partial');sys.stderr.write('failed');raise SystemExit(7)"],
            None,
        )
        result = _run_process_tree(invocation, cwd=Path.cwd(), env=os.environ.copy(), timeout=1)
        self.assertEqual(result.returncode, 7)
        self.assertEqual(result.stdout.strip(), "partial")
        self.assertEqual(result.stderr.strip(), "failed")

    def test_timeout_contains_detached_descendant_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            child_pid_file = root / "child.pid"
            parent_script = root / "spawn_detached.py"
            parent_script.write_text(
                "import subprocess,sys,time\n"
                "from pathlib import Path\n"
                "flags=(subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.DETACHED_PROCESS) if hasattr(subprocess,'DETACHED_PROCESS') else 0\n"
                "kwargs={'creationflags':flags} if flags else {'start_new_session':True}\n"
                "child=subprocess.Popen([sys.executable,'-c','import time\\nwhile True: time.sleep(.05)'],**kwargs)\n"
                "Path(sys.argv[1]).write_text(str(child.pid),encoding='ascii')\n"
                "time.sleep(5)\n",
                encoding="utf-8",
            )
            invocation = Invocation(
                [sys.executable, str(parent_script), str(child_pid_file)],
                None,
                windows_executable=os.name == "nt",
            )
            started = time.monotonic()
            with self.assertRaises(subprocess.TimeoutExpired):
                _run_process_tree(invocation, cwd=root, env=os.environ.copy(), timeout=1.0)
            self.assertLess(time.monotonic() - started, 2.0)
            self.assertTrue(child_pid_file.is_file())
            child_pid = int(child_pid_file.read_text(encoding="ascii"))
            deadline = time.monotonic() + 0.8
            while time.monotonic() < deadline and self._process_alive(child_pid):
                time.sleep(0.02)
            self.assertFalse(self._process_alive(child_pid), f"detached child survived: {child_pid}")

    @staticmethod
    def _process_alive(pid: int) -> bool:
        if os.name == "nt":
            import ctypes
            process = ctypes.windll.kernel32.OpenProcess(0x00100000, False, pid)
            if not process:
                return False
            try:
                return ctypes.windll.kernel32.WaitForSingleObject(process, 0) == 258
            finally:
                ctypes.windll.kernel32.CloseHandle(process)
        try:
            status = Path("/proc") / str(pid) / "stat"
            if status.is_file():
                fields = status.read_text(encoding="utf-8", errors="replace").rsplit(")", 1)[-1].split()
                return bool(fields) and fields[0] != "Z"
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False


class LateByteHttpDeadlineTest(unittest.TestCase):
    def test_late_byte_then_idle_does_not_wait_for_stale_socket_timeout(self) -> None:
        prefixes = (
            b'HTTP/1.1 2',
            b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n1',
            b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n1\r\nA\r\n0\r\nX',
        )
        for prefix in prefixes:
            with self.subTest(prefix=prefix):
                server, client = socket.socketpair()
                stop = threading.Event()

                def serve() -> None:
                    try:
                        server.sendall(prefix)
                        if not stop.wait(0.06):
                            server.sendall(b' ')
                        stop.wait(0.25)
                    except OSError:
                        pass
                    finally:
                        server.close()

                thread = threading.Thread(target=serve, daemon=True)
                thread.start()
                started = time.monotonic()
                addresses = [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 80))]
                outcome: list[tuple[bool, object, dict]] = []

                def fetch() -> None:
                    with mock.patch('socket.create_connection', return_value=client), \
                         mock.patch('socket.getaddrinfo', return_value=addresses):
                        outcome.append(safe_fetch_url('http://example.test/x', timeout=0.1))

                worker = threading.Thread(target=fetch, daemon=True)
                worker.start()
                worker.join(0.25)
                completed = not worker.is_alive()
                elapsed = time.monotonic() - started
                stop.set()
                client.close()
                server.close()
                thread.join(0.25)
                self.assertTrue(completed, 'request exceeded its watchdog')
                self.assertFalse(outcome[0][0])
                self.assertLessEqual(elapsed, 0.15, outcome[0])


if __name__ == "__main__":
    unittest.main()
