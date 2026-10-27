import reflex as rx

config = rx.Config(
    app_name="helios",
    app_module_import="helios.helios",
    frontend_port=3000,
    backend_port=8000,
)
