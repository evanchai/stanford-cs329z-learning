import sys
import os
import tempfile
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / 'hw1').resolve()
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
sys.dont_write_bytecode = True
sys.path.insert(0, str(root))
import cs329z_hw1.llm as llm

blocked = []
def no_model(*args, **kwargs):
    blocked.append('real_lm')
    raise RuntimeError('Audit forbids real LM and subscription CLI calls')
llm._load_env = lambda: None
llm.LM.__call__ = no_model
llm.LM.__init__ = no_model

def audit(event, args):
    if event in {'socket.connect', 'socket.getaddrinfo'}:
        blocked.append('network')
        raise RuntimeError('Audit forbids network access')
sys.addaudithook(audit)

import pytest
class AuditPlugin:
    def pytest_collection_modifyitems(self, items):
        for item in items:
            if 'archive' in item.fixturenames:
                item.add_marker(pytest.mark.skip(reason='Real email archive deliberately excluded from safe export'))
    def pytest_sessionfinish(self, session):
        print('AUDIT_BLOCKED_ATTEMPTS', blocked)

report_dir = root.parent / 'reports'
report_dir.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='cs329z-audit-') as work:
    result = pytest.main([
        str(root/'tests'), '-m', 'not live', '-q', '-p', 'no:cacheprovider',
        '--ignore='+str(root/'tests/test_sim_eval.py'),
        '--basetemp='+str(Path(work)/'tests'),
        '--junitxml='+str(report_dir/'latest-offline-junit.xml'),
    ], plugins=[AuditPlugin()])
    # Report paths and hostnames are machine-specific; omit them from shareable evidence.
    import xml.etree.ElementTree as ET
    report = report_dir/'latest-offline-junit.xml'
    if report.exists():
        tree = ET.parse(report)
        for suite in tree.getroot().iter('testsuite'):
            suite.attrib.pop('hostname', None)
        for node in tree.getroot().iter('skipped'):
            node.text = 'Real email archive intentionally excluded; see README.'
        tree.write(report, encoding='unicode')
raise SystemExit(result)
