### This file handles simulation events. These allow cross-system interaction
### without entangling logic.
###
### As of the v2 overhaul, this module doesn't actually do anything, as it was
### mainly for the authority system. I'll keep it around in case it's useful
### at some point later.

import logging
from typing import TYPE_CHECKING
from collections.abc import Callable

logger = logging.getLogger(__name__)

from world.world import listeners

class Event:
    type: str
    """
    The event type that is raised by this event.
    
    This is used by a :class:`Rule` check to determine whether its effect will 
    trigger.
    """
    objects: list[object]
    """
    The game objects that are involved in this event. 
    
    Should always contain at least one item, the
    source object that triggered this event. This source should also always be 
    the first item if there are multiple.
    """
    context: dict
    """
    Any additional information necessary for a particular :class:`Rule` 
    effect. 
    
    Will probably be empty for most types; only add keys when
    absolutely necessary.
    """
    def __init__(self, type: str, objects: list[object], context: dict):
        """
        :param type: The event type that is raised by this event.
    
            This is used by a :class:`Rule` check to determine whether its 
            effect will trigger.
        :param objects: The game objects that are involved in this event. 
    
            Should always contain at least one item, the source object that 
            triggered this event. This source should also always be the first 
            item if there are multiple.
        :param context: Any additional information necessary for a particular 
            :class:`Rule` effect.
    
            Check which context items are necessary in the docs for an event
            type.
        :type type: str
        :type objects: list[object]
        :type context: dict
        """
        self.type = type
        self.objects = objects
        self.source = objects[0]
        self.context = context

class Rule:
    """
    A rule which calls a specific effect function when its check returns True.
    """
    check: Callable[["Listener", Event], bool]
    """
    A function which takes a :class:`Listener` and an :class:`Event` and 
    determines whether this rule will trigger.
    """
    effect: Callable[["Listener", Event], None]
    """
    Called by this rule when its check returns True, given the parent
    :class:`Listener` and source :class:`Event`. 
    
    The parent game object can be found through :class:`Listener`.parent.
    """
    def __init__(self, check: Callable[["Listener", Event], bool], 
                 effect: Callable[["Listener", Event], None]):
        """
        :param check: A function which takes a :class:`Listener` and an 
            :class:`Event` and determines whether this rule will trigger.
        :param effect: Called by this rule when its check returns True, given 
            the parent :class:`Listener` and source :class:`Event`. 
    
            The parent game object can be found through 
            :class:`Listener`.parent.
        :type check: Callable[[:class:`Listener`, :class:`Event`], bool]
        :type effect: Callable[[:class:`Listener`, :class:`Event`]]
        """
        
        self.check = check
        self.effect = effect

class Listener:
    """
    An object that listens for a type of :class:`Event` and modifies its parent
    game object when triggered.
    """
    parent: object
    """
    The game object referred to by this listener.
    """
    rules: list[Rule]
    """
    Every :class:`Rule` this listener is checking for each event.
    """
    def __init__(self, parent: object, rules: list[Rule]):
        """
        :param parent: The game object referred to by this listener.
        :param rules: Every :class:`Rule` this listener is checking for each 
            event.
        :type parent: object
        :type rules: list[Rule]
        """
        
        self.parent = parent
        self.rules = rules

def new_listener(parent: object, rules: list[Rule]):
    listeners.append(Listener(parent, rules))

async def event(event: Event):
    """
    Dispatches an :class:`Event`. Any :class:`Listener` whose check matches
    this event will be triggered.
    """
    for listener in listeners:
        for rule in listener.rules:
            if rule.check(listener, event):
                logger.info(f"""{listener.parent} is responding to {event}""")
                await rule.effect(listener, event)