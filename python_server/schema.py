import json
import copy
# import asyncio
import random

from graphene import (
    Schema, ObjectType, String, Boolean, ID, Field, Int, List, Float,
    Mutation, NonNull
)

from rx import Observable, subjects

#This example uses an in-memory list of dictionaries as a data store.
pins = [{
    "id" : 0,
    "title" : "mona lisa",
    "link" : "",
    "image" : ""
}]

#Create a subject to handle pin_added subscriptions
pin_added_subject = subjects.Subject()

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
        #Get a new ID
        id_ = len(pins)

        #Pack the new pin object, and "store" to the pin list.
        new_pin = {
            "id" : id_,
            "title": title,
            "link": link,
            "image": image,
        }
        pins.append(new_pin)

        #Notify subscribers that a pin has been added.
        pin_added_subject.on_next(
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
            )

        return pins_as_obj_list

class Subscription(ObjectType):

    pin_added = Field(Pin)

    def resolve_pin_added(root, info):
        return pin_added_subject

schema = Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
)