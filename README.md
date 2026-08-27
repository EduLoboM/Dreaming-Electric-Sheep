[![Build](https://github.com/EduLoboM/Dreaming-Electric-Sheep/workflows/Main/badge.svg)](https://github.com/EduLoboM/Dreaming-Electric-Sheep/actions)
[![pypi](https://img.shields.io/pypi/v/dreaming-electric-sheep.svg?color=blue)](https://pypi.org/project/dreaming-electric-sheep/)
[![versions](https://img.shields.io/pypi/pyversions/dreaming-electric-sheep.svg)](https://github.com/EduLoboM/Dreaming-Electric-Sheep)
[![license](https://img.shields.io/github/license/EduLoboM/Dreaming-Electric-Sheep.svg)](https://github.com/EduLoboM/Dreaming-Electric-Sheep/blob/main/LICENSE)

# Dreaming Electric Sheep

**Dreaming Electric Sheep** is an ultra high-performance asynchronous web framework to build event-based web
applications with Python, developed as an optimized fork of [BlackSheep](https://github.com/Neoteroi/BlackSheep). It is inspired by
[Flask](https://palletsprojects.com/p/flask/), [ASP.NET
Core](https://docs.microsoft.com/en-us/aspnet/core/), and the work by [Yury
Selivanov](https://magic.io/blog/uvloop-blazing-fast-python-networking/).

<p align="center">
  <a href="#dreaming-electric-sheep"><img width="180" src="https://limbuscompany.wiki.gg/images/thumb/Dreaming_Electric_Sheep_Gift.png/100px-Dreaming_Electric_Sheep_Gift.png?128db1" alt="Dreaming Electric Sheep"></a>
</p>

```bash
pip install dreaming-electric-sheep
```

---

```python
from datetime import datetime, timezone

from dreaming_electric_sheep import Application, get


app = Application()

@get("/")
async def home():
    return f"Hello, World! {datetime.now(timezone.utc).isoformat()}"

```

## Dependencies

Dreaming Electric Sheep supports running with `CPython` and [`PyPy`](https://pypy.org/), and makes `httptools` an optional dependency.

The Dreaming Electric Sheep HTTP Client includes HTTP/2 support and requires `h11` and `h2` libraries.

For slightly better performance in `URL` parsing when running on `CPython`,
it is recommended to install `httptools` (optional).

## Requirements

[Python](https://www.python.org): any version listed in the project's
classifiers.

Dreaming Electric Sheep belongs to the category of
[ASGI](https://asgi.readthedocs.io/en/latest/) web frameworks, so it requires
an ASGI HTTP server to run, such as [uvicorn](https://www.uvicorn.org/),
[hypercorn](https://pgjones.gitlab.io/hypercorn/) or
[granian](https://github.com/emmett-framework/granian).
For example, to use it with uvicorn:

```bash
pip install uvicorn
```

To run an application like in the example above, use the methods provided by
the ASGI HTTP Server:

```bash
# if the Dreaming Electric Sheep app is defined in a file `server.py`

$ uvicorn server:app
```

To run for production, refer to the documentation of the chosen ASGI server
(i.e. for [uvicorn](https://www.uvicorn.org/#running-with-gunicorn)).

## Automatic bindings and dependency injection

Dreaming Electric Sheep supports automatic binding of values for request handlers, by type
annotation or by conventions.

```python
from dataclasses import dataclass

from dreaming_electric_sheep import Application, FromJSON, FromQuery, get, post


app = Application()


@dataclass
class CreateCatInput:
    name: str


@post("/api/cats")
async def example(data: FromJSON[CreateCatInput]):
    # in this example, data is bound automatically reading the JSON
    # payload and creating an instance of `CreateCatInput`
    ...


@get("/:culture_code/:area")
async def home(culture_code, area):
    # in this example, both parameters are obtained from routes with
    # matching names
    return f"Request for: {culture_code} {area}"


@get("/api/products")
def get_products(
    page: int = 1,
    size: int = 30,
    search: str = "",
):
    # this example illustrates support for implicit query parameters with
    # default values
    # since the source of page, size, and search is not specified and no
    # route parameter matches their name, they are obtained from query string
    ...


@get("/api/products2")
def get_products2(
    page: FromQuery[int] = FromQuery(1),
    size: FromQuery[int] = FromQuery(30),
    search: FromQuery[str] = FromQuery(""),
):
    # this example illustrates support for explicit query parameters with
    # default values
    # in this case, parameters are explicitly read from query string
    ...

```

It also supports dependency injection, a feature that provides a consistent and clean way to use dependencies in request handlers.

## Strategies to handle authentication and authorization

Dreaming Electric Sheep implements strategies to handle authentication and authorization:

```python
app.use_authentication()\
    .add(ExampleAuthenticationHandler())


app.use_authorization()\
    .add(AdminsPolicy())


@auth("admin")
@get("/")
async def only_for_admins():
    ...


@auth()
@get("/")
async def only_for_authenticated_users():
    ...
```

Dreaming Electric Sheep provides:

* Built-in support for **OpenID Connect** authentication
* Built-in support for **JWT Bearer** authentication

Meaning that it is easy to integrate with services such as:

* [Auth0](https://auth0.com)
* [Microsoft Entra ID](https://www.microsoft.com/en-us/security/business/identity-access/microsoft-entra-id)
* [Azure Active Directory B2C](https://docs.microsoft.com/en-us/azure/active-directory-b2c/overview)
* [Okta](https://www.okta.com)

It also offers built-in support for **Basic authentication**,
**API Key authentication**, **JWT Bearer authentication using symmetric encryption**,
and automatic generation of OpenAPI Documentation for security schemes when using
built-in classes for authentication. It supports defining custom authentication handlers
and custom mappers for OpenAPI Documentation.

## Web framework features

* ASGI compatibility
* Routing
* Request handlers can be defined as functions or class methods
* Middlewares
* WebSocket
* Server-Sent Events (SSE)
* Built-in support for dependency injection
* Support for automatic binding of route and query parameters to request handler method calls
* Strategy to handle exceptions
* Strategy to handle authentication and authorization
* Built-in support for OpenID Connect authentication using OIDC discovery
* Built-in support for JWT Bearer authentication using OIDC discovery and other sources of JWKS
* Handlers normalization
* Serving static files
* Integration with Jinja2
* Support for serving SPAs that use HTML5 History API for client side routing
* Support for automatic generation of OpenAPI Documentation
* Strategy to handle CORS settings
* Sessions
* Support for automatic binding of `dataclasses` and [`Pydantic`](https://pydantic-docs.helpmanual.io) models to handle the request body payload expected by request handlers
* `TestClient` class to simplify testing of applications
* Anti Forgery validation to protect against Cross-Site Request Forgery (XSRF/CSRF) attacks

## Client features

Dreaming Electric Sheep includes an HTTP Client with native HTTP/2 support.
The client automatically detects and uses HTTP/2 when the server supports it, with
seamless fallback to HTTP/1.1.

**Example:**

```python
import asyncio

from dreaming_electric_sheep.client import ClientSession


async def client_example():
    async with ClientSession() as client:
        response = await client.get("https://docs.python.org/3/")
        text = await response.text()
        print(text)


asyncio.run(client_example())
```

> [!IMPORTANT]
>
> Dreaming Electric Sheep supports [PyPy](https://pypy.org/) (`PyPy 3.11`). The HTTP client requires `h11` and `h2` libraries. The `httptools` library is
> optional and only provides better URL parsing performance on CPython. These
> dependencies affect only the `dreaming_electric_sheep.client` namespace.

## Supported platforms and runtimes

* Python: all versions included in the [build matrix](.github/workflows/main.yml).
* CPython and PyPy.
* Ubuntu.
* Windows.
* macOS.

## Branches

The _main_ branch contains the currently developed version.
