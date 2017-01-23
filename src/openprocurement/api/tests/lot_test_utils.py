# -*- coding: utf-8 -*-
import unittest
from copy import deepcopy
from datetime import timedelta

from openprocurement.api.models import get_now
from openprocurement.api.tests.base import BaseWebTest, BaseTenderWebTest, test_tender_data, test_lots, test_organization


def create_tender_lot_invalid(self):
    response = self.app.post_json('/tenders/some_id/lots', {'data': {'title': 'lot title', 'description': 'lot description'}}, status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location': u'url', u'name': u'tender_id'}
    ])

    request_path = '/tenders/{}/lots?acc_token={}'.format(self.tender_id, self.tender_token)

    response = self.app.post(request_path, 'data', status=415)
    self.assertEqual(response.status, '415 Unsupported Media Type')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description':
            u"Content-Type header should be one of ['application/json']", u'location': u'header', u'name': u'Content-Type'}
    ])

    response = self.app.post(
        request_path, 'data', content_type='application/json', status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'No JSON object could be decoded',
            u'location': u'body', u'name': u'data'}
    ])

    response = self.app.post_json(request_path, 'data', status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Data not available',
            u'location': u'body', u'name': u'data'}
    ])

    response = self.app.post_json(
        request_path, {'not_data': {}}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Data not available',
            u'location': u'body', u'name': u'data'}
    ])

    response = self.app.post_json(request_path, {'data': {}}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [u'This field is required.'], u'location': u'body', u'name': u'minimalStep'},
        {u'description': [u'This field is required.'], u'location': u'body', u'name': u'value'},
        {u'description': [u'This field is required.'], u'location': u'body', u'name': u'title'},
    ])

    response = self.app.post_json(request_path, {'data': {
                                  'invalid_field': 'invalid_value'}}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Rogue field', u'location':
            u'body', u'name': u'invalid_field'}
    ])

    response = self.app.post_json(request_path, {'data': {'value': 'invalid_value'}}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [
            u'Please use a mapping for this field or Value instance instead of unicode.'], u'location': u'body', u'name': u'value'}
    ])

    response = self.app.post_json(request_path, {'data': {
        'title': 'lot title',
        'description': 'lot description',
        'value': {'amount': '100.0'},
        'minimalStep': {'amount': '500.0'},
    }}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [u'value should be less than value of lot'], u'location': u'body', u'name': u'minimalStep'}
    ])

    response = self.app.post_json(request_path, {'data': {
        'title': 'lot title',
        'description': 'lot description',
        'value': {'amount': '500.0'},
        'minimalStep': {'amount': '100.0', 'currency': "USD"}
    }})
    self.assertEqual(response.status, '201 Created')
    # but minimalStep currency stays unchanged
    response = self.app.get(request_path)
    self.assertEqual(response.content_type, 'application/json')
    lots = response.json['data']
    self.assertEqual(len(lots), 1)
    self.assertEqual(lots[0]['minimalStep']['currency'], "UAH")
    self.assertEqual(lots[0]['minimalStep']['amount'], 100)

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(
        self.tender_id, self.tender_token), {"data": {"items": [{'relatedLot': '0' * 32}]}}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [{u'relatedLot': [u'relatedLot should be one of lots']}], u'location': u'body', u'name': u'items'}
    ])

