from aiogram.dispatcher.filters.state import State, StatesGroup


class WelcomePost(StatesGroup):
    wl_post1 = State()


class MassSend(StatesGroup):
    MSend = State()
    MSend1 = State()


class EditButtonText(StatesGroup):
    EditButtonText1 = State()
    EditButtonText2 = State()


class EditButtonResponseText(StatesGroup):
    EditButtonResponseText1 = State()
    EditButtonResponseText2 = State()


class PlannedMailing(StatesGroup):
    PlannedMailing1 = State()
    PlannedMailing2 = State()
    PlannedMailing3 = State()
    PlannedMailing4 = State()
