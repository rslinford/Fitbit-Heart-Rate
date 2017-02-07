from flask import Flask, request
from flask_restful import reqparse, abort, Api, Resource
import json

app = Flask(__name__)
api = Api(app)

ALOG = []

alog_filename = '2017-02-07_alog.txt'


def append_alog_entry(entry):
    ALOG.append(entry)
    with open(alog_filename, 'a') as f:
        f.write('\n')
        json.dump(entry, f)


def abort_if_entry_doesnt_exist(entry_id):
    # todo: search for entry
    if len(ALOG) == 0:
        abort(404, message="Todo {} doesn't exist".format(entry_id))

parser = reqparse.RequestParser()
parser.add_argument('task')


class ALogEntry(Resource):
    def get(self, entry_id):
        abort_if_entry_doesnt_exist(entry_id)
        # todo: lookup and return something meaningful
        return ALOG[0]

    def delete(self, entry_id):
        abort_if_entry_doesnt_exist(entry_id)
        # todo: lookup and delete the right one
        del ALOG[0]
        return '', 204

    def put(self, entry_id):
        abort_if_entry_doesnt_exist(entry_id)
        json_body = request.get_json()
        # todo: lookup and replace the right one
        ALOG[0] = json_body
        return json_body, 201


class ALog(Resource):
    def get(self):
        return ALOG

    def post(self):
        json_body = request.get_json()
        append_alog_entry(json_body)
        return json_body, 201

api.add_resource(ALog, '/alog')
api.add_resource(ALogEntry, '/alog/<entry_id>')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
