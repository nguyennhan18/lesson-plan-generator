"""Preserve provenance in an Office custom XML part, without granting trust on import."""
import json
from lxml import etree
from lessonai.services.lesson_quality import plan_snapshot
from lessonai.services.visual_requirements import fingerprint

NAMESPACE = 'urn:lessonai:provenance:v1'
PART_NAME = 'customXml/lessonai-provenance.xml'


def plan_provenance(plan):
    data = plan_snapshot(plan)
    return {'artifact': 'lesson_plan', 'content_fingerprint': fingerprint(data),
            'generation_metadata': data.get('generation_metadata'),
            'approved_outline': data.get('approved_outline')}


def attach_docx_provenance(doc, provenance):
    from docx.opc.part import Part
    from docx.opc.packuri import PackURI
    from docx.opc.constants import RELATIONSHIP_TYPE as RT
    root = etree.Element(f'{{{NAMESPACE}}}provenance')
    root.text = json.dumps(provenance, ensure_ascii=False, sort_keys=True)
    part = Part(PackURI('/' + PART_NAME), 'application/xml', etree.tostring(root, encoding='UTF-8', xml_declaration=True), doc.part.package)
    doc.part.relate_to(part, RT.CUSTOM_XML)


def read_office_provenance(archive):
    if PART_NAME not in archive.namelist():
        return None
    root = etree.fromstring(archive.read(PART_NAME), etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False))
    if root.tag != f'{{{NAMESPACE}}}provenance':
        raise ValueError('Metadata Office không đúng cấu trúc')
    value = json.loads(root.text or '{}')
    if not isinstance(value, dict):
        raise ValueError('Metadata Office không hợp lệ')
    return {'data': value, 'status': 'unverified_import'}
