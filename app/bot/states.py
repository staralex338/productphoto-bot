"""
FSM (Finite State Machine) states for the bot conversation flow.

Tracks where each user is in the UPLOAD → CHOOSE STYLE → GENERATE pipeline.
"""

from aiogram.fsm.state import State, StatesGroup


class GenerationFlow(StatesGroup):
    """
    States for the product photo generation flow.

    Flow:
        idle → [user sends photo] → uploading
        uploading → [photo validated] → choosing_style
        choosing_style → [style selected] → generating
        generating → [generation complete] → idle
    """

    # Waiting for user to upload a product photo
    uploading = State()

    # Photo received, waiting for style selection
    choosing_style = State()

    # Style selected, generation in progress
    generating = State()


class AdminSearch(StatesGroup):
    """State for admin searching users."""

    waiting_for_query = State()


class AdminBroadcast(StatesGroup):
    """States for admin broadcast flow."""

    waiting_for_message = State()
    waiting_for_confirmation = State()


class AdminSettings(StatesGroup):
    """States for admin settings flow."""

    waiting_for_key = State()
    waiting_for_value = State()
