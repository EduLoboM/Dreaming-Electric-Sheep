"""
This module implements a feature inspired by "Model Binding" in ASP.NET web framework.
It provides a strategy to have request parameters read and injected into request
handlers. This feature is also useful to generate OpenAPI Documentation (Swagger)
automatically.

See:
    https://www.neoteroi.dev/blacksheep/binders/
"""

from abc import abstractmethod
from collections.abc import Iterable as IterableAbc
from functools import partial
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    ForwardRef,
    Generic,
    Sequence,
    Type,
    TypeVar,
)
from urllib.parse import unquote
from uuid import UUID

import msgspec
from guardpost import Identity
from rodi import CannotResolveTypeException, ContainerProtocol

try:
    from pydantic import BaseModel
except ImportError:
    BaseModel = ()  # type: ignore

from dreaming_electric_sheep.contents import FormPart
from dreaming_electric_sheep.exceptions import (
    BadRequest,
    BadRequestFormat,
    UnprocessableEntity,
    UnsupportedMediaType,
)
from dreaming_electric_sheep.messages import Request
from dreaming_electric_sheep.server.bindings.converters import (
    class_converters,
    converters,
)
from dreaming_electric_sheep.server.routing import Router, URLResolver
from dreaming_electric_sheep.server.websocket import WebSocket
from dreaming_electric_sheep.settings.json import json_settings
from dreaming_electric_sheep.url import URL

T = TypeVar("T")
TypeOrName = Type | str


empty = object()


class BindingException(Exception):
    pass


class BinderAlreadyDefinedException(BindingException):
    def __init__(self, class_name: str, overriding_class_name: str) -> None:
        super().__init__(
            f"There is already a binder defined for {class_name}. "
            f"The second type is: {overriding_class_name}"
        )


class NameAliasAlreadyDefinedException(BindingException):
    def __init__(self, alias: str, overriding_class_name: str) -> None:
        super().__init__(
            f"There is already a name alias defined for '{alias}', "
            f"the second type is: {overriding_class_name}"
        )
        self.alias = alias


class TypeAliasAlreadyDefinedException(BindingException):
    def __init__(self, alias: Any, overriding_class_name: str) -> None:
        super().__init__(
            f"There is already a type alias defined for '{alias.__name__}', "
            f"the second type is: {overriding_class_name}"
        )
        self.alias = alias


class BinderNotRegisteredForValueType(BindingException):
    def __init__(self, value_type: Type["BoundValue"]) -> None:
        super().__init__(
            f"There is no binder to handle: {value_type}. "
            f"To resolve, define a Binder class with `handle` class attribute "
            f"referencing {value_type}."
        )


class BinderMeta(type):
    handlers: dict[Type[Any], Type["Binder"]] = {}
    aliases: dict[Any, Callable[[ContainerProtocol], "Binder"]] = {}

    def __init__(cls, name, bases, attr_dict):
        super().__init__(name, bases, attr_dict)
        handle = getattr(cls, "handle", None)
        name_alias = getattr(cls, "name_alias", None)
        type_alias = getattr(cls, "type_alias", None)

        if name_alias:
            if name_alias in cls.aliases:
                raise NameAliasAlreadyDefinedException(name_alias, name)
            cls.aliases[name_alias] = cls.from_alias  # type: ignore

        if type_alias:
            if type_alias in cls.aliases:
                raise TypeAliasAlreadyDefinedException(type_alias, name)
            cls.aliases[type_alias] = cls.from_alias  # type: ignore

        if handle:
            if handle in cls.handlers:
                raise BinderAlreadyDefinedException(handle, name)
            cls.handlers[handle] = cls  # type: ignore


class BoundValue(Generic[T]):
    """Base class for parameters that are bound for a web request."""

    name: str | None = None

    def __init__(self, value: T) -> None:
        self._value = value

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self._value})>"

    @property
    def value(self) -> T:
        return self._value


class FromHeader(BoundValue[T]):
    """
    A parameter obtained from request headers.
    """


class FromQuery(BoundValue[T]):
    """A parameter obtained from URL query parameters."""


class FromCookie(BoundValue[T]):
    """
    A parameter obtained from a cookie.
    """


class FromServices(BoundValue[T]):
    """
    A parameter obtained from configured application services.
    """


class FromJSON(BoundValue[T]):
    """
    A parameter obtained from JSON request body.
    If value type is `dict`, `typing.Dict`, or not specified, the deserialized JSON
    is returned without any cast.
    """

    default_value_type = dict


FromJson = FromJSON  # for backward compatibility


class FromText(BoundValue[str]):
    """
    A parameter obtained from the request body as plain text.
    """


class FromBytes(BoundValue[bytes]):
    """
    A parameter obtained from the request body as raw bytes.
    """


class FromForm(BoundValue[T]):
    """
    A parameter obtained from Form request body: either
    application/x-www-form-urlencoded or multipart/form-data.

    Use `FromForm[T]` when you need to bind complex structured data from
    forms, including a mix of regular fields, nested objects, and
    file uploads (represented as `FileBuffer` fields).

    When to use:
    - FromForm[T]: For complex types with mixed regular fields and files
    - FromFiles: For simple array of uploaded files without structure

    Example:
        @dataclass
        class UserProfile:
            name: str
            email: str
            avatar: FileBuffer

        @app.router.post("/profile")
        async def create_profile(data: FromForm[UserProfile]):
            # data.value.name and data.value.email are strings
            # data.value.avatar is the uploaded file as bytes
            return {"status": "created"}
    """

    default_value_type = dict


