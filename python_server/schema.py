import json
import copy
# import asyncio
import random

from graphene import (
    Schema, ObjectType, String, Boolean, ID, Field, Int, List, Float,
    Mutation, NonNull
)

pins = [{
    "id" : 0,
    "title" : "mona lisa",
    "link" : "",
    "image" : ""
}]

class Pin(ObjectType):
    id = Int()
    title = String()
    link = String()
    image = String()

class AddPin(Mutation):
    class Arguments:
        title = NonNull(String)
        link = NonNull(String)
        image = NonNull(String)

    Output = Int

    def mutate(self, info, title, link, image):
        id_ = len(pins)
        new_pin = {
            "id" : id_,
            "title": title,
            "link": link,
            "image": image,
        }
        pins.append(new_pin)

        # subject.on_next({
        #     "id": len(pins),
        #     "message": message,
        # })

        subject.on_next(
            Pin(**new_pin)
        )

        return id_

class Mutation(ObjectType):
    add_pin = AddPin.Field()

class Query(ObjectType):
    pins = List(Pin)

    def resolve_pins(self, info):
        pins_as_obj_list = []

        for i, pin in enumerate(pins):
            pins_as_obj_list.append(
                Pin(**pin)
                # # String("test")
                # # "test"
                # json.dumps({
                #     "id": i,
                #     "message":m,
                # })
            )

        return pins_as_obj_list

from rx import Observable, subjects

subject = subjects.Subject()

class Subscription(ObjectType):

    pin_added = Field(Pin)
    # count_seconds = Int(up_to=Int())
    # random_int = Field(RandomType)
    # new_message = NonNull(String)

    # def resolve_count_seconds(root, info, up_to=5):
    #     return Observable.interval(1000)\
    #         .map(lambda i: "{0}".format(i))\
    #         .take_while(lambda i: int(i) <= up_to)

    # def resolve_random_int(root, info):
    #     return Observable.interval(1000)\
    #         .map(lambda i: RandomType(seconds=i, random_int=random.randint(0, 500)))

    def resolve_pin_added(root, info):#, user_id):
        print("XXXXX")
        print(root)
        print(info)

        return subject

    # def resolve_new_message(root, info):#, user_id):
    #     print("XXXXX")
    #     print(root)
    #     print(info)
    #     # pass
    #     # newMessage(userId: Int!): String!
    #     # return Observable._create(1000)\
    #     #     .map(lambda i: RandomType(seconds=i, random_int=random.randint(0, 500)))

    #     return subject#.\
    #         # filter(lambda msg: msg[0] == 'authors').\
    #         # map(lambda msg: _resolve(msg[1]))

schema = Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
)