def delete_tender_lot(self):
    response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(
        self.tender_id, self.tender_token), {'data': test_lots[0]})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    lot = response.json['data']

    response = self.app.delete('/tenders/{}/lots/{}?acc_token={}'.format(
        self.tender_id, lot['id'], self.tender_token))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'], lot)

    response = self.app.delete('/tenders/{}/lots/some_id?acc_token={}'.format(
        self.tender_id, self.tender_token), status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'lot_id'}
    ])

    response = self.app.delete('/tenders/some_id/lots/some_id', status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'tender_id'}
    ])

    response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(
        self.tender_id, self.tender_token), {'data': test_lots[0]})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    lot = response.json['data']

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(self.tender_id, self.tender_token), {"data": {
        "items": [
            {
                'relatedLot': lot['id']
            }
        ]
    }})
    self.assertEqual(response.status, '200 OK')

    response = self.app.delete('/tenders/{}/lots/{}?acc_token={}'.format(
        self.tender_id, lot['id'], self.tender_token), status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [{u'relatedLot': [u'relatedLot should be one of lots']}], u'location': u'body', u'name': u'items'}
    ])

    self.set_status(self.status)

    response = self.app.delete('/tenders/{}/lots/{}?acc_token={}'.format(self.tender_id, lot['id'], self.tender_token), status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't delete lot in current ({}) tender status".format(self.status))

def tender_lot_guarantee(self):
    data = deepcopy(test_tender_data)
    data['guarantee'] = {"amount": 100, "currency": "USD"}
    response = self.app.post_json('/tenders', {'data': data})
    tender = response.json['data']
    owner_token = response.json['access']['token']
    self.assertEqual(response.status, '201 Created')
    self.assertIn('guarantee', response.json['data'])
    self.assertEqual(response.json['data']['guarantee']['amount'], 100)
    self.assertEqual(response.json['data']['guarantee']['currency'], "USD")

    lot = deepcopy(test_lots[0])
    lot['guarantee'] = {"amount": 20, "currency": "USD"}
    response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(tender['id'], owner_token), {'data': lot})
    self.assertEqual(response.status, '201 Created')
    self.assertIn('guarantee', response.json['data'])
    self.assertEqual(response.json['data']['guarantee']['amount'], 20)
    self.assertEqual(response.json['data']['guarantee']['currency'], "USD")

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender['id'], owner_token), {'data': {'guarantee': {"currency": "GBP"}}})
    self.assertEqual(response.status, '200 OK')
    self.assertIn('guarantee', response.json['data'])
    self.assertEqual(response.json['data']['guarantee']['amount'], 20)
    self.assertEqual(response.json['data']['guarantee']['currency'], "GBP")

    lot['guarantee'] = {"amount": 20, "currency": "GBP"}
    response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(tender['id'], owner_token), {'data': lot})
    self.assertEqual(response.status, '201 Created')
    lot_id = response.json['data']['id']
    self.assertEqual(response.json['data']['guarantee']['amount'], 20)
    self.assertEqual(response.json['data']['guarantee']['currency'], "GBP")

    response = self.app.get('/tenders/{}'.format(tender['id']))
    self.assertEqual(response.json['data']['guarantee']['amount'], 20 + 20)
    self.assertEqual(response.json['data']['guarantee']['currency'], "GBP")

    lot2 = deepcopy(test_lots[0])
    lot2['guarantee'] = {"amount": 30, "currency": "GBP"}
    response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(tender['id'], owner_token), {'data': lot2})
    self.assertEqual(response.status, '201 Created')
    lot2_id = response.json['data']['id']
    self.assertEqual(response.json['data']['guarantee']['amount'], 30)
    self.assertEqual(response.json['data']['guarantee']['currency'], "GBP")

    lot2['guarantee'] = {"amount": 40, "currency": "USD"}
    response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(tender['id'], owner_token), {'data': lot2}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [u'lot guarantee currency should be identical to tender guarantee currency'], u'location': u'body', u'name': u'lots'}
    ])

    response = self.app.get('/tenders/{}'.format(tender['id']))
    self.assertIn('guarantee', response.json['data'])
    self.assertEqual(response.json['data']['guarantee']['amount'], 20 + 20 + 30)
    self.assertEqual(response.json['data']['guarantee']['currency'], "GBP")

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(tender['id'], owner_token), {"data": {"guarantee": {"amount": 55}}})
    self.assertEqual(response.json['data']['guarantee']['amount'], 20 + 20 + 30)
    self.assertEqual(response.json['data']['guarantee']['currency'], "GBP")

    response = self.app.patch_json('/tenders/{}/lots/{}?acc_token={}'.format(tender['id'], lot2_id, owner_token), {'data': {'guarantee': {"amount": 35, "currency": "GBP"}}})
    self.assertEqual(response.json['data']['guarantee']['amount'], 35)
    self.assertEqual(response.json['data']['guarantee']['currency'], "GBP")

    response = self.app.get('/tenders/{}'.format(tender['id']))
    self.assertIn('guarantee', response.json['data'])
    self.assertEqual(response.json['data']['guarantee']['amount'], 20 + 20 + 35)
    self.assertEqual(response.json['data']['guarantee']['currency'], "GBP")

    for l_id in (lot_id, lot2_id):
        response = self.app.patch_json('/tenders/{}/lots/{}?acc_token={}'.format(tender['id'], l_id, owner_token), {'data': {'guarantee': {"amount": 0, "currency": "GBP"}}})
        self.assertEqual(response.json['data']['guarantee']['amount'], 0)
        self.assertEqual(response.json['data']['guarantee']['currency'], "GBP")

    response = self.app.get('/tenders/{}'.format(tender['id']))
    self.assertIn('guarantee', response.json['data'])
    self.assertEqual(response.json['data']['guarantee']['amount'], 20)
    self.assertEqual(response.json['data']['guarantee']['currency'], "GBP")

    for l_id in (lot_id, lot2_id):
        response = self.app.delete('/tenders/{}/lots/{}?acc_token={}'.format(tender['id'], l_id, owner_token))
        self.assertEqual(response.status, '200 OK')

    response = self.app.get('/tenders/{}'.format(tender['id']))
    self.assertIn('guarantee', response.json['data'])
    self.assertEqual(response.json['data']['guarantee']['amount'], 20)
    self.assertEqual(response.json['data']['guarantee']['currency'], "GBP")