class FromXML(BoundValue[T]):
    """
    A parameter obtained from an XML request body (``application/xml`` or ``text/xml``).

    Requires ``defusedxml`` for safe parsing against common XML attacks (XXE, entity
    expansion, DTD injection). Install it with::

        pip install dreaming-electric-sheep[xml]

    The root element tag is ignored; its child elements are mapped to model fields by
    name.  All standard field-type coercions (int, float, datetime, UUID …) apply via
    the same converter chain used by JSON and form binders.
    """

    default_value_type = dict


class FromBody(BoundValue[T]):
    """
    A parameter obtained from the request body, accepting multiple content types.
    By default accepts application/json and application/x-www-form-urlencoded /
    multipart/form-data. For explicit format control use a union annotation such as
    ``FromJSON[T] | FromForm[T]``, which is handled identically at runtime.
    """

    default_value_type = dict


class FromFiles(BoundValue[list[FormPart]]):
    """
    A parameter obtained from multipart/form-data files.
    """


class FromRoute(BoundValue[T]):
    """
    A parameter obtained from URL path fragment.
    """


class ClientInfo(BoundValue[tuple[str, int]]):
    """
    Client ip and port information obtained from a request scope.
    """


class ServerInfo(BoundValue[tuple[str, int]]):
    """
    Server ip and port information obtained from a request scope.
    """


class RequestUser(BoundValue[Identity]):
    """
    Returns the identity of the user that initiated the web request.
    This value is obtained from the configured authentication strategy.
    """


class RequestURL(BoundValue[URL]):
    """
    Returns the URL of the request.
    """


class RequestMethod(BoundValue[str]):
    """
    Returns the HTTP Method of the request.
    """


def _implicit_default(obj: "Binder"):
    try:
        return issubclass(obj.handle, BoundValue)
    except (AttributeError, TypeError):
        return False


class Binder(metaclass=BinderMeta):  # type: ignore
    handle: ClassVar[Type[Any]]
    name_alias: ClassVar[str] = ""
    type_alias: ClassVar[Any] = None

    def __init__(
        self,
        expected_type: Any,
        name: str = "",
        implicit: bool = False,
        required: bool = True,
        converter: Callable | None = None,
    ):
        self._implicit = implicit or not _implicit_default(self)
        self.parameter_name = name
        self.expected_type = expected_type
        self.required = required
        self.root_required = True
        self.converter = converter
        self.default: Any = empty

    @classmethod
    def from_alias(cls, services: ContainerProtocol):
        return cls()  # type: ignore

    @property
    def implicit(self) -> bool:
        return self._implicit

    def get_type_for_generic_iterable(self, expected_type):
        if expected_type in {list, tuple, set}:
            return expected_type

        origin = expected_type.__origin__
        if origin in {list, tuple, set}:
            return origin
        # here we cannot make something perfect: if the user of the library
        # wants something better,
        # a converter should be specified when configuring binders; here the
        # code defaults to list
        # for all abstract types (typing.Sequence, Set, etc.) even though not perfect
        return list

    def is_generic_iterable_annotation(self, param_type):
        return hasattr(param_type, "__origin__") and (
            param_type.__origin__ in {list, tuple, set}
            or self._issubclass(param_type.__origin__, IterableAbc)
        )

    @staticmethod
    def _issubclass(clstype, class_or_tuple) -> bool:
        try:
            return issubclass(clstype, class_or_tuple)
        except TypeError:
            return False

    def generic_iterable_annotation_item_type(self, param_type):
        try:
            item_type = param_type.__args__[0]
        except (IndexError, AttributeError):
            return str
        return item_type

    def get_parameter_sync(self, request: Request) -> Any:
        """
        Synchronously gets a parameter to be passed to a request handler.
        """
        try:
            value = self.get_value_sync(request)
        except UnicodeDecodeError as decode_error:
            raise BadRequest(
                f"Unicode decode error. "
                f"Cannot decode the request content using: {decode_error.encoding}. "
                "Ensure the request content is encoded using the encoding declared in "
                "the Content-Type request header."
            )
        except ValueError as value_error:
            raise BadRequest("Invalid parameter.") from value_error

        if value is None and self.default is not empty:
            return self.default

        if self.implicit:
            return value

        if self.root_required is False and value is None:
            return None

        return self.handle(value)

    def get_value_sync(self, request: Request) -> Any:
        """Synchronously gets a value from the given request object."""
        raise NotImplementedError(
            "This binder does not support synchronous evaluation."
        )

    async def get_parameter(self, request: Request) -> Any:
        """
        Gets a parameter to be passed to a request handler.

        The parameter can be equal to the value, when a binder is applied implicitly,
        or a BoundValue[T] when a binder is applied explicitly.

        Example:

            @app("/:id")
            def example(id: FromRoute[str]):
                # here id is an instance of FromRoute because the annotation is
                # explicit, the value is read with `id.value`
                ...

            @app("/:id")
            def example(id: str):
                # here id is directly a `str` because the annotation is
                # applied implicitly
                ...
        """
        try:
            value = await self.get_value(request)
        except UnicodeDecodeError as decode_error:
            raise BadRequest(
                f"Unicode decode error. "
                f"Cannot decode the request content using: {decode_error.encoding}. "
                "Ensure the request content is encoded using the encoding declared in "
                "the Content-Type request header."
            )
        except ValueError as value_error:
            raise BadRequest("Invalid parameter.") from value_error

        if value is None and self.default is not empty:
            return self.default

        if self.implicit:
            return value

        if self.root_required is False and value is None:
            # This is the case of:
            # BoundValue[T | None]
            return None

        return self.handle(value)

    @abstractmethod
    async def get_value(self, request: Request) -> Any:
        """Gets a value from the given request object."""


