# app/helpers/ma_schema_validators.py

from flask import current_app
import mimetypes
from marshmallow import ValidationError
from marshmallow.validate import Validator
import re
import typing


def not_blank(data):
    """Custom marshmallow validator for empty string data
    """
    if not data:
        raise ValidationError({"status": "2", "msg": "Field can't be blank"})


def only_letters(data):
    """Custom marshmallow validator for only letters
    """
    if not re.match("^[a-zA-ZñÑáéíóúÁÉÍÓÚ ]*$", data):
        raise ValidationError(
            {"status": "7", "msg": "Field accept only letters"})


def only_numbers(data):
    """Custom marshmallow validator for only numbers
    """
    if not re.match("^[0-9]*$", data):
        raise ValidationError(
            {"status": "8", "msg": "Field accept only numbers"})


def validate_image(data):
    if data:
        mimetype, encoding = mimetypes.guess_type(data)
        if not (mimetype and mimetype.startswith('image')):
            raise ValidationError(
                {"status": "9", "msg": "Invalid image field"})


def validate_video(data):

    #mimetype,encoding = mimetypes.guess_type(data)
    # if not (mimetype and mimetype.startswith('video')):
    #    raise ValidationError("Invalid video url")
    return True


def validate_email(data):
    if not re.search(r'[^@]+@[^@]+\.[^@]+', data):
        raise ValidationError({"status": "1", "msg": "Invalid email address"})


def validate_url(data):

    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        # domain...
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    if not re.match(regex, data):
        raise ValidationError({"status": "10", "msg": "Invalid url address"})


class OneOf(Validator):
    """Validator which succeeds if ``value`` is a member of ``choices``.

    :param choices: A sequence of valid values.
    :param labels: Optional sequence of labels to pair with the choices.
    """

    default_message = "Must be one of: {choices}."

    def __init__(
        self,
        choices: typing.Iterable,
        labels: typing.Iterable[str] = None,
        *,
        error: str = None
    ):
        self.choices = choices
        self.choices_text = ", ".join(str(choice) for choice in self.choices)
        self.labels = labels if labels is not None else []
        self.labels_text = ", ".join(str(label) for label in self.labels)
        self.error = error or self.default_message  # type: str

    def __call__(self, value) -> str:
        if value and value not in self.choices:
            raise ValidationError(
                {"status": "11", "msg": "Not a valid choice"})
        if not value:
            value = None
        return value


class Range(Validator):
    """Validator which succeeds if the value passed to it is within the specified
    range. If ``min`` is not specified, or is specified as `None`,
    no lower bound exists. If ``max`` is not specified, or is specified as `None`,
    no upper bound exists. The inclusivity of the bounds (if they exist) is configurable.
    If ``min_inclusive`` is not specified, or is specified as `True`, then
    the ``min`` bound is included in the range. If ``max_inclusive`` is not specified,
    or is specified as `True`, then the ``max`` bound is included in the range.

    :param min: The minimum value (lower bound). If not provided, minimum
        value will not be checked.
    :param max: The maximum value (upper bound). If not provided, maximum
        value will not be checked.
    :param min_inclusive: Whether the `min` bound is included in the range.
    :param max_inclusive: Whether the `max` bound is included in the range.
    """

    def __init__(
        self,
        min=None,
        max=None,
        *,
        min_inclusive: bool = True,
        max_inclusive: bool = True,
        error: str = None
    ):
        self.min = min
        self.max = max
        self.error = error
        self.min_inclusive = min_inclusive
        self.max_inclusive = max_inclusive

    def __call__(self, value) -> typing.Any:
        if value and self.min is not None and (
            value < self.min if self.min_inclusive else value <= self.min
        ):
            raise ValidationError({"status": "12", "msg": "Out of range"})

        if value and self.max is not None and (
            value > self.max if self.max_inclusive else value >= self.max
        ):
            raise ValidationError({"status": "12", "msg": "Out of range"})

        return value


class Length(Validator):
    """Validator which succeeds if the value passed to it has a
    length between a minimum and maximum. Uses len(), so it
    can work for strings, lists, or anything with length.

    :param min: The minimum length. If not provided, minimum length
        will not be checked.
    :param max: The maximum length. If not provided, maximum length
        will not be checked.
    :param equal: The exact length. If provided, maximum and minimum
        length will not be checked.
    """

    def __init__(
        self, min: int = None, max: int = None, *, equal: int = None, error: str = None
    ):
        if equal is not None and any([min, max]):
            raise ValueError(
                "The `equal` parameter was provided, maximum or "
                "minimum parameter must not be provided."
            )

        self.min = min
        self.max = max
        self.error = error
        self.equal = equal

    def __call__(self, value) -> typing.Any:
        length = len(value)

        if self.equal is not None:
            if length != self.equal:
                raise ValidationError(
                    {"status": "13", "msg": "Invalid length"})
            return value

        if self.min is not None and length < self.min:
            raise ValidationError({"status": "13", "msg": "Invalid length"})

        if self.max is not None and length > self.max:
            raise ValidationError({"status": "13", "msg": "Invalid length"})

        return value