def tender_value(self):
    request_path = '/tenders/{}'.format(self.tender_id)
    response = self.app.get(request_path)
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['value']['amount'], sum([i['value']['amount'] for i in self.initial_lots]))
    self.assertEqual(response.json['data']['minimalStep']['amount'], min([i['minimalStep']['amount'] for i in self.initial_lots]))

def tender_features_invalid(self):
    request_path = '/tenders/{}?acc_token={}'.format(self.tender_id, self.tender_token)
    data = self.test_tender_data.copy()
    item = data['items'][0].copy()
    item['id'] = "1"
    data['items'] = [item]
    data['features'] = [
        {
            "featureOf": "lot",
            "relatedItem": self.initial_lots[0]['id'],
            "title": u"Потужність всмоктування",
            "enum": [
                {
                    "value": 0.5,
                    "title": u"До 1000 Вт"
                },
                {
                    "value": 0.15,
                    "title": u"Більше 1000 Вт"
                }
            ]
        }
    ]
    response = self.app.patch_json(request_path, {'data': data}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [{u'enum': [{u'value': [u'Float value should be less than 0.3.']}]}], u'location': u'body', u'name': u'features'}
    ])
    data['features'][0]["enum"][0]["value"] = 0.1
    data['features'].append(data['features'][0].copy())
    data['features'][1]["enum"][0]["value"] = 0.2
    response = self.app.patch_json(request_path, {'data': data}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [u'Sum of max value of all features for lot should be less then or equal to 30%'], u'location': u'body', u'name': u'features'}
    ])
    data['features'][1]["enum"][0]["value"] = 0.1
    data['features'].append(data['features'][0].copy())
    data['features'][2]["relatedItem"] = self.initial_lots[1]['id']
    data['features'].append(data['features'][2].copy())
    response = self.app.patch_json(request_path, {'data': data})
    self.assertEqual(response.status, '200 OK')