def get_binder_by_type(bound_value_type: Type[BoundValue]) -> Type[Binder]:
    origin = bound_value_type.__dict__.get("__origin__")

    if origin and issubclass(origin, BoundValue):
        # In this case, it's a BoundValue of specified type
        bound_value_type = origin

    if bound_value_type in Binder.handlers:
        return Binder.handlers[bound_value_type]

    for cls in bound_value_type.__bases__:
        if cls in Binder.handlers:
            return Binder.handlers[cls]

    raise BinderNotRegisteredForValueType(bound_value_type)


class MissingBodyError(BadRequest):
    def __init__(self):
        super().__init__("Missing body payload")


class MissingParameterError(BadRequest):
    def __init__(self, name: str, source: str):
        super().__init__(f"Missing {source} parameter `{name}`")


class InvalidRequestBody(BadRequest):
    def __init__(self, description: str = "Invalid body payload"):
        super().__init__(description)


class MissingConverterError(Exception):
    def __init__(self, expected_type, binder_type):
        super().__init__(
            f"A default converter for type `{str(expected_type)}` "
            f"is not configured. "
            f"Please define a converter method for this binder "
            f"({binder_type.__name__})."
        )


def get_default_class_converter(expected_type):
    for converter in class_converters:
        if converter.can_convert(expected_type):
            return partial(converter.convert, expected_type=expected_type)

    def default_converter(data):
        if isinstance(data, dict):
            return expected_type(**data)
        else:
            # list, simple type
            return expected_type(data)

    return default_converter


class BodyBinder(Binder):
    _excluded_methods = {"GET", "HEAD", "TRACE"}

    def __init__(
        self,
        expected_type,
        name: str = "body",
        implicit: bool = False,
        required: bool = False,
        converter: Callable | None = None,
    ):
        super().__init__(expected_type, name, implicit, required, None)

        if not converter:
            converter = self.get_default_binder_for_body(expected_type)  # type: ignore
        self.converter = converter

    def _get_default_converter_single(self, expected_type):
        for converter in converters:
            if converter.can_convert(expected_type):
                return partial(converter.convert, expected_type=expected_type)
        return get_default_class_converter(expected_type)

    def _get_default_converter_for_iterable(self, expected_type):
        generic_type = self.get_type_for_generic_iterable(expected_type)
        item_type = self.generic_iterable_annotation_item_type(expected_type)

        if isinstance(item_type, ForwardRef):  # pragma: no cover
            from dreaming_electric_sheep.server.normalization import (
                UnsupportedForwardRefInSignatureError,
            )

            raise UnsupportedForwardRefInSignatureError(expected_type)

        item_converter = self._get_default_converter_single(item_type)

        def list_converter(values):
            if not isinstance(values, list):
                raise BadRequest("Invalid input: expected a list of objects.")

            return generic_type(item_converter(value) for value in values)

        return list_converter

    def get_default_binder_for_body(self, expected_type: Type):
        if self.is_generic_iterable_annotation(expected_type) or expected_type in {
            list,
            set,
            tuple,
        }:
            if expected_type is Dict or expected_type.__origin__ is dict:
                return lambda value: dict(**value)
            return self._get_default_converter_for_iterable(expected_type)

        return get_default_class_converter(expected_type)

    @property
    @abstractmethod
    def content_type(self) -> str:
        """Returns the content type related to this binder"""

    @abstractmethod
    def matches_content_type(self, request: Request) -> bool:
        raise NotImplementedError()

    @abstractmethod
    async def read_data(self, request: Request) -> Any:
        raise NotImplementedError()

    async def get_value(self, request: Request) -> T | None:
        if request.method not in self._excluded_methods and self.matches_content_type(
            request
        ):
            data = await self.read_data(request)

            if not data:
                raise MissingBodyError()

            return self.parse_value(data)

        if self.required:
            if self.default is not empty:
                # very unlikely: this is to support user defined default parameters
                return None

            if not request.has_body():
                raise MissingBodyError()

            raise InvalidRequestBody("Expected request content")

        return None

    def parse_value(self, data: dict):
        try:
            return self.converter(data)
        except TypeError as type_error:
            raise BadRequest(
                "Bad Request: invalid parameter in request payload."
            ) from type_error
        except ValueError as value_error:
            raise InvalidRequestBody(str(value_error)) from value_error


_DECODER_CACHE: dict[tuple[Any, Any], msgspec.json.Decoder] = {}
_ENCODER_CACHE: dict[Any, msgspec.json.Encoder] = {}


