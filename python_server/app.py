import os
import json
from collections import namedtuple

from flask import Flask
from flask_cors import CORS
from flask_graphql import GraphQLView
from flask_sockets import Sockets

from rx import Observable
from graphql_ws.constants import GQL_DATA, GQL_COMPLETE
from graphql_ws.gevent import GeventSubscriptionServer, SubscriptionObserver

from gevent import pywsgi
from graphql.execution.executors.gevent import GeventExecutor as Executor
from geventwebsocket.handler import WebSocketHandler


from schema import schema
from playground import TEMPLATE as PLAYGROUND_TEMPLATE


class DagsterSubscriptionServer(GeventSubscriptionServer):
    '''Subscription server that is able to handle non-subscription commands'''

    def __init__(self, middleware=None, **kwargs):
        self.middleware = middleware or []
        super(GeventSubscriptionServer, self).__init__(**kwargs)

    def execute(self, request_context, params):
        # print("execute")
        # https://github.com/graphql-python/graphql-ws/issues/7
        params['context_value'] = request_context
        params['middleware'] = self.middleware
        return super(GeventSubscriptionServer, self).execute(request_context, params)

    def send_execution_result(self, connection_context, op_id, execution_result):
        # print("send_execution_result")
        # print(op_id)
        if execution_result == GQL_COMPLETE:
            return self.send_message(connection_context, op_id, GQL_COMPLETE, {})
        else:
            result = self.execution_result_to_dict(execution_result)
            return self.send_message(connection_context, op_id, GQL_DATA, result)

    def on_start(self, connection_context, op_id, params):
        # print("on_start")
        try:
            execution_result = self.execute(connection_context.request_context, params)
            if not isinstance(execution_result, Observable):
                observable = Observable.of(execution_result, GQL_COMPLETE)
            else:
                observable = execution_result
            observable.subscribe(
                SubscriptionObserver(
                    connection_context, op_id, self.send_execution_result, self.send_error,
                    self.on_close
                )
            )
        except Exception as e:
            self.send_error(connection_context, op_id, str(e))

    # def on_connect(self, connection_context, payload):
    #     # print("on_connect")
    #     return
    #     # raise NotImplementedError("on_connect method not implemented")
    #     # return {"type": "connection_init", "payload": {}} #This comes from the client
    #     return {"type": "connection_ack"}


def dagster_graphql_subscription_view(subscription_server):

    def view(ws):
        subscription_server.handle(ws)
        return []

    return view

class DagsterGraphQLView(GraphQLView):
    def __init__(self, **kwargs):##context, **kwargs):
        super(DagsterGraphQLView, self).__init__(**kwargs)

app = Flask(__name__)
sockets = Sockets(app)
app.app_protocol = lambda environ_path_info: 'graphql-ws'

# app.add_url_rule('/graphql', view_func=view_func)

subscription_server = DagsterSubscriptionServer(
    schema=schema,
)

app.add_url_rule(
    '/graphql',
    'graphql',
    DagsterGraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True,
        # XXX(freiksenet): Pass proper ws url
        graphiql_template=PLAYGROUND_TEMPLATE,
        executor=Executor(),
    ),
)

sockets.add_url_rule(
    '/graphql',
    'graphql',
    # '/subscriptions',
    # 'subscriptions',
    dagster_graphql_subscription_view(subscription_server),
)

CORS(app, resources={r'/graphql': {'origins': '*'}})

if __name__ == '__main__':

    host = '127.0.0.1'
    port = 5061

    server = pywsgi.WSGIServer((host, port), app, handler_class=WebSocketHandler,)
    print('Serving on http://{host}:{port}'.format(host=host, port=port))
    server.serve_forever()