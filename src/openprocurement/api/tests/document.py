# -*- coding: utf-8 -*-
import unittest
from email.header import Header
from openprocurement.api.tests.base import BaseTenderWebTest, create_classmethod
from openprocurement.api.tests.document_test_utils import (not_found,
                                                           put_tender_document,
                                                           patch_tender_document,
                                                           create_tender_document,
                                                           create_tender_document_json_invalid,
                                                           create_tender_document_json,
                                                           put_tender_document_json)


class TenderDocumentResourceTest(BaseTenderWebTest):
    status = 'active.tendering'
    test_not_found = create_classmethod(not_found)
    test_put_tender_document = create_classmethod(put_tender_document)
    test_patch_tender_document = create_classmethod(patch_tender_document)
    test_create_tender_document = create_classmethod(create_tender_document)


class TenderDocumentWithDSResourceTest(TenderDocumentResourceTest):
    docservice = True
    test_create_tender_document_json_invalid = create_classmethod(create_tender_document_json_invalid)
    test_create_tender_document_json = create_classmethod(create_tender_document_json)
    test_put_tender_document_json = create_classmethod(put_tender_document_json)

    def test_create_tender_document_error(self):
        self.tearDownDS()
        response = self.app.post('/tenders/{}/documents'.format(self.tender_id),
                                 upload_files=[('file', u'укр.doc', 'content')],
                                 status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't upload document to document service.")
        self.setUpBadDS()
        response = self.app.post('/tenders/{}/documents'.format(self.tender_id),
                                 upload_files=[('file', u'укр.doc', 'content')],
                                 status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't upload document to document service.")



def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TenderDocumentResourceTest))
    suite.addTest(unittest.makeSuite(TenderDocumentWithDSResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
