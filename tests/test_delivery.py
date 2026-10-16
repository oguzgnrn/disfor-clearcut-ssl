import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from verify_package import verify

class DeliveryIntegrity(unittest.TestCase):
    def archive(self, folder, payload=b'actual', name='Orman_SSL/example.txt', extra=None):
        path=Path(folder)/'test.zip'
        manifest=[dict(path='example.txt',bytes=6,sha256=hashlib.sha256(b'actual').hexdigest())]
        with zipfile.ZipFile(path,'w') as z:
            z.writestr(name,payload)
            z.writestr('Orman_SSL/PACKAGE_MANIFEST.json',json.dumps(manifest))
            if extra: z.writestr(extra,b'unlisted')
        return path
    def test_valid_package(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(verify(self.archive(d))['files'],1)
    def test_modified_payload_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,'mismatch'):
                verify(self.archive(d,payload=b'edited'))
    def test_path_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,'Unsafe'):
                verify(self.archive(d,name='Orman_SSL/../../outside'))
    def test_unlisted_payload_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,'Unlisted'):
                verify(self.archive(d,extra='Orman_SSL/unexpected.txt'))