def patch_tender_currency(self):
    # create lot
    response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(self.tender_id, self.tender_token),
                                  {'data': test_lots[0]})

    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    lot = response.json['data']
    self.assertEqual(lot['value']['currency'], "UAH")

    # update tender currency without mimimalStep currency change
    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(self.tender_id, self.tender_token),
                                   {"data": {"value": {"currency": "GBP"}}}, status=422)

    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [u'currency should be identical to currency of value of tender'],
         u'location': u'body', u'name': u'minimalStep'}
    ])

    # update tender currency
    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(self.tender_id, self.tender_token), {
        "data": {
            "value": {"currency": "GBP"},
            "minimalStep": {"currency": "GBP"
            }
        }
    })

    self.assertEqual(response.status, '200 OK')
    # log currency is updated too
    response = self.app.get('/tenders/{}/lots/{}'.format(self.tender_id, lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    lot = response.json['data']
    self.assertEqual(lot['value']['currency'], "GBP")

    # try to update lot currency
    response = self.app.patch_json('/tenders/{}/lots/{}?acc_token={}'.format(self.tender_id, lot['id'], self.tender_token),
                                   {"data": {"value": {"currency": "USD"}}})
    self.assertEqual(response.status, '200 OK')
    # but the value stays unchanged
    response = self.app.get('/tenders/{}/lots/{}'.format(self.tender_id, lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    lot = response.json['data']
    self.assertEqual(lot['value']['currency'], "GBP")

    # try to update minimalStep currency
    response = self.app.patch_json('/tenders/{}/lots/{}?acc_token={}'.format(self.tender_id, lot['id'], self.tender_token),
                                   {"data": {"minimalStep": {"currency": "USD"}}})
    self.assertEqual(response.status, '200 OK')
    # but the value stays unchanged
    response = self.app.get('/tenders/{}/lots/{}'.format(self.tender_id, lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    lot = response.json['data']
    self.assertEqual(lot['minimalStep']['currency'], "GBP")

    # try to update lot minimalStep currency and lot value currency in single request
    response = self.app.patch_json('/tenders/{}/lots/{}?acc_token={}'.format(self.tender_id, lot['id'], self.tender_token),
                                   {"data": {"value": {"currency": "USD"}, "minimalStep": {"currency": "USD"}}})
    self.assertEqual(response.status, '200 OK')
    # but the value stays unchanged
    response = self.app.get('/tenders/{}/lots/{}'.format(self.tender_id, lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    lot = response.json['data']
    self.assertEqual(lot['value']['currency'], "GBP")
    self.assertEqual(lot['minimalStep']['currency'], "GBP")

def patch_tender_vat(self):
    # set tender VAT
    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(self.tender_id, self.tender_token),
                                   {"data": {"value": {"valueAddedTaxIncluded": True}}})

    self.assertEqual(response.status, '200 OK')

    # create lot
    response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(self.tender_id, self.tender_token),
                                  {'data': test_lots[0]})

    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    lot = response.json['data']
    self.assertTrue(lot['value']['valueAddedTaxIncluded'])

    # update tender VAT
    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(self.tender_id, self.tender_token), {
        "data":{"value": {"valueAddedTaxIncluded": False}, "minimalStep": {"valueAddedTaxIncluded": False}}})

    self.assertEqual(response.status, '200 OK')
    # log VAT is updated too
    response = self.app.get('/tenders/{}/lots/{}'.format(self.tender_id, lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    lot = response.json['data']
    self.assertFalse(lot['value']['valueAddedTaxIncluded'])

    # try to update lot VAT
    response = self.app.patch_json('/tenders/{}/lots/{}?acc_token={}'.format(self.tender_id, lot['id'], self.tender_token),
                                   {"data": {"value": {"valueAddedTaxIncluded": True}}})
    self.assertEqual(response.status, '200 OK')
    # but the value stays unchanged
    response = self.app.get('/tenders/{}/lots/{}'.format(self.tender_id, lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    lot = response.json['data']
    self.assertFalse(lot['value']['valueAddedTaxIncluded'])

    # try to update minimalStep VAT
    response = self.app.patch_json('/tenders/{}/lots/{}?acc_token={}'.format(self.tender_id, lot['id'], self.tender_token),
                                   {"data": {"minimalStep": {"valueAddedTaxIncluded": True}}})
    self.assertEqual(response.status, '200 OK')
    # but the value stays unchanged
    response = self.app.get('/tenders/{}/lots/{}'.format(self.tender_id, lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    lot = response.json['data']
    self.assertFalse(lot['minimalStep']['valueAddedTaxIncluded'])

    # try to update minimalStep VAT and value VAT in single request
    response = self.app.patch_json('/tenders/{}/lots/{}?acc_token={}'.format(self.tender_id, lot['id'], self.tender_token),{
        "data": {"value": {"valueAddedTaxIncluded": True}, "minimalStep": {"valueAddedTaxIncluded": True}}})
    self.assertEqual(response.status, '200 OK')
    # but the value stays unchanged
    response = self.app.get('/tenders/{}/lots/{}'.format(self.tender_id, lot['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    lot = response.json['data']
    self.assertFalse(lot['value']['valueAddedTaxIncluded'])
    self.assertEqual(lot['minimalStep']['valueAddedTaxIncluded'], lot['value']['valueAddedTaxIncluded'])