def get_precompiled_decoder(
    target_type: Any = Any,
    dec_hook: Callable[[type, Any], Any] | None = None,
) -> msgspec.json.Decoder:
    """
    Returns a pre-compiled msgspec.json.Decoder for the given type and dec_hook,
    caching compiled decoders across endpoints to eliminate dynamic type inspection.
    """
    if target_type in (None, empty):
        target_type = dict

    key = (target_type, dec_hook)
    decoder = _DECODER_CACHE.get(key)
    if decoder is not None:
        return decoder

    def composite_dec_hook(tp, obj):
        if dec_hook is not None:
            try:
                res = dec_hook(tp, obj)
                if res is not None:
                    return res
            except Exception:
                pass

        if isinstance(tp, type):
            if issubclass(tp, UUID) and isinstance(obj, str):
                return UUID(obj)
            try:
                from pydantic import BaseModel

                if issubclass(tp, BaseModel):
                    return tp.model_validate(obj)
            except (ImportError, TypeError):
                pass
            if hasattr(tp, "convert") and callable(getattr(tp, "convert")):
                return tp.convert(obj)
            if hasattr(tp, "__dataclass_fields__") or issubclass(tp, msgspec.Struct):
                return obj
            try:
                conv = get_default_class_converter(tp)
                return conv(obj)
            except (TypeError, ValueError):
                raise
            except Exception:
                pass

        return obj

    try:
        decoder = msgspec.json.Decoder(target_type, dec_hook=composite_dec_hook)
    except Exception:
        decoder = msgspec.json.Decoder(dec_hook=composite_dec_hook)

    _DECODER_CACHE[key] = decoder
    return decoder


def get_precompiled_encoder(
    enc_hook: Callable[[Any], Any] | None = None,
) -> msgspec.json.Encoder:
    """
    Returns a pre-compiled msgspec.json.Encoder for the given enc_hook,
    caching compiled encoders across endpoints.
    """
    encoder = _ENCODER_CACHE.get(enc_hook)
    if encoder is not None:
        return encoder

    def composite_enc_hook(obj):
        if enc_hook is not None:
            try:
                res = enc_hook(obj)
                if res is not None:
                    return res
            except Exception:
                pass

        if isinstance(obj, UUID):
            return str(obj)
        try:
            from pydantic import BaseModel

            if isinstance(obj, BaseModel):
                return obj.model_dump()
        except (ImportError, TypeError):
            pass

        return obj

    try:
        encoder = msgspec.json.Encoder(enc_hook=composite_enc_hook)
    except Exception:
        encoder = msgspec.json.Encoder()

    _ENCODER_CACHE[enc_hook] = encoder
    return encoder


class JSONBinder(BodyBinder):
    handle = FromJSON

    def __init__(
        self,
        expected_type: Type = empty,
        name: str = "",
        implicit: bool = False,
        required: bool = False,
        default: Any = empty,
        converter: Callable | None = None,
        dec_hook: Callable[[type, Any], Any] | None = None,
    ):
        super().__init__(expected_type, name, implicit, required, converter)
        self.default = default
        self.dec_hook = dec_hook
        self.decoder = self._build_decoder(
            expected_type,
            dec_hook,
            converter is not None
            and converter != self.get_default_binder_for_body(expected_type),
        )

    @property
    def converter(self):
        return getattr(self, "_converter", None)

    @converter.setter
    def converter(self, value):
        self._converter = value
        if hasattr(self, "expected_type"):
            has_custom = (
                value is not None
                and value != self.get_default_binder_for_body(self.expected_type)
            )
            self.decoder = self._build_decoder(
                self.expected_type, getattr(self, "dec_hook", None), has_custom
            )

    def _build_decoder(
        self,
        expected_type: Type,
        custom_dec_hook: Callable | None = None,
        has_custom_converter: bool = False,
    ):
        if has_custom_converter:
            target_type = Any
        else:
            target_type = expected_type

        return get_precompiled_decoder(target_type, custom_dec_hook)

    @property
    def content_type(self) -> str:
        return "application/json"

    def matches_content_type(self, request: Request) -> bool:
        return request.declares_json()

    async def read_data(self, request: Request) -> Any:
        return await request.read_raw()

    async def get_value(self, request: Request) -> T | None:
        if request.method not in self._excluded_methods and self.matches_content_type(
            request
        ):
            raw_data = await request.read_raw()

            if not raw_data:
                if not self.required or self.default is not empty:
                    return self.default if self.default is not empty else None
                raise MissingBodyError()

            charset = request.charset or "utf8"
            if charset.lower() not in ("utf-8", "utf8", "ascii"):
                try:
                    text = raw_data.decode(charset)
                    raw_data = text.encode("utf-8")
                except UnicodeDecodeError as decode_error:
                    raise BadRequest(
                        f"Unicode decode error. Cannot decode the request content using: {decode_error.encoding}. "
                        "Ensure the request content is encoded using the encoding declared in the Content-Type request header."
                    )

            if json_settings.has_custom_loads:
                try:
                    text = raw_data.decode(charset)
                    data = json_settings.loads(text)
                    if (
                        self.converter
                        and self.converter
                        != self.get_default_binder_for_body(self.expected_type)
                    ):
                        return self.parse_value(data)
                    return data
                except (ValueError, TypeError) as err:
                    raise BadRequestFormat(f"Cannot parse content as JSON: {err}", err)

            try:
                data = self.decoder.decode(raw_data)
                if (
                    self.converter
                    and self.converter
                    != self.get_default_binder_for_body(self.expected_type)
                ):
                    return self.parse_value(data)
                return data
            except UnicodeDecodeError as decode_error:
                charset_name = (
                    request.charset or decode_error.encoding or "utf-8"
                ).lower()
                raise BadRequest(
                    f"Unicode decode error. Cannot decode the request content using: {charset_name}. "
                    "Ensure the request content is encoded using the encoding declared in the Content-Type request header."
                )
            except msgspec.ValidationError as validation_error:
                err_str = str(validation_error)
                if "codec can't decode" in err_str or "UnicodeDecodeError" in err_str:
                    charset_name = (request.charset or "utf-8").lower()
                    raise BadRequest(
                        f"Unicode decode error. Cannot decode the request content using: {charset_name}. "
                        "Ensure the request content is encoded using the encoding declared in the Content-Type request header."
                    )
                tp = self.expected_type
                if tp not in (None, empty):
                    try:
                        raw_obj = msgspec.json.decode(raw_data)
                        if (
                            self.converter
                            and self.converter != self.get_default_binder_for_body(tp)
                        ):
                            return self.parse_value(raw_obj)
                        conv = get_default_class_converter(tp)
                        val = conv(raw_obj)
                        return val
                    except (MissingBodyError,):
                        raise
                    except Exception:
                        pass
                raise UnprocessableEntity(
                    f"Validation error: {validation_error}",
                    details=str(validation_error),
                )
            except msgspec.DecodeError as decode_error:
                err_str = str(decode_error)
                if "codec can't decode" in err_str or "UnicodeDecodeError" in err_str:
                    charset_name = (request.charset or "utf-8").lower()
                    raise BadRequest(
                        f"Unicode decode error. Cannot decode the request content using: {charset_name}. "
                        "Ensure the request content is encoded using the encoding declared in the Content-Type request header."
                    )
                content_type = request.content_type()
                if content_type and b"json" in content_type:
                    raise BadRequestFormat(
                        f"Declared Content-Type is {content_type.decode()} but "
                        f"the content cannot be parsed as JSON: {decode_error}",
                        decode_error,
                    )
                raise BadRequestFormat(
                    f"Cannot parse content as JSON: {decode_error}", decode_error
                )
            except (TypeError, ValueError) as value_error:
                raise UnprocessableEntity(
                    f"Validation error: {value_error}",
                    details=str(value_error),
                )

        if self.required:
            if self.default is not empty:
                return None

            if not request.has_body():
                raise MissingBodyError()

            raise InvalidRequestBody("Expected request content")

        return None


