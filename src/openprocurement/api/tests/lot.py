# -*- coding: utf-8 -*-
import unittest
from copy import deepcopy
from datetime import timedelta

from openprocurement.api.models import get_now
from openprocurement.api.tests.lot_test_utils import (create_tender_lot_invalid,
                                                      delete_tender_lot,
                                                      tender_lot_guarantee,
                                                      tender_value,
                                                      tender_features_invalid,
                                                      patch_tender_currency,
                                                      patch_tender_vat)
from openprocurement.api.tests.base import (BaseWebTest,
                                            BaseTenderWebTest,
                                            test_tender_data,
                                            test_lots,
                                            test_organization,
                                            create_classmethod)


class BaseTenderLotResourceTest(object):
    test_create_tender_lot_invalid = create_classmethod(create_tender_lot_invalid)
    test_delete_tender_lot = create_classmethod(delete_tender_lot)
    test_tender_lot_guarantee = create_classmethod(tender_lot_guarantee)
    test_patch_tender_currency = create_classmethod(patch_tender_currency)
    test_patch_tender_vat = create_classmethod(patch_tender_vat)

    def test_create_tender_lot(self):
        response = self.app.post_json('/tenders/{}/lots'.format(self.tender_id), {'data': test_lots[0]})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        lot = response.json['data']
        self.assertEqual(lot['title'], 'lot title')
        self.assertEqual(lot['description'], 'lot description')
        self.assertIn('id', lot)
        self.assertIn(lot['id'], response.headers['Location'])
        self.assertNotIn('guarantee', lot)

        response = self.app.get('/tenders/{}'.format(self.tender_id))
        self.assertNotIn('guarantee', response.json['data'])

        lot2 = deepcopy(test_lots[0])
        lot2['guarantee'] = {"amount": 100500, "currency": "USD"}
        response = self.app.post_json('/tenders/{}/lots'.format(self.tender_id), {'data': lot2})
        self.assertEqual(response.status, '201 Created')
        data = response.json['data']
        self.assertIn('guarantee', data)
        self.assertEqual(data['guarantee']['amount'], 100500)
        self.assertEqual(data['guarantee']['currency'], "USD")

        response = self.app.get('/tenders/{}'.format(self.tender_id))
        self.assertIn('guarantee', response.json['data'])
        self.assertEqual(response.json['data']['guarantee']['amount'], 100500)
        self.assertEqual(response.json['data']['guarantee']['currency'], "USD")
        self.assertNotIn('guarantee', response.json['data']['lots'][0])

        lot3 = deepcopy(test_lots[0])
        lot3['guarantee'] = {"amount": 500, "currency": "UAH"}
        response = self.app.post_json('/tenders/{}/lots'.format(self.tender_id), {'data': lot3}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'lot guarantee currency should be identical to tender guarantee currency'], u'location': u'body', u'name': u'lots'}
        ])

        lot3['guarantee'] = {"amount": 500}
        response = self.app.post_json('/tenders/{}/lots'.format(self.tender_id), {'data': lot3}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'lot guarantee currency should be identical to tender guarantee currency'], u'location': u'body', u'name': u'lots'}
        ])

        lot3['guarantee'] = {"amount": 20, "currency": "USD"}
        response = self.app.post_json('/tenders/{}/lots'.format(self.tender_id), {'data': lot3})
        self.assertEqual(response.status, '201 Created')
        data = response.json['data']
        self.assertIn('guarantee', data)
        self.assertEqual(data['guarantee']['amount'], 20)
        self.assertEqual(data['guarantee']['currency'], "USD")

        response = self.app.get('/tenders/{}'.format(self.tender_id))
        self.assertIn('guarantee', response.json['data'])
        self.assertEqual(response.json['data']['guarantee']['amount'], 100500 + 20)
        self.assertEqual(response.json['data']['guarantee']['currency'], "USD")

        response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {"data": {"guarantee": {"currency": "EUR"}}})
        self.assertEqual(response.json['data']['guarantee']['amount'], 100500 + 20)
        self.assertEqual(response.json['data']['guarantee']['currency'], "EUR")
        self.assertNotIn('guarantee', response.json['data']['lots'][0])
        self.assertEqual(response.json['data']['lots'][1]['guarantee']['amount'], 100500)
        self.assertEqual(response.json['data']['lots'][1]['guarantee']['currency'], "EUR")
        self.assertEqual(response.json['data']['lots'][2]['guarantee']['amount'], 20)
        self.assertEqual(response.json['data']['lots'][2]['guarantee']['currency'], "EUR")

        response = self.app.post_json('/tenders/{}/lots'.format(self.tender_id), {'data': lot}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'Lot id should be uniq for all lots'], u'location': u'body', u'name': u'lots'}
        ])

        self.set_status('active.tendering')

        response = self.app.post_json('/tenders/{}/lots'.format(self.tender_id), {'data': test_lots[0]}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add lot in current (active.tendering) tender status")

    def test_patch_tender_lot(self):
        response = self.app.post_json('/tenders/{}/lots'.format(self.tender_id), {'data': test_lots[0]})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        lot = response.json['data']

        response = self.app.patch_json('/tenders/{}/lots/{}'.format(self.tender_id, lot['id']), {"data": {"title": "new title"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["title"], "new title")

        response = self.app.patch_json('/tenders/{}/lots/{}'.format(self.tender_id, lot['id']), {"data": {"guarantee": {"amount": 12}}})
        self.assertEqual(response.status, '200 OK')
        self.assertIn('guarantee', response.json['data'])
        self.assertEqual(response.json['data']['guarantee']['amount'], 12)
        self.assertEqual(response.json['data']['guarantee']['currency'], 'UAH')

        response = self.app.patch_json('/tenders/{}/lots/{}'.format(self.tender_id, lot['id']), {"data": {"guarantee": {"currency": "USD"}}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.body, 'null')

        response = self.app.patch_json('/tenders/{}/lots/some_id'.format(self.tender_id), {"data": {"title": "other title"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'lot_id'}
        ])

        response = self.app.patch_json('/tenders/some_id/lots/some_id', {"data": {"title": "other title"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.get('/tenders/{}/lots/{}'.format(self.tender_id, lot['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["title"], "new title")

        self.set_status(self.status)

        response = self.app.patch_json('/tenders/{}/lots/{}'.format(self.tender_id, lot['id']), {"data": {"title": "other title"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update lot in current ({}) tender status".format(self.status))

    def test_get_tender_lot(self):
        response = self.app.post_json('/tenders/{}/lots'.format(self.tender_id), {'data': test_lots[0]})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        lot = response.json['data']

        response = self.app.get('/tenders/{}/lots/{}'.format(self.tender_id, lot['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(set(response.json['data']), set([u'id', u'date', u'title', u'description', u'minimalStep', u'value', u'status']))

        self.set_status('active.qualification')

        response = self.app.get('/tenders/{}/lots/{}'.format(self.tender_id, lot['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], lot)

        response = self.app.get('/tenders/{}/lots/some_id'.format(self.tender_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'lot_id'}
        ])

        response = self.app.get('/tenders/some_id/lots/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

    def test_get_tender_lots(self):
        response = self.app.post_json('/tenders/{}/lots'.format(self.tender_id), {'data': test_lots[0]})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        lot = response.json['data']

        response = self.app.get('/tenders/{}/lots'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(set(response.json['data'][0]), set([u'id',  u'date', u'title', u'description', u'minimalStep', u'value', u'status']))

        self.set_status('active.qualification')

        response = self.app.get('/tenders/{}/lots'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'][0], lot)

        response = self.app.get('/tenders/some_id/lots', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

class TenderLotResourceTest(BaseTenderWebTest, BaseTenderLotResourceTest):
    status = 'active.tendering'
    test_tender_data = test_tender_data

class BaseTenderLotFeatureResourceTest(object):
    test_tender_value = create_classmethod(tender_value)
    test_tender_features_invalid = create_classmethod(tender_features_invalid)

class TenderLotFeatureResourceTest(BaseTenderWebTest,
                                   BaseTenderLotFeatureResourceTest):
    initial_lots = 2 * test_lots
    test_tender_data = test_tender_data


class TenderLotBidderResourceTest(BaseTenderWebTest):
    initial_status = 'active.tendering'
    initial_lots = test_lots

    def test_create_tender_bidder_invalid(self):
        request_path = '/tenders/{}/bids'.format(self.tender_id)
        response = self.app.post_json(request_path, {'data': {'tenderers': [test_organization]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'This field is required.'], u'location': u'body', u'name': u'lotValues'}
        ])

        response = self.app.post_json(request_path, {'data': {'tenderers': [test_organization], 'lotValues': [{"value": {"amount": 500}}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [{u'relatedLot': [u'This field is required.']}], u'location': u'body', u'name': u'lotValues'}
        ])

        response = self.app.post_json(request_path, {'data': {'tenderers': [test_organization], 'lotValues': [{"value": {"amount": 500}, 'relatedLot': "0" * 32}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [{u'relatedLot': [u'relatedLot should be one of lots']}], u'location': u'body', u'name': u'lotValues'}
        ])

        response = self.app.post_json(request_path, {'data': {'tenderers': [test_organization], 'lotValues': [{"value": {"amount": 5000000}, 'relatedLot': self.initial_lots[0]['id']}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [{u'value': [u'value of bid should be less than value of lot']}], u'location': u'body', u'name': u'lotValues'}
        ])

        response = self.app.post_json(request_path, {'data': {'tenderers': [test_organization], 'lotValues': [{"value": {"amount": 500, 'valueAddedTaxIncluded': False}, 'relatedLot': self.initial_lots[0]['id']}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [{u'value': [u'valueAddedTaxIncluded of bid should be identical to valueAddedTaxIncluded of value of lot']}], u'location': u'body', u'name': u'lotValues'}
        ])

        response = self.app.post_json(request_path, {'data': {'tenderers': [test_organization], 'lotValues': [{"value": {"amount": 500, 'currency': "USD"}, 'relatedLot': self.initial_lots[0]['id']}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [{u'value': [u'currency of bid should be identical to currency of value of lot']}], u'location': u'body', u'name': u'lotValues'},
        ])

        response = self.app.post_json(request_path, {'data': {'tenderers': [test_organization], "value": {"amount": 500}, 'lotValues': [{"value": {"amount": 500}, 'relatedLot': self.initial_lots[0]['id']}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'value should be posted for each lot of bid'], u'location': u'body', u'name': u'value'}
        ])

        response = self.app.post_json(request_path, {'data': {'tenderers': test_organization, 'lotValues': [{"value": {"amount": 500}, 'relatedLot': self.initial_lots[0]['id']}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u"invalid literal for int() with base 10: 'contactPoint'", u'location': u'body', u'name': u'data'},
        ])

        response = self.app.post_json(request_path, {'data': {'tenderers': [test_organization], 'lotValues': [{"value": {"amount": 500}, 'relatedLot': self.initial_lots[0]['id']}, {"value": {"amount": 500}, 'relatedLot': self.initial_lots[0]['id']}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u"bids don't allow duplicated proposals"], u'location': u'body', u'name': u'lotValues'}
        ])

    def test_patch_tender_bidder(self):
        lot_id = self.initial_lots[0]['id']
        response = self.app.post_json('/tenders/{}/bids'.format(self.tender_id), {'data': {'tenderers': [test_organization], 'lotValues': [{"value": {"amount": 500}, 'relatedLot': lot_id}]}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        bidder = response.json['data']
        lot = bidder['lotValues'][0]

        response = self.app.patch_json('/tenders/{}/bids/{}'.format(self.tender_id, bidder['id']), {"data": {'tenderers': [{"name": u"Державне управління управлінням справами"}]}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['lotValues'][0]['date'], lot['date'])
        self.assertNotEqual(response.json['data']['tenderers'][0]['name'], bidder['tenderers'][0]['name'])

        response = self.app.patch_json('/tenders/{}/bids/{}'.format(self.tender_id, bidder['id']), {"data": {'lotValues': [{"value": {"amount": 500}, 'relatedLot': lot_id}], 'tenderers': [test_organization]}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['lotValues'][0]['date'], lot['date'])
        self.assertEqual(response.json['data']['tenderers'][0]['name'], bidder['tenderers'][0]['name'])

        response = self.app.patch_json('/tenders/{}/bids/{}'.format(self.tender_id, bidder['id']), {"data": {'lotValues': [{"value": {"amount": 400}, 'relatedLot': lot_id}]}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['lotValues'][0]["value"]["amount"], 400)
        self.assertNotEqual(response.json['data']['lotValues'][0]['date'], lot['date'])

        self.set_status('complete')

        response = self.app.get('/tenders/{}/bids/{}'.format(self.tender_id, bidder['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['lotValues'][0]["value"]["amount"], 400)

        response = self.app.patch_json('/tenders/{}/bids/{}'.format(self.tender_id, bidder['id']), {"data": {'lotValues': [{"value": {"amount": 500}, 'relatedLot': lot_id}]}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update bid in current (complete) tender status")


class TenderLotFeatureBidderResourceTest(BaseTenderWebTest):
    initial_lots = test_lots

    def setUp(self):
        super(TenderLotFeatureBidderResourceTest, self).setUp()
        self.lot_id = self.initial_lots[0]['id']
        response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {"data": {
            "items": [
                {
                    'relatedLot': self.lot_id,
                    'id': '1'
                }
            ],
            "features": [
                {
                    "code": "code_item",
                    "featureOf": "item",
                    "relatedItem": "1",
                    "title": u"item feature",
                    "enum": [
                        {
                            "value": 0.01,
                            "title": u"good"
                        },
                        {
                            "value": 0.02,
                            "title": u"best"
                        }
                    ]
                },
                {
                    "code": "code_lot",
                    "featureOf": "lot",
                    "relatedItem": self.lot_id,
                    "title": u"lot feature",
                    "enum": [
                        {
                            "value": 0.01,
                            "title": u"good"
                        },
                        {
                            "value": 0.02,
                            "title": u"best"
                        }
                    ]
                },
                {
                    "code": "code_tenderer",
                    "featureOf": "tenderer",
                    "title": u"tenderer feature",
                    "enum": [
                        {
                            "value": 0.01,
                            "title": u"good"
                        },
                        {
                            "value": 0.02,
                            "title": u"best"
                        }
                    ]
                }
            ]
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['items'][0]['relatedLot'], self.lot_id)
        self.set_status('active.tendering')

    def test_create_tender_bidder_invalid(self):
        request_path = '/tenders/{}/bids'.format(self.tender_id)
        response = self.app.post_json(request_path, {'data': {'tenderers': [test_organization]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'All features parameters is required.'], u'location': u'body', u'name': u'parameters'},
            {u'description': [u'This field is required.'], u'location': u'body', u'name': u'lotValues'}
        ])

        response = self.app.post_json(request_path, {'data': {'tenderers': [test_organization], 'lotValues': [{"value": {"amount": 500}}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [{u'relatedLot': [u'This field is required.']}], u'location': u'body', u'name': u'lotValues'}
        ])

        response = self.app.post_json(request_path, {'data': {'tenderers': [test_organization], 'lotValues': [{"value": {"amount": 500}, 'relatedLot': "0" * 32}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [{u'relatedLot': [u'relatedLot should be one of lots']}], u'location': u'body', u'name': u'lotValues'}
        ])

        response = self.app.post_json(request_path, {'data': {'tenderers': [test_organization], 'lotValues': [{"value": {"amount": 5000000}, 'relatedLot': self.lot_id}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [{u'value': [u'value of bid should be less than value of lot']}], u'location': u'body', u'name': u'lotValues'}
        ])

        response = self.app.post_json(request_path, {'data': {'tenderers': [test_organization], 'lotValues': [{"value": {"amount": 500, 'valueAddedTaxIncluded': False}, 'relatedLot': self.lot_id}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [{u'value': [u'valueAddedTaxIncluded of bid should be identical to valueAddedTaxIncluded of value of lot']}], u'location': u'body', u'name': u'lotValues'}
        ])

        response = self.app.post_json(request_path, {'data': {'tenderers': [test_organization], 'lotValues': [{"value": {"amount": 500, 'currency': "USD"}, 'relatedLot': self.lot_id}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [{u'value': [u'currency of bid should be identical to currency of value of lot']}], u'location': u'body', u'name': u'lotValues'},
        ])

        response = self.app.post_json(request_path, {'data': {'tenderers': test_organization, 'lotValues': [{"value": {"amount": 500}, 'relatedLot': self.lot_id}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u"invalid literal for int() with base 10: 'contactPoint'", u'location': u'body', u'name': u'data'},
        ])

        response = self.app.post_json(request_path, {'data': {'tenderers': [test_organization], 'lotValues': [{"value": {"amount": 500}, 'relatedLot': self.lot_id}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'All features parameters is required.'], u'location': u'body', u'name': u'parameters'}
        ])

        response = self.app.post_json(request_path, {'data': {'tenderers': [test_organization], 'lotValues': [{"value": {"amount": 500}, 'relatedLot': self.lot_id}], 'parameters': [{"code": "code_item", "value": 0.01}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'All features parameters is required.'], u'location': u'body', u'name': u'parameters'}
        ])

        response = self.app.post_json(request_path, {'data': {'tenderers': [test_organization], 'lotValues': [{"value": {"amount": 500}, 'relatedLot': self.lot_id}], 'parameters': [{"code": "code_invalid", "value": 0.01}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [{u'code': [u'code should be one of feature code.']}], u'location': u'body', u'name': u'parameters'}
        ])

        response = self.app.post_json(request_path, {'data': {'tenderers': [test_organization], 'lotValues': [{"value": {"amount": 500}, 'relatedLot': self.lot_id}], 'parameters': [
            {"code": "code_item", "value": 0.01},
            {"code": "code_tenderer", "value": 0},
            {"code": "code_lot", "value": 0.01},
        ]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [{u'value': [u'value should be one of feature value.']}], u'location': u'body', u'name': u'parameters'}
        ])

    def test_create_tender_bidder(self):
        request_path = '/tenders/{}/bids'.format(self.tender_id)
        response = self.app.post_json(request_path, {'data': {'tenderers': [test_organization], 'lotValues': [{"value": {"amount": 500}, 'relatedLot': self.lot_id}], 'parameters': [
            {"code": "code_item", "value": 0.01},
            {"code": "code_tenderer", "value": 0.01},
            {"code": "code_lot", "value": 0.01},
        ]}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        bidder = response.json['data']
        self.assertEqual(bidder['tenderers'][0]['name'], test_organization['name'])
        self.assertIn('id', bidder)
        self.assertIn(bidder['id'], response.headers['Location'])

        self.set_status('complete')

        response = self.app.post_json(request_path, {'data': {'tenderers': [test_organization], 'lotValues': [{"value": {"amount": 500}, 'relatedLot': self.lot_id}], 'parameters': [
            {"code": "code_item", "value": 0.01},
            {"code": "code_tenderer", "value": 0.01},
            {"code": "code_lot", "value": 0.01},
        ]}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't add bid in current (complete) tender status")


class TenderLotProcessTest(BaseTenderWebTest):
    setUp = BaseWebTest.setUp

    def test_1lot_0bid(self):
        self.app.authorization = ('Basic', ('broker', ''))
        # create tender
        response = self.app.post_json('/tenders', {"data": test_tender_data})
        tender_id = self.tender_id = response.json['data']['id']
        owner_token = response.json['access']['token']
        # add lot
        response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(tender_id, owner_token), {'data': test_lots[0]})
        self.assertEqual(response.status, '201 Created')
        lot_id = response.json['data']['id']
        # add relatedLot for item
        response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender_id, owner_token), {"data": {"items": [{'relatedLot': lot_id}]}})
        self.assertEqual(response.status, '200 OK')
        # switch to active.tendering
        response = self.set_status('active.tendering', {"lots": [{"auctionPeriod": {"startDate": (get_now() + timedelta(days=10)).isoformat()}}]})
        self.assertIn("auctionPeriod", response.json['data']['lots'][0])
        # switch to unsuccessful
        response = self.set_status('active.auction', {"lots": [{"auctionPeriod": {"startDate": None}}], 'status': 'active.tendering'})
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(tender_id), {"data": {"id": tender_id}})
        self.assertEqual(response.json['data']["lots"][0]['status'], 'unsuccessful')
        self.assertEqual(response.json['data']['status'], 'unsuccessful')

    def test_1lot_1bid(self):
        self.app.authorization = ('Basic', ('broker', ''))
        # create tender
        response = self.app.post_json('/tenders', {"data": test_tender_data})
        tender_id = self.tender_id = response.json['data']['id']
        owner_token = response.json['access']['token']
        # add lot
        response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(tender_id, owner_token), {'data': test_lots[0]})
        self.assertEqual(response.status, '201 Created')
        lot_id = response.json['data']['id']
        # add relatedLot for item
        response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender_id, owner_token), {"data": {"items": [{'relatedLot': lot_id}]}})
        self.assertEqual(response.status, '200 OK')
        # switch to active.tendering
        response = self.set_status('active.tendering', {"lots": [{"auctionPeriod": {"startDate": (get_now() + timedelta(days=10)).isoformat()}}]})
        self.assertIn("auctionPeriod", response.json['data']['lots'][0])
        # create bid
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.post_json('/tenders/{}/bids'.format(tender_id),
                                      {'data': {'tenderers': [test_organization], 'lotValues': [{"value": {"amount": 500}, 'relatedLot': lot_id}]}})
        # switch to active.qualification
        response = self.set_status('active.auction', {"lots": [{"auctionPeriod": {"startDate": None}}], 'status': 'active.tendering'})
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(tender_id), {"data": {"id": tender_id}})
        # get awards
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}/awards?acc_token={}'.format(tender_id, owner_token))
        # get pending award
        award_id = [i['id'] for i in response.json['data'] if i['status'] == 'pending'][0]
        # set award as active
        self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(tender_id, award_id, owner_token), {"data": {"status": "active"}})
        # get contract id
        response = self.app.get('/tenders/{}'.format(tender_id))
        contract_id = response.json['data']['contracts'][-1]['id']
        # after stand slill period
        self.set_status('complete', {'status': 'active.awarded'})
        # time travel
        tender = self.db.get(tender_id)
        for i in tender.get('awards', []):
            i['complaintPeriod']['endDate'] = i['complaintPeriod']['startDate']
        self.db.save(tender)
        # sign contract
        self.app.authorization = ('Basic', ('broker', ''))
        self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(tender_id, contract_id, owner_token), {"data": {"status": "active"}})
        # check status
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}'.format(tender_id))
        self.assertEqual(response.json['data']["lots"][0]['status'], 'complete')
        self.assertEqual(response.json['data']['status'], 'complete')

    def test_1lot_2bid(self):
        self.app.authorization = ('Basic', ('broker', ''))
        # create tender
        response = self.app.post_json('/tenders', {"data": test_tender_data})
        tender_id = self.tender_id = response.json['data']['id']
        owner_token = response.json['access']['token']
        # add lot
        response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(tender_id, owner_token), {'data': test_lots[0]})
        self.assertEqual(response.status, '201 Created')
        lot_id = response.json['data']['id']
        self.initial_lots = [response.json['data']]
        # add relatedLot for item
        response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender_id, owner_token), {"data": {"items": [{'relatedLot': lot_id}]}})
        self.assertEqual(response.status, '200 OK')
        # switch to active.tendering
        response = self.set_status('active.tendering', {"lots": [{"auctionPeriod": {"startDate": (get_now() + timedelta(days=10)).isoformat()}}]})
        self.assertIn("auctionPeriod", response.json['data']['lots'][0])
        # create bid
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.post_json('/tenders/{}/bids'.format(tender_id),
                                      {'data': {'tenderers': [test_organization], 'lotValues': [{"value": {"amount": 450}, 'relatedLot': lot_id}]}})
        bid_id = response.json['data']['id']
        bid_token = response.json['access']['token']
        # create second bid
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.post_json('/tenders/{}/bids'.format(tender_id),
                                      {'data': {'tenderers': [test_organization], 'lotValues': [{"value": {"amount": 475}, 'relatedLot': lot_id}]}})
        # switch to active.auction
        self.set_status('active.auction')
        # get auction info
        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.get('/tenders/{}/auction'.format(tender_id))
        auction_bids_data = response.json['data']['bids']
        # posting auction urls
        response = self.app.patch_json('/tenders/{}/auction/{}'.format(tender_id, lot_id), {
            'data': {
                'lots': [
                    {
                        'id': i['id'],
                        'auctionUrl': 'https://tender.auction.url'
                    }
                    for i in response.json['data']['lots']
                ],
                'bids': [
                    {
                        'id': i['id'],
                        'lotValues': [
                            {
                                'relatedLot': j['relatedLot'],
                                'participationUrl': 'https://tender.auction.url/for_bid/{}'.format(i['id'])
                            }
                            for j in i['lotValues']
                        ],
                    }
                    for i in auction_bids_data
                ]
            }
        })
        # view bid participationUrl
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}/bids/{}?acc_token={}'.format(tender_id, bid_id, bid_token))
        self.assertEqual(response.json['data']['lotValues'][0]['participationUrl'], 'https://tender.auction.url/for_bid/{}'.format(bid_id))
        # posting auction results
        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.post_json('/tenders/{}/auction/{}'.format(tender_id, lot_id), {'data': {'bids': auction_bids_data}})
        # get awards
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}/awards?acc_token={}'.format(tender_id, owner_token))
        # get pending award
        award_id = [i['id'] for i in response.json['data'] if i['status'] == 'pending'][0]
        # set award as active
        self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(tender_id, award_id, owner_token), {"data": {"status": "active"}})
        # get contract id
        response = self.app.get('/tenders/{}'.format(tender_id))
        contract_id = response.json['data']['contracts'][-1]['id']
        # after stand slill period
        self.set_status('complete', {'status': 'active.awarded'})
        # time travel
        tender = self.db.get(tender_id)
        for i in tender.get('awards', []):
            i['complaintPeriod']['endDate'] = i['complaintPeriod']['startDate']
        self.db.save(tender)
        # sign contract
        self.app.authorization = ('Basic', ('broker', ''))
        self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(tender_id, contract_id, owner_token), {"data": {"status": "active"}})
        # check status
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}'.format(tender_id))
        self.assertEqual(response.json['data']["lots"][0]['status'], 'complete')
        self.assertEqual(response.json['data']['status'], 'complete')

    def test_2lot_0bid(self):
        self.app.authorization = ('Basic', ('broker', ''))
        # create tender
        response = self.app.post_json('/tenders', {"data": test_tender_data})
        tender_id = self.tender_id = response.json['data']['id']
        owner_token = response.json['access']['token']
        lots = []
        for lot in 2 * test_lots:
            # add lot
            response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(tender_id, owner_token), {'data': test_lots[0]})
            self.assertEqual(response.status, '201 Created')
            lots.append(response.json['data']['id'])
        # add item
        response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender_id, owner_token), {"data": {"items": [test_tender_data['items'][0] for i in lots]}})
        # add relatedLot for item
        response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender_id, owner_token), {"data": {"items": [{'relatedLot': i} for i in lots]}})
        self.assertEqual(response.status, '200 OK')
        # switch to active.tendering
        response = self.set_status('active.tendering', {"lots": [
            {"auctionPeriod": {"startDate": (get_now() + timedelta(days=10)).isoformat()}}
            for i in lots
        ]})
        self.assertTrue(all(["auctionPeriod" in i for i in response.json['data']['lots']]))
        # switch to unsuccessful
        response = self.set_status('active.auction', {
            "lots": [
                {"auctionPeriod": {"startDate": None}}
                for i in lots
            ],
            'status': 'active.tendering'})
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(tender_id), {"data": {"id": tender_id}})
        self.assertTrue(all([i['status'] == 'unsuccessful' for i in response.json['data']['lots']]))
        self.assertEqual(response.json['data']['status'], 'unsuccessful')

    def test_2lot_2can(self):
        self.app.authorization = ('Basic', ('broker', ''))
        # create tender
        response = self.app.post_json('/tenders', {"data": test_tender_data})
        tender_id = self.tender_id = response.json['data']['id']
        owner_token = response.json['access']['token']
        lots = []
        for lot in 2 * test_lots:
            # add lot
            response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(tender_id, owner_token), {'data': test_lots[0]})
            self.assertEqual(response.status, '201 Created')
            lots.append(response.json['data']['id'])
        # add item
        response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender_id, owner_token), {"data": {"items": [test_tender_data['items'][0] for i in lots]}})
        # add relatedLot for item
        response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender_id, owner_token), {"data": {"items": [{'relatedLot': i} for i in lots]}})
        self.assertEqual(response.status, '200 OK')
        # switch to active.tendering
        response = self.set_status('active.tendering', {"lots": [
            {"auctionPeriod": {"startDate": (get_now() + timedelta(days=10)).isoformat()}}
            for i in lots
        ]})
        self.assertTrue(all(["auctionPeriod" in i for i in response.json['data']['lots']]))
        # cancel every lot
        for lot_id in lots:
            response = self.app.post_json('/tenders/{}/cancellations?acc_token={}'.format(tender_id, owner_token), {'data': {
                'reason': 'cancellation reason',
                'status': 'active',
                "cancellationOf": "lot",
                "relatedLot": lot_id
            }})
        response = self.app.get('/tenders/{}'.format(tender_id))
        self.assertTrue(all([i['status'] == 'cancelled' for i in response.json['data']['lots']]))
        self.assertEqual(response.json['data']['status'], 'cancelled')

    def test_2lot_2bid_0com_1can_before_auction(self):
        self.app.authorization = ('Basic', ('broker', ''))
        # create tender
        response = self.app.post_json('/tenders', {"data": test_tender_data})
        tender_id = self.tender_id = response.json['data']['id']
        owner_token = response.json['access']['token']
        lots = []
        for lot in 2 * test_lots:
            # add lot
            response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(tender_id, owner_token), {'data': test_lots[0]})
            self.assertEqual(response.status, '201 Created')
            lots.append(response.json['data']['id'])
        # add item
        response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender_id, owner_token), {"data": {"items": [test_tender_data['items'][0] for i in lots]}})
        # add relatedLot for item
        response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender_id, owner_token), {"data": {"items": [{'relatedLot': i} for i in lots]}})
        self.assertEqual(response.status, '200 OK')
        # switch to active.tendering
        response = self.set_status('active.tendering', {"lots": [
            {"auctionPeriod": {"startDate": (get_now() + timedelta(days=10)).isoformat()}}
            for i in lots
        ]})
        # create bid
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.post_json('/tenders/{}/bids'.format(tender_id), {'data': {'tenderers': [test_organization], 'lotValues': [
            {"value": {"amount": 500}, 'relatedLot': lot_id}
            for lot_id in lots
        ]}})
        # for first lot
        lot_id = lots[0]
        # create bid #2 for 1 lot
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.post_json('/tenders/{}/bids'.format(tender_id), {'data': {'tenderers': [test_organization], 'lotValues': [
            {"value": {"amount": 500}, 'relatedLot': lot_id}
        ]}})
        # cancel lot
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.post_json('/tenders/{}/cancellations?acc_token={}'.format(tender_id, owner_token), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": lot_id
        }})
        # switch to active.qualification
        response = self.set_status('active.auction', {'status': 'active.tendering'})
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(tender_id), {"data": {"id": tender_id}})
        self.assertEqual(response.json['data']['status'], 'active.qualification')
        # for second lot
        lot_id = lots[1]
        # get awards
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}/awards?acc_token={}'.format(tender_id, owner_token))
        # get pending award
        award_id = [i['id'] for i in response.json['data'] if i['status'] == 'pending' and i['lotID'] == lot_id][0]
        # set award as unsuccessful
        self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(tender_id, award_id, owner_token), {"data": {"status": "unsuccessful"}})
        # after stand slill period
        self.set_status('complete', {'status': 'active.awarded'})
        # time travel
        tender = self.db.get(tender_id)
        for i in tender.get('awards', []):
            i['complaintPeriod']['endDate'] = i['complaintPeriod']['startDate']
        self.db.save(tender)
        # check tender status
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(tender_id), {"data": {"id": tender_id}})
        # check status
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}'.format(tender_id))
        self.assertEqual([i['status'] for i in response.json['data']['lots']], [u'cancelled', u'unsuccessful'])
        self.assertEqual(response.json['data']['status'], 'unsuccessful')

    def test_2lot_1bid_0com_1can(self):
        self.app.authorization = ('Basic', ('broker', ''))
        # create tender
        response = self.app.post_json('/tenders', {"data": test_tender_data})
        tender_id = self.tender_id = response.json['data']['id']
        owner_token = response.json['access']['token']
        lots = []
        for lot in 2 * test_lots:
            # add lot
            response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(tender_id, owner_token), {'data': test_lots[0]})
            self.assertEqual(response.status, '201 Created')
            lots.append(response.json['data']['id'])
        # add item
        response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender_id, owner_token), {"data": {"items": [test_tender_data['items'][0] for i in lots]}})
        # add relatedLot for item
        response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender_id, owner_token), {"data": {"items": [{'relatedLot': i} for i in lots]}})
        self.assertEqual(response.status, '200 OK')
        # switch to active.tendering
        response = self.set_status('active.tendering', {"lots": [
            {"auctionPeriod": {"startDate": (get_now() + timedelta(days=10)).isoformat()}}
            for i in lots
        ]})
        # create bid
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.post_json('/tenders/{}/bids'.format(tender_id), {'data': {'tenderers': [test_organization], 'lotValues': [
            {"value": {"amount": 500}, 'relatedLot': lot_id}
            for lot_id in lots
        ]}})
        # switch to active.qualification
        response = self.set_status('active.auction', {
            "lots": [
                {"auctionPeriod": {"startDate": None}}
                for i in lots
            ],
            'status': 'active.tendering'})
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(tender_id), {"data": {"id": tender_id}})
        # for first lot
        lot_id = lots[0]
        # cancel lot
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.post_json('/tenders/{}/cancellations?acc_token={}'.format(tender_id, owner_token), {'data': {
            'reason': 'cancellation reason',
            'status': 'active',
            "cancellationOf": "lot",
            "relatedLot": lot_id
        }})
        # for second lot
        lot_id = lots[1]
        # get awards
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}/awards?acc_token={}'.format(tender_id, owner_token))
        # get pending award
        award_id = [i['id'] for i in response.json['data'] if i['status'] == 'pending' and i['lotID'] == lot_id][0]
        # set award as unsuccessful
        self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(tender_id, award_id, owner_token), {"data": {"status": "unsuccessful"}})
        # after stand slill period
        self.set_status('complete', {'status': 'active.awarded'})
        # time travel
        tender = self.db.get(tender_id)
        for i in tender.get('awards', []):
            i['complaintPeriod']['endDate'] = i['complaintPeriod']['startDate']
        self.db.save(tender)
        # check tender status
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(tender_id), {"data": {"id": tender_id}})
        # check status
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}'.format(tender_id))
        self.assertEqual([i['status'] for i in response.json['data']['lots']], [u'cancelled', u'unsuccessful'])
        self.assertEqual(response.json['data']['status'], 'unsuccessful')

    def test_2lot_1bid_2com_1win(self):
        self.app.authorization = ('Basic', ('broker', ''))
        # create tender
        response = self.app.post_json('/tenders', {"data": test_tender_data})
        tender_id = self.tender_id = response.json['data']['id']
        owner_token = response.json['access']['token']
        lots = []
        for lot in 2 * test_lots:
            # add lot
            response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(tender_id, owner_token), {'data': test_lots[0]})
            self.assertEqual(response.status, '201 Created')
            lots.append(response.json['data']['id'])
        # add item
        response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender_id, owner_token), {"data": {"items": [test_tender_data['items'][0] for i in lots]}})
        # add relatedLot for item
        response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender_id, owner_token), {"data": {"items": [{'relatedLot': i} for i in lots]}})
        self.assertEqual(response.status, '200 OK')
        # switch to active.tendering
        response = self.set_status('active.tendering', {"lots": [
            {"auctionPeriod": {"startDate": (get_now() + timedelta(days=10)).isoformat()}}
            for i in lots
        ]})
        # create bid
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.post_json('/tenders/{}/bids'.format(tender_id), {'data': {'tenderers': [test_organization], 'lotValues': [
            {"value": {"amount": 500}, 'relatedLot': lot_id}
            for lot_id in lots
        ]}})
        # switch to active.qualification
        response = self.set_status('active.auction', {
            "lots": [
                {"auctionPeriod": {"startDate": None}}
                for i in lots
            ],
            'status': 'active.tendering'})
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(tender_id), {"data": {"id": tender_id}})
        for lot_id in lots:
            # get awards
            self.app.authorization = ('Basic', ('broker', ''))
            response = self.app.get('/tenders/{}/awards?acc_token={}'.format(tender_id, owner_token))
            # get pending award
            award_id = [i['id'] for i in response.json['data'] if i['status'] == 'pending' and i['lotID'] == lot_id][0]
            # set award as active
            self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(tender_id, award_id, owner_token), {"data": {"status": "active"}})
            # get contract id
            response = self.app.get('/tenders/{}'.format(tender_id))
            contract_id = response.json['data']['contracts'][-1]['id']
            # after stand slill period
            self.set_status('complete', {'status': 'active.awarded'})
            # time travel
            tender = self.db.get(tender_id)
            for i in tender.get('awards', []):
                i['complaintPeriod']['endDate'] = i['complaintPeriod']['startDate']
            self.db.save(tender)
            # sign contract
            self.app.authorization = ('Basic', ('broker', ''))
            self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(tender_id, contract_id, owner_token), {"data": {"status": "active"}})
        # check status
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}'.format(tender_id))
        self.assertTrue(all([i['status'] == 'complete' for i in response.json['data']['lots']]))
        self.assertEqual(response.json['data']['status'], 'complete')

    def test_2lot_1bid_0com_0win(self):
        self.app.authorization = ('Basic', ('broker', ''))
        # create tender
        response = self.app.post_json('/tenders', {"data": test_tender_data})
        tender_id = self.tender_id = response.json['data']['id']
        owner_token = response.json['access']['token']
        lots = []
        for lot in 2 * test_lots:
            # add lot
            response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(tender_id, owner_token), {'data': test_lots[0]})
            self.assertEqual(response.status, '201 Created')
            lots.append(response.json['data']['id'])
        # add item
        response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender_id, owner_token), {"data": {"items": [test_tender_data['items'][0] for i in lots]}})
        # add relatedLot for item
        response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender_id, owner_token), {"data": {"items": [{'relatedLot': i} for i in lots]}})
        self.assertEqual(response.status, '200 OK')
        # switch to active.tendering
        response = self.set_status('active.tendering', {"lots": [
            {"auctionPeriod": {"startDate": (get_now() + timedelta(days=10)).isoformat()}}
            for i in lots
        ]})
        # create bid
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.post_json('/tenders/{}/bids'.format(tender_id), {'data': {'tenderers': [test_organization], 'lotValues': [
            {"value": {"amount": 500}, 'relatedLot': lot_id}
            for lot_id in lots
        ]}})
        # switch to active.qualification
        response = self.set_status('active.auction', {
            "lots": [
                {"auctionPeriod": {"startDate": None}}
                for i in lots
            ],
            'status': 'active.tendering'})
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(tender_id), {"data": {"id": tender_id}})
        # for every lot
        for lot_id in lots:
            # get awards
            self.app.authorization = ('Basic', ('broker', ''))
            response = self.app.get('/tenders/{}/awards?acc_token={}'.format(tender_id, owner_token))
            # get pending award
            award_id = [i['id'] for i in response.json['data'] if i['status'] == 'pending' and i['lotID'] == lot_id][0]
            # set award as unsuccessful
            self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(tender_id, award_id, owner_token), {"data": {"status": "unsuccessful"}})
            # after stand slill period
            self.set_status('complete', {'status': 'active.awarded'})
            # time travel
            tender = self.db.get(tender_id)
            for i in tender.get('awards', []):
                i['complaintPeriod']['endDate'] = i['complaintPeriod']['startDate']
            self.db.save(tender)
        # check tender status
        self.set_status('complete', {'status': 'active.awarded'})
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(tender_id), {"data": {"id": tender_id}})
        # check status
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}'.format(tender_id))
        self.assertTrue(all([i['status'] == 'unsuccessful' for i in response.json['data']['lots']]))
        self.assertEqual(response.json['data']['status'], 'unsuccessful')

    def test_2lot_1bid_1com_1win(self):
        self.app.authorization = ('Basic', ('broker', ''))
        # create tender
        response = self.app.post_json('/tenders', {"data": test_tender_data})
        tender_id = self.tender_id = response.json['data']['id']
        owner_token = response.json['access']['token']
        lots = []
        for lot in 2 * test_lots:
            # add lot
            response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(tender_id, owner_token), {'data': test_lots[0]})
            self.assertEqual(response.status, '201 Created')
            lots.append(response.json['data']['id'])
        # add item
        response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender_id, owner_token), {"data": {"items": [test_tender_data['items'][0] for i in lots]}})
        # add relatedLot for item
        response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender_id, owner_token), {"data": {"items": [{'relatedLot': i} for i in lots]}})
        self.assertEqual(response.status, '200 OK')
        # switch to active.tendering
        response = self.set_status('active.tendering', {"lots": [
            {"auctionPeriod": {"startDate": (get_now() + timedelta(days=10)).isoformat()}}
            for i in lots
        ]})
        # create bid
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.post_json('/tenders/{}/bids'.format(tender_id), {'data': {'tenderers': [test_organization], 'lotValues': [
            {"value": {"amount": 500}, 'relatedLot': lot_id}
            for lot_id in lots
        ]}})
        # switch to active.qualification
        response = self.set_status('active.auction', {
            "lots": [
                {"auctionPeriod": {"startDate": None}}
                for i in lots
            ],
            'status': 'active.tendering'})
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(tender_id), {"data": {"id": tender_id}})
        # for first lot
        lot_id = lots[0]
        # get awards
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}/awards?acc_token={}'.format(tender_id, owner_token))
        # get pending award
        award_id = [i['id'] for i in response.json['data'] if i['status'] == 'pending' and i['lotID'] == lot_id][0]
        # set award as active
        self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(tender_id, award_id, owner_token), {"data": {"status": "active"}})
        # get contract id
        response = self.app.get('/tenders/{}'.format(tender_id))
        contract_id = response.json['data']['contracts'][-1]['id']
        # after stand slill period
        self.set_status('complete', {'status': 'active.awarded'})
        # time travel
        tender = self.db.get(tender_id)
        for i in tender.get('awards', []):
            i['complaintPeriod']['endDate'] = i['complaintPeriod']['startDate']
        self.db.save(tender)
        # sign contract
        self.app.authorization = ('Basic', ('broker', ''))
        self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(tender_id, contract_id, owner_token), {"data": {"status": "active"}})
        # for second lot
        lot_id = lots[1]
        # get awards
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}/awards?acc_token={}'.format(tender_id, owner_token))
        # get pending award
        award_id = [i['id'] for i in response.json['data'] if i['status'] == 'pending' and i['lotID'] == lot_id][0]
        # set award as unsuccessful
        self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(tender_id, award_id, owner_token), {"data": {"status": "unsuccessful"}})
        # after stand slill period
        self.set_status('complete', {'status': 'active.awarded'})
        # time travel
        tender = self.db.get(tender_id)
        for i in tender.get('awards', []):
            i['complaintPeriod']['endDate'] = i['complaintPeriod']['startDate']
        self.db.save(tender)
        # check tender status
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(tender_id), {"data": {"id": tender_id}})
        # check status
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}'.format(tender_id))
        self.assertEqual([i['status'] for i in response.json['data']['lots']], [u'complete', u'unsuccessful'])
        self.assertEqual(response.json['data']['status'], 'complete')

    def test_2lot_2bid_2com_2win(self):
        self.app.authorization = ('Basic', ('broker', ''))
        # create tender
        response = self.app.post_json('/tenders', {"data": test_tender_data})
        tender_id = self.tender_id = response.json['data']['id']
        owner_token = response.json['access']['token']
        lots = []
        for lot in 2 * test_lots:
            # add lot
            response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(tender_id, owner_token), {'data': test_lots[0]})
            self.assertEqual(response.status, '201 Created')
            lots.append(response.json['data']['id'])
        self.initial_lots = lots
        # add item
        response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender_id, owner_token), {"data": {"items": [test_tender_data['items'][0] for i in lots]}})
        # add relatedLot for item
        response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender_id, owner_token), {"data": {"items": [{'relatedLot': i} for i in lots]}})
        self.assertEqual(response.status, '200 OK')
        # switch to active.tendering
        response = self.set_status('active.tendering', {"lots": [
            {"auctionPeriod": {"startDate": (get_now() + timedelta(days=10)).isoformat()}}
            for i in lots
        ]})
        # create bid
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.post_json('/tenders/{}/bids'.format(tender_id), {'data': {'tenderers': [test_organization], 'lotValues': [
            {"value": {"amount": 500}, 'relatedLot': lot_id}
            for lot_id in lots
        ]}})
        # create second bid
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.post_json('/tenders/{}/bids'.format(tender_id), {'data': {'tenderers': [test_organization], 'lotValues': [
            {"value": {"amount": 500}, 'relatedLot': lot_id}
            for lot_id in lots
        ]}})
        # switch to active.auction
        self.set_status('active.auction')
        # get auction info
        self.app.authorization = ('Basic', ('auction', ''))
        response = self.app.get('/tenders/{}/auction'.format(tender_id))
        auction_bids_data = response.json['data']['bids']
        for lot_id in lots:
            # posting auction urls
            response = self.app.patch_json('/tenders/{}/auction/{}'.format(tender_id, lot_id), {
                'data': {
                    'lots': [
                        {
                            'id': i['id'],
                            'auctionUrl': 'https://tender.auction.url'
                        }
                        for i in response.json['data']['lots']
                    ],
                    'bids': [
                        {
                            'id': i['id'],
                            'lotValues': [
                                {
                                    'relatedLot': j['relatedLot'],
                                    'participationUrl': 'https://tender.auction.url/for_bid/{}'.format(i['id'])
                                }
                                for j in i['lotValues']
                            ],
                        }
                        for i in auction_bids_data
                    ]
                }
            })
            # posting auction results
            self.app.authorization = ('Basic', ('auction', ''))
            response = self.app.post_json('/tenders/{}/auction/{}'.format(tender_id, lot_id), {'data': {'bids': auction_bids_data}})
        # for first lot
        lot_id = lots[0]
        # get awards
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}/awards?acc_token={}'.format(tender_id, owner_token))
        # get pending award
        award_id = [i['id'] for i in response.json['data'] if i['status'] == 'pending' and i['lotID'] == lot_id][0]
        # set award as active
        self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(tender_id, award_id, owner_token), {"data": {"status": "active"}})
        # get contract id
        response = self.app.get('/tenders/{}'.format(tender_id))
        contract_id = response.json['data']['contracts'][-1]['id']
        # after stand slill period
        self.set_status('complete', {'status': 'active.awarded'})
        # time travel
        tender = self.db.get(tender_id)
        for i in tender.get('awards', []):
            i['complaintPeriod']['endDate'] = i['complaintPeriod']['startDate']
        self.db.save(tender)
        # sign contract
        self.app.authorization = ('Basic', ('broker', ''))
        self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(tender_id, contract_id, owner_token), {"data": {"status": "active"}})
        # for second lot
        lot_id = lots[1]
        # get awards
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}/awards?acc_token={}'.format(tender_id, owner_token))
        # get pending award
        award_id = [i['id'] for i in response.json['data'] if i['status'] == 'pending' and i['lotID'] == lot_id][0]
        # set award as unsuccessful
        self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(tender_id, award_id, owner_token), {"data": {"status": "unsuccessful"}})
        # get awards
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}/awards?acc_token={}'.format(tender_id, owner_token))
        # get pending award
        award_id = [i['id'] for i in response.json['data'] if i['status'] == 'pending' and i['lotID'] == lot_id][0]
        # set award as active
        self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(tender_id, award_id, owner_token), {"data": {"status": "active"}})
        # get contract id
        response = self.app.get('/tenders/{}'.format(tender_id))
        contract_id = response.json['data']['contracts'][-1]['id']
        # after stand slill period
        self.set_status('complete', {'status': 'active.awarded'})
        # time travel
        tender = self.db.get(tender_id)
        for i in tender.get('awards', []):
            i['complaintPeriod']['endDate'] = i['complaintPeriod']['startDate']
        self.db.save(tender)
        # sign contract
        self.app.authorization = ('Basic', ('broker', ''))
        self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(tender_id, contract_id, owner_token), {"data": {"status": "active"}})
        # check status
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}'.format(tender_id))
        self.assertTrue(all([i['status'] == 'complete' for i in response.json['data']['lots']]))
        self.assertEqual(response.json['data']['status'], 'complete')

    def test_2lot_1feature_2bid_2com_2win(self):
        self.app.authorization = ('Basic', ('broker', ''))
        # create tender
        response = self.app.post_json('/tenders', {"data": test_tender_data})
        tender_id = self.tender_id = response.json['data']['id']
        owner_token = response.json['access']['token']
        lots = []
        for lot in 2 * test_lots:
            # add lot
            response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(tender_id, owner_token), {'data': test_lots[0]})
            self.assertEqual(response.status, '201 Created')
            lots.append(response.json['data']['id'])
        self.initial_lots = lots
        # add item
        response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender_id, owner_token), {"data": {"items": [test_tender_data['items'][0] for i in lots]}})
        # add relatedLot for item
        response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender_id, owner_token), {"data": {"items": [{'relatedLot': i} for i in lots]}})
        # add features
        response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender_id, owner_token), {"data": {"features": [
            {
                "code": "code_item",
                "featureOf": "item",
                "relatedItem": response.json['data']['items'][0]['id'],
                "title": u"item feature",
                "enum": [
                    {
                        "value": 0.1,
                        "title": u"good"
                    },
                    {
                        "value": 0.2,
                        "title": u"best"
                    }
                ]
            }
        ]}})
        self.assertEqual(response.status, '200 OK')
        # switch to active.tendering
        response = self.set_status('active.tendering', {"lots": [
            {"auctionPeriod": {"startDate": (get_now() + timedelta(days=10)).isoformat()}}
            for i in lots
        ]})
        # create bid
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.post_json('/tenders/{}/bids'.format(tender_id), {'data': {'tenderers': [test_organization], 'lotValues': [
            {"value": {"amount": 500}, 'relatedLot': lots[0]}
        ], 'parameters': [{"code": "code_item", "value": 0.2}]}})
        # create second bid
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.post_json('/tenders/{}/bids'.format(tender_id), {'data': {'tenderers': [test_organization], 'lotValues': [
            {"value": {"amount": 500}, 'relatedLot': lots[1]}
        ]}})
        # switch to active.qualification
        response = self.set_status('active.auction', {'status': 'active.tendering'})
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.patch_json('/tenders/{}'.format(tender_id), {"data": {"id": tender_id}})
        # for first lot
        lot_id = lots[0]
        # get awards
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}/awards?acc_token={}'.format(tender_id, owner_token))
        # get pending award
        award_id = [i['id'] for i in response.json['data'] if i['status'] == 'pending' and i['lotID'] == lot_id][0]
        # set award as active
        self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(tender_id, award_id, owner_token), {"data": {"status": "active"}})
        # get contract id
        response = self.app.get('/tenders/{}'.format(tender_id))
        contract_id = response.json['data']['contracts'][-1]['id']
        # after stand slill period
        self.set_status('complete', {'status': 'active.awarded'})
        # time travel
        tender = self.db.get(tender_id)
        for i in tender.get('awards', []):
            i['complaintPeriod']['endDate'] = i['complaintPeriod']['startDate']
        self.db.save(tender)
        # sign contract
        self.app.authorization = ('Basic', ('broker', ''))
        self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(tender_id, contract_id, owner_token), {"data": {"status": "active"}})
        # for second lot
        lot_id = lots[1]
        # get awards
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}/awards?acc_token={}'.format(tender_id, owner_token))
        # get pending award
        award_id = [i['id'] for i in response.json['data'] if i['status'] == 'pending' and i['lotID'] == lot_id][0]
        # set award as active
        self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(tender_id, award_id, owner_token), {"data": {"status": "active"}})
        # get contract id
        response = self.app.get('/tenders/{}'.format(tender_id))
        contract_id = response.json['data']['contracts'][-1]['id']
        # after stand slill period
        self.set_status('complete', {'status': 'active.awarded'})
        # time travel
        tender = self.db.get(tender_id)
        for i in tender.get('awards', []):
            i['complaintPeriod']['endDate'] = i['complaintPeriod']['startDate']
        self.db.save(tender)
        # sign contract
        self.app.authorization = ('Basic', ('broker', ''))
        self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(tender_id, contract_id, owner_token), {"data": {"status": "active"}})
        # check status
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.get('/tenders/{}'.format(tender_id))
        self.assertTrue(all([i['status'] == 'complete' for i in response.json['data']['lots']]))
        self.assertEqual(response.json['data']['status'], 'complete')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TenderLotResourceTest))
    suite.addTest(unittest.makeSuite(TenderLotBidderResourceTest))
    suite.addTest(unittest.makeSuite(TenderLotFeatureBidderResourceTest))
    suite.addTest(unittest.makeSuite(TenderLotProcessTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