JsonBinder = JSONBinder


class FormBinder(BodyBinder):
    """
    Extracts a model from form content, either
    application/x-www-form-urlencoded, or multipart/form-data.
    """

    handle = FromForm

    @property
    def content_type(self) -> str:
        return "multipart/form-data;application/x-www-form-urlencoded"

    def matches_content_type(self, request: Request) -> bool:
        return request.declares_content_type(
            b"application/x-www-form-urlencoded"
        ) or request.declares_content_type(b"multipart/form-data")

    async def read_data(self, request: Request) -> Any:
        return await request.form()


class TextBinder(BodyBinder):
    handle = FromText

    @property
    def content_type(self) -> str:
        return "text/plain"

    def matches_content_type(self, request: Request) -> bool:
        return True

    def parse_value(self, data: str):
        return data  # No need for parsing

    async def read_data(self, request: Request) -> Any:
        return await request.text()


def _element_to_dict(element) -> dict:
    """Recursively convert an ElementTree element to a plain dict.

    - Strips XML namespaces from tag names.
    - Multiple sibling elements with the same tag are collected into a list.
    - Attributes of the element are merged into the dict.
    """
    result: dict = {}

    # Include element attributes first so child tags can override them if needed
    for attr_name, attr_value in element.attrib.items():
        if "}" in attr_name:
            attr_name = attr_name.split("}", 1)[1]
        result[attr_name] = attr_value

    for child in element:
        tag = child.tag
        if "}" in tag:
            tag = tag.split("}", 1)[1]

        child_value = _element_to_dict(child) if len(child) > 0 else child.text

        if tag in result:
            existing = result[tag]
            if not isinstance(existing, list):
                result[tag] = [existing]
            result[tag].append(child_value)
        else:
            result[tag] = child_value

    return result


class XMLBinder(BodyBinder):
    """
    Extracts a model from an XML request body (``application/xml`` or ``text/xml``).

    Uses ``defusedxml`` to protect against XXE injection, entity expansion (billion
    laughs), and DTD-based attacks.  Install the extra with::

        pip install dreaming-electric-sheep[xml]

    The root element tag is ignored; its direct children are mapped to model fields by
    name.  The same type-coercion converters used by the JSON and form binders apply,
    so ``int``, ``float``, ``datetime``, ``UUID``, and other annotated field types are
    automatically coerced from their string representation.
    """

    handle = FromXML

    @property
    def content_type(self) -> str:
        return "application/xml;text/xml"

    def matches_content_type(self, request: Request) -> bool:
        return request.declares_content_type(
            b"application/xml"
        ) or request.declares_content_type(b"text/xml")

    async def read_data(self, request: Request) -> Any:
        raw = await request.read()
        if not raw:
            return None
        return self._parse_xml(raw)

    @staticmethod
    def _parse_xml(content: bytes) -> dict:
        try:
            import defusedxml.ElementTree as _ET  # type: ignore[import]
            from defusedxml import DefusedXmlException  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "defusedxml is required for safe XML parsing. "
                "Install it with: pip install dreaming-electric-sheep[xml]"
            ) from exc

        try:
            root = _ET.fromstring(content)
        except DefusedXmlException:
            raise  # security violations (XXE, entity expansion, DTD) propagate as-is
        except Exception as exc:
            raise InvalidRequestBody(f"Invalid XML: {exc}") from exc

        return _element_to_dict(root)


class MultiFormatBodyBinder(BodyBinder):
    """
    A BodyBinder that accepts multiple content types by delegating to a list of inner
    BodyBinders. The first inner binder whose ``matches_content_type`` returns True is
    used to read and parse the request body.

    Instances are created automatically by the normalization layer when a union of
    body-binder annotations is used (e.g. ``FromJSON[T] | FromForm[T]``), or when
    ``FromBody[T]`` is used.
    """

    def __init__(
        self,
        inner_binders: "list[BodyBinder]",
        expected_type=None,
        name: str = "body",
        implicit: bool = False,
        required: bool = False,
    ):
        # Pass a no-op converter so BodyBinder.__init__ doesn't build one unnecessarily;
        # get_value is fully overridden and never calls self.converter.
        super().__init__(
            expected_type
            or (inner_binders[0].expected_type if inner_binders else object),
            name,
            implicit,
            required,
            converter=lambda data: data,
        )
        self.inner_binders = inner_binders

    @property
    def content_type(self) -> str:
        return ";".join(b.content_type for b in self.inner_binders)

    def matches_content_type(self, request: Request) -> bool:
        return any(b.matches_content_type(request) for b in self.inner_binders)

    async def read_data(self, request: Request) -> Any:  # pragma: no cover
        raise NotImplementedError()

    async def get_value(self, request: Request) -> Any:
        if request.method in self._excluded_methods:
            return None
        for binder in self.inner_binders:
            if binder.matches_content_type(request):
                return await binder.get_value(request)
        if self.required:
            if not request.has_body():
                raise MissingBodyError()
            raise UnsupportedMediaType(
                f"None of the supported content types matched the request. "
                f"Accepted: {', '.join(b.content_type for b in self.inner_binders)}"
            )
        return None


class FromBodyBinder(MultiFormatBodyBinder):
    """
    Binder for ``FromBody[T]``. By default accepts only JSON bodies.
    To support additional formats, configure the ``binder_types`` class attribute::

        FromBodyBinder.binder_types = [JSONBinder, FormBinder]
    """

    handle = FromBody
    binder_types: list[type[BodyBinder]] = [JSONBinder]

    def __init__(
        self,
        expected_type,
        name: str = "body",
        implicit: bool = False,
        required: bool = False,
        converter=None,
    ):
        inner = [
            binder_type(expected_type, name, implicit, required)
            for binder_type in self.binder_types
        ]
        super().__init__(inner, expected_type, name, implicit, required)


class BytesBinder(Binder):
    handle = FromBytes

    async def get_value(self, request: Request) -> bytes | None:
        return await request.read()


class SyncBinder(Binder):
    """
    Base binder class for values that can be read synchronously from requests
    with complete headers. Like route, query string and header parameters.
    """

    def __init__(
        self,
        expected_type: Any = list[str],
        name: str = "",
        implicit: bool = False,
        required: bool = False,
        converter: Callable[[Sequence[str]], Any] | None = None,
    ):
        super().__init__(
            expected_type,
            name=name,
            implicit=implicit,
            required=required,
            converter=converter or self._get_converter(expected_type),
        )

    def _get_converter(self, expected_type) -> Callable[[Sequence[str]], Any]:
        if self.is_generic_iterable_annotation(expected_type) or expected_type in {
            list,
            set,
            tuple,
        }:
            return self._get_converter_for_iterable(expected_type)

        for converter in converters:
            if converter.can_convert(expected_type):
                return lambda values: converter.convert(
                    values[0] if values else None, expected_type
                )

        raise MissingConverterError(expected_type, self.__class__)

    def _get_converter_single(self, expected_type):
        for converter in converters:
            if converter.can_convert(expected_type):
                return partial(converter.convert, expected_type=expected_type)
        raise MissingConverterError(expected_type, self.__class__)

    def _get_converter_for_iterable(
        self, expected_type
    ) -> Callable[[Sequence[str]], Any]:
        generic_type = self.get_type_for_generic_iterable(expected_type)
        item_type = self.generic_iterable_annotation_item_type(expected_type)
        item_converter = self._get_converter_single(item_type)
        return lambda values: generic_type(item_converter(value) for value in values)

    @abstractmethod
    def get_raw_value(self, request: Request) -> Sequence[str]:
        """Reads a set of values from request information as strings."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Gets a name that describe the source of values for this SyncBinder."""

    _empty_iterables = [list(), set(), tuple()]

    def _empty_iterable(self, value):
        return value in self._empty_iterables

    def get_value_sync(self, request: Request) -> Any | None:
        raw_value = self.get_raw_value(request)
        try:
            value = self.converter(raw_value)
        except ValueError as converter_error:
            raise BadRequest(
                f"Invalid value {raw_value} for parameter `{self.parameter_name}`; "
                f"expected a valid {self.expected_type.__name__}."
            ) from converter_error

        if self.default is not empty and (value is None or self._empty_iterable(value)):
            return None

        if value is None and self.required and self.root_required:
            raise MissingParameterError(self.parameter_name, self.source_name)

        if not self.required and self._empty_iterable(value):
            return None

        return value

    async def get_value(self, request: Request) -> Any | None:
        return self.get_value_sync(request)


class HeaderBinder(SyncBinder):
    handle = FromHeader

    @property
    def source_name(self) -> str:
        return "header"

    def get_raw_value(self, request: Request) -> Sequence[str]:
        headers = request.get_headers(self.parameter_name.encode())
        if not headers:
            headers = request.get_headers(self.parameter_name)
        return [
            h.decode("utf8") if isinstance(h, (bytes, bytearray)) else str(h)
            for h in headers
        ]


class QueryBinder(SyncBinder):
    handle = FromQuery

    def __init__(
        self,
        expected_type: T = str,
        name: str | None = None,
        implicit: bool = False,
        required: bool = True,
        converter: Callable | None = None,
    ):
        super().__init__(expected_type, name, implicit, required, converter)
        self._is_iterable = self.is_generic_iterable_annotation(
            expected_type
        ) or expected_type in {list, set, tuple}
        self._scalar_type = expected_type if not self._is_iterable else None
        if self._scalar_type is int:
            self._fast_convert = self._convert_int
        elif self._scalar_type is float:
            self._fast_convert = self._convert_float
        elif self._scalar_type is bool:
            self._fast_convert = self._convert_bool
        elif self._scalar_type is str or str(self._scalar_type) == "~T":
            self._fast_convert = self._convert_str
        else:
            self._fast_convert = None

    @staticmethod
    def _convert_str(val: str) -> str:
        if "%" in val:
            return unquote(val)
        return val

    @staticmethod
    def _convert_int(val: str) -> int:
        return int(val)

    @staticmethod
    def _convert_float(val: str) -> float:
        return float(val)

    @staticmethod
    def _convert_bool(val: str) -> bool:
        low = val.lower()
        if low in ("true", "1", "yes", "on"):
            return True
        if low in ("false", "0", "no", "off"):
            return False
        raise ValueError(f"Cannot convert {val!r} to bool")

    @property
    def source_name(self) -> str:
        return "query"

    def get_raw_value(self, request: Request) -> Sequence[str]:
        if self._is_iterable:
            return request.get_query_params(self.parameter_name)
        val = request.get_query_param(self.parameter_name)
        if val is not None:
            return [val]
        return []

    def get_value_sync(self, request: Request) -> Any | None:
        if self._is_iterable:
            raw_values = request.get_query_params(self.parameter_name)
            try:
                value = self.converter(raw_values)
            except ValueError as converter_error:
                raise BadRequest(
                    f"Invalid value {raw_values} for parameter `{self.parameter_name}`; "
                    f"expected a valid {self.expected_type}."
                ) from converter_error

            if self.default is not empty and (
                value is None or self._empty_iterable(value)
            ):
                return None
            if value is None and self.required and self.root_required:
                raise MissingParameterError(self.parameter_name, self.source_name)
            if not self.required and self._empty_iterable(value):
                return None
            return value

        # Fast scalar path
        raw_val = request.get_query_param(self.parameter_name)
        if raw_val is None or (
            raw_val == ""
            and (not self.required or not self.root_required)
            and self.expected_type is not str
        ):
            if self.default is not empty:
                return None
            if raw_val is None and self.required and self.root_required:
                raise MissingParameterError(self.parameter_name, self.source_name)
            return None

        if self._fast_convert is not None:
            try:
                return self._fast_convert(raw_val)
            except (ValueError, TypeError) as err:
                type_name = (
                    self.expected_type.__name__
                    if hasattr(self.expected_type, "__name__")
                    else str(self.expected_type)
                )
                raw_values = request.get_query_params(self.parameter_name)
                raise BadRequest(
                    f"Invalid value {raw_values} for parameter `{self.parameter_name}`; "
                    f"expected a valid {type_name}."
                ) from err

        try:
            return self.converter([raw_val])
        except ValueError as converter_error:
            type_name = (
                self.expected_type.__name__
                if hasattr(self.expected_type, "__name__")
                else str(self.expected_type)
            )
            raise BadRequest(
                f"Invalid value {[raw_val]} for parameter `{self.parameter_name}`; "
                f"expected a valid {type_name}."
            ) from converter_error


class CookieBinder(SyncBinder):
    handle = FromCookie

    @property
    def source_name(self) -> str:
        return "cookie"

    def get_raw_value(self, request: Request) -> Sequence[str]:
        cookie = request.cookies.get(self.parameter_name)
        if cookie:
            return [cookie]
        return []


class RouteBinder(SyncBinder):
    handle = FromRoute

    def __init__(
        self,
        expected_type: T = str,
        name: str | None = None,
        implicit: bool = False,
        required: bool = True,
        converter: Callable | None = None,
    ):
        super().__init__(expected_type, name or "route", implicit, required, converter)
        if expected_type is int:
            self._fast_convert = int
        elif expected_type is float:
            self._fast_convert = float
        elif expected_type is str or str(expected_type) == "~T":
            self._fast_convert = QueryBinder._convert_str
        else:
            self._fast_convert = None

    def get_raw_value(self, request: Request) -> Sequence[str]:
        val = request.route_values.get(self.parameter_name, "")
        return [val] if val is not None else []

    def get_value_sync(self, request: Request) -> Any | None:
        raw_val = request.route_values.get(self.parameter_name)
        if raw_val is None or raw_val == "":
            if self.default is not empty:
                return None
            if self.required and self.root_required:
                raise MissingParameterError(self.parameter_name, self.source_name)
            return None
        if self._fast_convert is not None:
            try:
                return self._fast_convert(raw_val)
            except (ValueError, TypeError) as err:
                type_name = (
                    self.expected_type.__name__
                    if hasattr(self.expected_type, "__name__")
                    else str(self.expected_type)
                )
                raise BadRequest(
                    f"Invalid value {raw_val!r} for parameter `{self.parameter_name}`; "
                    f"expected a valid {type_name}."
                ) from err
        return super().get_value_sync(request)

    @property
    def source_name(self) -> str:
        return "route"


class ServiceBinder(Binder):
    handle = FromServices

    def __init__(
        self,
        service,
        name: str = "",
        implicit: bool = False,
        services: ContainerProtocol | None = None,
    ):
        super().__init__(service, name, implicit, False, None)
        self.services = services
        self._prebound_factory = None
        self._init_prebinding()

    def _init_prebinding(self):
        tp = self.expected_type
        if isinstance(tp, type):
            init = getattr(tp, "__init__", None)
            if init is object.__init__ or (
                callable(init)
                and hasattr(init, "__code__")
                and getattr(init.__code__, "co_argcount", 0) == 1
            ):
                self._prebound_factory = tp

    def get_value_sync(self, request: Request) -> Any:
        try:
            scope = request._di_scope  # type: ignore
        except AttributeError:
            scope = None

        if self.services is not None:
            try:
                return self.services.resolve(self.expected_type, scope)
            except CannotResolveTypeException:
                pass

        if self._prebound_factory is not None:
            return self._prebound_factory()

        return None

    async def get_value(self, request: Request) -> Any:
        return self.get_value_sync(request)


class ControllerParameter(BoundValue[T]):
    pass


class ControllerBinder(ServiceBinder):
    """
    Binder used to activate an instance of Controller. This binder is applied
    automatically by the application
    object at startup, as type annotation, for handlers configured on classes
    inheriting `dreaming_electric_sheep.server.Controller`.

    If used manually, it causes several controllers to be instantiated and
    injected into request handlers.
    However, only the controller configured as `self` is taken into
    consideration for base route and callbacks.
    """

    handle = ControllerParameter

    def __init__(
        self,
        service,
        name: str = "",
        implicit: bool = False,
        services: ContainerProtocol | None = None,
    ):
        super().__init__(service, name, implicit, services)
        self._init_controller_prebinding()

    def _init_controller_prebinding(self):
        tp = self.expected_type
        if isinstance(tp, type):
            init = getattr(tp, "__init__", None)
            if init is object.__init__ or (
                callable(init)
                and hasattr(init, "__code__")
                and getattr(init.__code__, "co_argcount", 0) == 1
            ):
                self._prebound_factory = tp

    async def get_value(self, request: Request) -> T | None:
        return await super().get_value(request)


class RequestBinder(Binder):
    name_alias = "request"
    type_alias = Request

    def __init__(self, implicit: bool = True):
        super().__init__(Request, implicit=implicit)

    def get_value_sync(self, request: Request) -> Any:
        return request

    async def get_value(self, request: Request) -> Any:
        return request


class WebSocketBinder(Binder):
    name_alias = "websocket"
    type_alias = WebSocket

    def __init__(self, implicit: bool = True):
        super().__init__(WebSocket, implicit=implicit)

    async def get_value(self, websocket: WebSocket) -> WebSocket | None:
        return websocket


class IdentityBinder(Binder):
    handle = RequestUser

    async def get_value(self, request: Request) -> Identity | None:
        return getattr(request, "identity", None)


class ExactBinder(Binder):
    def __init__(self, exact_object):
        super().__init__(object, implicit=True)
        self.exact_object = exact_object

    async def get_value(self, request: Request) -> Any:
        return self.exact_object


class ServicesBinder(ExactBinder):
    name_alias = "services"

    @classmethod
    def from_alias(cls, services: ContainerProtocol) -> "ServicesBinder":
        return cls(services)


class ClientInfoBinder(Binder):
    handle = ClientInfo

    async def get_value(self, request: Request) -> tuple[str, int]:
        return tuple(request.scope["client"])


class ServerInfoBinder(Binder):
    handle = ServerInfo

    async def get_value(self, request: Request) -> tuple[str, int]:
        return tuple(request.scope["server"])


class RequestURLBinder(Binder):
    handle = RequestURL

    def __init__(self):
        super().__init__(URL, name="request url", implicit=False)

    async def get_value(self, request: Request) -> URL:
        return request.url


class RequestMethodBinder(Binder):
    handle = RequestMethod

    def __init__(self):
        super().__init__(str, name="request method", implicit=False)

    async def get_value(self, request: Request) -> str:
        return request.method


class FilesBinder(Binder):
    handle = FromFiles

    async def get_value(self, request: Request) -> list[FormPart]:
        return await request.files()


class URLResolverBinder(Binder):
    """
    Binder that injects a URLResolver into request handlers.
    The URLResolver is constructed per-request from the singleton Router and the
    current Request, so it correctly reflects the request's base_path for
    generating URLs relative to the mount root.
    """

    type_alias = URLResolver

    def __init__(self, router: Router, implicit: bool = True):
        super().__init__(URLResolver, implicit=implicit)
        self._router = router

    @classmethod
    def from_alias(cls, services: ContainerProtocol) -> "URLResolverBinder":
        from dreaming_electric_sheep.server import Application

        app: Application = services.resolve(Application)
        return cls(app.router)

    async def get_value(self, request: Request) -> URLResolver:
        return URLResolver(self._router, request)
